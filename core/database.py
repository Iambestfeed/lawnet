import sys
import os
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models.legal_document import LegalDocument
from core.models.legal_qa import LegalQA
from core.models.judgment import Judgment
from core.models.judgment_document_relation import JudgmentDocumentRelation
from core.models.crawl_tracker import CrawlTracker
from core.models.process_tracker import ProcessTracker

import os
import csv
import json
import logging
from datetime import datetime
from typing import Generator, Any
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from dateutil.parser import parse
import random
from sqlalchemy.orm import declarative_base
from core.models.base import Base 

load_dotenv()

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

class DatabaseManager:
    def __init__(self):
        self.session = SessionLocal()
    
    def __enter__(self):
        return self 
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        if exc_type is not None:
            logger.error(f"Session error: {exc_val}")
            
    def close(self):
        """Đóng session"""
        self.session.close()
            
    def commit(self):
        """Commit transaction thủ công"""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.rollback()
            raise
    
    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()
        logger.info("Transaction rolled back")
            
    def insert_data(self, data_object):
        """Thêm dữ liệu sử dụng ORM"""
        try:
            self.session.add(data_object)
            self.session.commit()
            self.session.refresh(data_object)
            logger.info(f"Inserted into {data_object.__tablename__} successfully")
            return data_object
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        

    def export_data(self, table_name: str, file_path: str):
        """Xuất dữ liệu ra CSV sử dụng raw SQL"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                with engine.connect() as connection:
                    result = connection.execute(text(f"SELECT * FROM {table_name}"))
                    writer.writerow(result.keys())
                    writer.writerows(result.fetchall())
            logger.info(f"Exported {table_name} to {file_path}")
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise

    def import_data(self, table_name: str, file_path: str):
        """Nhập dữ liệu từ CSV sử dụng bulk insert"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                with engine.connect() as connection:
                    with connection.begin():
                        for row in reader:
                            cleaned_row = {
                                k: parse(v).date() if 'date' in k.lower() and v else v 
                                for k, v in row.items()
                            }
                            connection.execute(
                                text(f"INSERT INTO {table_name} ({','.join(row.keys())}) VALUES ({','.join([':'+k for k in row.keys()])})"),
                                cleaned_row
                            )
            logger.info(f"Imported {file_path} to {table_name}")
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            raise
    def get_random_samples(self):
        """Lấy 3 mẫu ngẫu nhiên từ tất cả các bảng liên quan"""
        results = {}
        try:
            # Lấy mẫu từ legal_documents
            legal_docs = self.session.query(LegalDocument).order_by(func.random()).limit(3).all()
            results['legal_documents'] = legal_docs if legal_docs else "Bảng legal_documents trống"

            # Lấy mẫu từ legal_qa
            legal_qa = self.session.query(LegalQA).order_by(func.random()).limit(3).all()
            results['legal_qa'] = legal_qa if legal_qa else "Bảng legal_qa trống"

            # Lấy mẫu từ judgments
            judgments = self.session.query(Judgment).order_by(func.random()).limit(3).all()
            results['judgments'] = judgments if judgments else "Bảng judgments trống"

            # Lấy mẫu từ judgment_document_relations
            relations = self.session.query(JudgmentDocumentRelation).order_by(func.random()).limit(3).all()
            if relations:
                results['relations'] = [{
                    'relation': rel,
                    'judgment': self.session.get(Judgment, rel.judgment_id),
                    'document': self.session.get(LegalDocument, rel.document_id)
                } for rel in relations]
            else:
                results['relations'] = "Bảng relations trống"

            return results

        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Lỗi khi lấy mẫu dữ liệu: {str(e)}")
            raise
        finally:
            self.session.close()

    def check_tables_data(self):
        """Kiểm tra dữ liệu trong các bảng và trả về số lượng bản ghi"""
        table_status = {}
        try:
            tables = [LegalDocument, LegalQA, Judgment, JudgmentDocumentRelation]
            for table in tables:
                count = self.session.query(table).count()
                table_status[table.__tablename__] = {
                    'count': count,
                    'status': 'Có dữ liệu' if count > 0 else 'Trống'
                }
            return table_status
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Lỗi kiểm tra bảng: {str(e)}")
            raise

    @staticmethod
    def validate_document(data: dict):
        """Validate dữ liệu trước khi insert"""
        required_fields = [
            'document_number', 
            'document_type', 
            'issuing_authority',
            'issue_date'
        ]
        
        for field in required_fields:
            if not data.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        if len(data['document_number']) > 255:
            raise ValueError("Document number exceeds maximum length")
        
        try:
            if data.get('issue_date'):
                parse(data['issue_date'])
        except ValueError:
            raise ValueError("Invalid date format for issue_date")
        
        return True
    def _save_to_db(self, data: dict):
        """Lưu dữ liệu vào database sử dụng context manager"""
        with DatabaseManager() as db:
            try:
                judgment = Judgment(**data)
                db.session.add(judgment)
                db.commit()  # Sử dụng commit từ DatabaseManager
                logger.info("Data saved to database successfully")
            except Exception as e:
                logger.error(f"Failed to save data: {str(e)}")
                # Không cần gọi rollback() ở đây vì đã xử lý trong __exit__
                raise
            
    def bulk_insert(self, objects: list):
        """Thêm bulk data cho hiệu suất cao"""
        try:
            self.session.bulk_save_objects(objects)
            self.session.commit()
            logger.info(f"Inserted {len(objects)} records successfully")
        except SQLAlchemyError as e:
            self.rollback()
            logger.error(f"Bulk insert error: {str(e)}")
            raise
    def get_pending_documents(self, max_retries: int = 3):
        """Lấy các documents cần xử lý"""
        return self.session.query(CrawlTracker).filter(
            (CrawlTracker.status.in_(['pending', 'failed'])) &
            (CrawlTracker.retry_count < max_retries)
        ).all()
    
    def get_existing_ids(self, ids: list, doc_type: str):
        """Kiểm tra ID đã tồn tại"""
        return set(
            self.session.query(CrawlTracker.document_id)
            .filter(
                CrawlTracker.document_id.in_(ids),
                CrawlTracker.document_type == doc_type
            )
            .scalars()
        )

def get_db() -> Generator:
    """Dependency cho FastAPI"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
        
def print_samples(samples):
    """Hàm phụ trợ in kết quả mẫu"""
    for table, data in samples.items():
        print(f"\n=== {table.upper().replace('_', ' ')} ===")
        if isinstance(data, str):
            print(data)
        else:
            for item in data:
                print("-" * 50)
                if table == 'relations':
                    print(f"Relation ID: {item['relation'].id}")
                    print(f"Judgment: {item['judgment'].case_number if item['judgment'] else 'Không tồn tại'}")
                    print(f"Document: {item['document'].document_number if item['document'] else 'Không tồn tại'}")
                else:
                    print(json.dumps(item.to_dict(), indent=2, ensure_ascii=False))