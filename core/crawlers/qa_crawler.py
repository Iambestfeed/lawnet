import requests
from bs4 import BeautifulSoup
from core.database import DatabaseManager
from core.models import LegalQA
import logging

logger = logging.getLogger(__name__)

class QACrawler:
    def __init__(self):
        self.base_url = "https://thuvienphapluat.vn/hoidap"
        self.db = DatabaseManager()

    def crawl(self, question_id: str):
        try:
            url = f"{self.base_url}/{question_id}"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {
                'question_html': self._extract_question(soup),
                'answer_html': self._extract_answer(soup),
                'category': self._extract_category(soup),
                # Thêm các trường khác
            }
            
            self._save_to_db(data)
            logger.info(f"Crawled QA {question_id} successfully")
            
        except Exception as e:
            logger.error(f"Failed to crawl QA {question_id}: {str(e)}")

    def _extract_question(self, soup) -> str:
        # PLACEHOLDER
        return ""

    def _extract_answer(self, soup) -> str:
        # PLACEHOLDER
        return ""

    def _extract_category(self, soup) -> str:
        # PLACEHOLDER
        return ""
        
    def _save_to_db(self, data: dict):
        self.db.insert_data(LegalQA, data)