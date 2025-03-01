import requests
from bs4 import BeautifulSoup
from core.database import DatabaseManager, SessionLocal
from core.models import ProcessTracker
import logging
from datetime import datetime
from typing import List
from multiprocessing import Pool, cpu_count
from functools import partial
import time

logger = logging.getLogger(__name__)

class SearchCrawler:
    def __init__(self, doc_type: str):
        self.doc_type = doc_type
        self.base_url = self._get_base_url()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _get_base_url(self) -> str:
        return {
            'law': "https://thuvienphapluat.vn/page/tim-van-ban.aspx?type=0&page={page}",
            'judgment': "https://thuvienphapluat.vn/banan/tim-ban-an?type_q=0&sortType=1&Category=0&page={page}"
        }[self.doc_type]

    def crawl_ids(self, start_page=1, end_page=None, max_empty_pages=3, delay=2, num_processes=None):
        num_processes = num_processes or cpu_count()
        page_ranges = self._split_page_range(start_page, end_page, num_processes)
        
        logger.info(f"Starting crawling with {num_processes} processes")
        
        with Pool(
            processes=num_processes,
            initializer=self._init_worker,
            initargs=(self.doc_type,)
        ) as pool:
            results = pool.map(
                partial(
                    self._process_page_range,
                    max_empty_pages=max_empty_pages,
                    delay=delay
                ),
                page_ranges
            )
        
        total_new = sum(results)
        logger.info(f"Crawling completed. Total new IDs added: {total_new}")
        return total_new

    def _split_page_range(self, start, end, num_chunks):
        if end is None:
            end = start + 100  # Default max pages to crawl
        
        pages = list(range(start, end + 1))
        chunk_size = max(1, (end - start + 1) // num_chunks)
        return [pages[i:i + chunk_size] for i in range(0, len(pages), chunk_size)]

    @staticmethod
    def _init_worker(doc_type):
        global worker_db, worker_headers, worker_doc_type
        worker_db = SessionLocal()
        worker_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        worker_doc_type = doc_type

    def _process_page_range(self, page_range, max_empty_pages, delay):
        local_db = worker_db
        total_new = 0
        empty_count = 0
        base_url = self._get_base_url()

        for page in page_range:
            try:
                time.sleep(delay)
                url = base_url.format(page=page)
                logger.debug(f"Processing page {page}")

                response = requests.get(url, headers=worker_headers, timeout=30)
                response.raise_for_status()
                
                ids = self._parse_ids(response.text)
                logger.debug(f"Found {len(ids)} IDs on page {page}")

                if not ids:
                    empty_count += 1
                    if empty_count >= max_empty_pages:
                        break
                    continue

                empty_count = 0
                new_ids = self._save_ids(local_db, ids)
                total_new += new_ids
                logger.debug(f"Added {new_ids} new IDs from page {page}")

            except Exception as e:
                logger.error(f"Error processing page {page}: {str(e)}")
                local_db.rollback()

        local_db.close()
        return total_new

    def _parse_ids(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        if worker_doc_type == 'law':
            return list(set([
                item['lawid'].strip() 
                for item in soup.select('p.nqTitle[lawid]') 
                if item['lawid'].strip()
            ]))
        elif worker_doc_type == 'judgment':
            return list(set([
                a['href'].split('-')[-1].split('/')[0]  # Lấy phần cuối cùng sau dấu - và trước dấu /
                for a in soup.select('a.h5.font-weight-bold[href*="/ban-an/"]')  # Cập nhật selector chính xác hơn
                if a['href']
            ]))
        return []

    def _save_ids(self, session, ids: List[str]) -> int:
        existing = session.query(ProcessTracker.document_id).filter(
            ProcessTracker.document_id.in_(ids),
            ProcessTracker.document_type == worker_doc_type
        ).all()
        
        existing_ids = {x[0] for x in existing}
        new_ids = [x for x in ids if x not in existing_ids]
        
        if new_ids:
            records = [
                ProcessTracker(
                    document_id=doc_id,
                    document_type=worker_doc_type,
                    status='pending',
                    created_at=datetime.now()
                ) for doc_id in new_ids
            ]
            session.bulk_save_objects(records)
            session.commit()
        
        return len(new_ids)