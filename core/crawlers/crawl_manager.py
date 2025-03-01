import logging
from datetime import datetime
from typing import List
from multiprocessing import Pool, cpu_count
from functools import partial
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import DATABASE_URL
from core.crawlers import JudgmentCrawler, LawCrawler
from core.models import CrawlTracker

logger = logging.getLogger(__name__)

class CrawlProcessingService:
    def __init__(self, doc_type: str, batch_size=100, max_retries=3, num_processes=None):
        self.doc_type = doc_type
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.num_processes = num_processes or cpu_count()
        
        # Tạo engine mới với SSL configuration
        self.engine = create_engine(
            DATABASE_URL,
            connect_args={
                'sslmode': 'require',
                'sslrootcert': '/path/to/ca-certificate.crt',  # Đường dẫn đến SSL certificate
            },
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.Session = sessionmaker(bind=self.engine)

    def process_pending(self):
        pending_ids = self._get_pending_ids()
        logger.info(f"Starting processing {len(pending_ids)} {self.doc_type} documents with {self.num_processes} processes")

        # Tạo worker function với các tham số cần thiết
        process_func = partial(
            self._process_single_worker,
            doc_type=self.doc_type,
            db_url=DATABASE_URL,
            max_retries=self.max_retries
        )

        with Pool(
            processes=self.num_processes,
            initializer=self._init_worker,
            initargs=(DATABASE_URL, self.doc_type)
        ) as pool:
            results = pool.map(process_func, pending_ids)

        success_count = sum(results)
        logger.info(f"Processing completed. Total success: {success_count}/{len(pending_ids)}")
        return success_count

    @staticmethod
    def _init_worker(db_url, doc_type):
        # Khởi tạo engine và session riêng cho mỗi worker
        global worker_engine, worker_session, worker_crawler
        worker_engine = create_engine(
            db_url,
            connect_args={
                'sslmode': 'require',
                'sslrootcert': '/path/to/ca-certificate.crt',
            },
            pool_pre_ping=True,
            pool_recycle=3600
        )
        worker_session = sessionmaker(bind=worker_engine)()
        worker_crawler = LawCrawler() if doc_type == 'law' else JudgmentCrawler()

    def _get_pending_ids(self) -> List[str]:
        """Lấy danh sách ID từ database sử dụng connection riêng"""
        session = self.Session()
        try:
            return [
                doc.document_id for doc in session.query(CrawlTracker).filter(
                    CrawlTracker.document_type == self.doc_type,
                    CrawlTracker.status.in_(['pending', 'failed']),
                    CrawlTracker.retry_count < self.max_retries
                ).order_by(CrawlTracker.created_at).limit(self.batch_size).all()
            ]
        finally:
            session.close()

    @staticmethod
    def _process_single_worker(doc_id: str, doc_type: str, db_url: str, max_retries: int) -> int:
        """Xử lý một document trong worker process"""
        try:
            session = worker_session
            crawler = worker_crawler

            doc = session.query(CrawlTracker).filter_by(
                document_id=doc_id,
                document_type=doc_type
            ).first()

            if not doc:
                return 0

            logger.info(f"Processing {doc_type} {doc_id} (attempt {doc.retry_count+1})")
            
            try:
                # Thực hiện crawl và lưu dữ liệu
                result = crawler.crawl(doc_id, saving=True)
                
                # Cập nhật trạng thái thành công
                doc.status = 'success'
                doc.last_attempt = datetime.now()
                doc.retry_count = 0
                doc.error_log = None
                session.commit()
                return 1
                
            except Exception as e:
                # Xử lý lỗi và rollback transaction
                session.rollback()
                doc.retry_count += 1
                doc.last_attempt = datetime.now()
                doc.error_log = str(e)[:500]
                doc.status = 'failed' if doc.retry_count >= max_retries else 'pending'
                session.commit()
                logger.error(f"Failed processing {doc_id}: {str(e)}")
                return 0

        except Exception as e:
            logger.error(f"Critical error in worker: {str(e)}")
            session.rollback()
            return 0
        finally:
            # Đóng session và reset connection
            session.close()
            worker_engine.dispose()