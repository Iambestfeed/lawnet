import requests
from bs4 import BeautifulSoup
from core.database import DatabaseManager
from core.models import Judgment
import logging
from datetime import datetime
from typing import Optional
import re

logger = logging.getLogger(__name__)

class JudgmentCrawler:
    def __init__(self):
        self.base_url = "https://thuvienphapluat.vn/banan/ban-an/x"
        self.db = DatabaseManager()

    def crawl(self, judgment_id: str, saving = False):
        try:
            url = f"{self.base_url}-{judgment_id}"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lấy metadata từ ul.list-group.detail-item
            metadata_section = soup.find("ul", class_="list-group detail-item")
            
            # Lấy nội dung chính từ div#vanban_content
            content_div = soup.find("div", id="vanban_content")
            
            data = {
                'case_name': self._extract_metadata(metadata_section, 'Tên bản án:'),
                'case_number': self._extract_metadata(metadata_section, 'Số hiệu:'),
                'issuing_authority': self._extract_authority(metadata_section),
                'trial_level': self._extract_metadata(metadata_section, 'Cấp xét xử:'),
                'field': self._extract_metadata(metadata_section, 'Lĩnh vực:'),
                'judgment_date': self._extract_date(metadata_section),
                'keywords': self._extract_keywords(metadata_section),
                'metadata_html': str(metadata_section) if metadata_section else None,  # Lưu metadata raw
                'content_html': str(content_div) if content_div else None,  # Lưu content raw
                'content_text': self._clean_content(content_div),
                'related_parties': self._extract_parties(soup)
            }
            
            if saving:
                self._save_to_db(data)
            logger.info(f"Crawled judgment {judgment_id} successfully")
            return data  # Thêm dòng này để trả về dữ liệu
            
        except Exception as e:
            logger.error(f"Failed to crawl judgment {judgment_id}: {str(e)}")
            raise

    def _extract_metadata(self, metadata_section, label: str) -> str:
        """Trích xuất metadata với cơ chế tìm kiếm chính xác"""
        if not metadata_section:
            return ""
        
        # Tìm thẻ b chứa label chính xác
        label_tag = metadata_section.find('b', string=label)
        
        if label_tag:
            # Đi đến div chứa giá trị tương ứng
            row = label_tag.find_parent('li').find('div', class_='row')
            if row:
                value_div = row.find('div', class_='col-xl-9')
                if value_div:
                    # Xử lý các trường hợp có thẻ con
                    return value_div.get_text(" ", strip=True).replace('\n', ' ')
        
        return ""

    def _extract_keywords(self, metadata_section) -> list:
        """Trích xuất từ khóa từ HTML"""
        if not metadata_section:
            return []
        
        # Tìm thẻ div chứa từ khóa
        kw_div = metadata_section.find('b', string='Từ khóa:').find_parent('li').find('div', class_='col-xl-9')
        
        if kw_div:
            # Trích xuất tất cả thẻ a
            return [a.get_text(strip=True) for a in kw_div.find_all('a')]
        
        return []

    def _extract_date(self, metadata_section) -> Optional[datetime]:
        """Trích xuất ngày ban hành chính xác"""
        date_str = self._extract_metadata(metadata_section, 'Ngày ban hành:')
        try:
            return datetime.strptime(date_str.strip(), "%d/%m/%Y")
        except (ValueError, TypeError, AttributeError):
            return None

    def _extract_authority(self, metadata_section) -> str:
        """Trích xuất cơ quan ban hành từ thẻ a"""
        if not metadata_section:
            return ""
        
        # Tìm trực tiếp thẻ a trong phần cơ quan ban hành
        a_tag = metadata_section.find('b', string='Cơ quan ban hành:').find_parent('li').find('a')
        return a_tag.get_text(strip=True) if a_tag else ""

    def _clean_content(self, content_div) -> str:
        """Làm sạch nội dung chính nâng cao"""
        if not content_div:
            return ""
        
        # Loại bỏ các thành phần không cần thiết
        unwanted = ['script', 'style', 'nav', 'footer', 'aside', 'header', 'form']
        for tag in content_div.find_all(unwanted):
            tag.decompose()
        
        # Chuẩn hóa khoảng trắng và xuống dòng
        text = content_div.get_text(" ", strip=True)
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())

    def _extract_parties(self, soup) -> dict:
        """Trích xuất các bên liên quan với cấu trúc mặc định"""
        parties = {"nguyen_don": [], "bi_don": [], "ben_lien_quan": []}
        
        # Tìm tất cả các phần có chứa thông tin các bên
        for section in soup.select('div.party-info-section'):
            header = section.find('h4').get_text(strip=True).lower()
            if 'nguyên đơn' in header:
                parties["nguyen_don"] = [li.get_text(strip=True) for li in section.select('ul > li')]
            elif 'bị đơn' in header:
                parties["bi_don"] = [li.get_text(strip=True) for li in section.select('ul > li')]
        
        return parties
        
    def _save_to_db(self, data: dict):
        """Lưu dữ liệu vào database"""
        with DatabaseManager() as db:
            try:
                judgment = Judgment(**data)
                db.insert_data(judgment)
                db.commit()
                logger.info("Data saved to database successfully")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to save data: {str(e)}")
                raise