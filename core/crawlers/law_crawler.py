# core/crawlers/law_crawler.py
import requests
from bs4 import BeautifulSoup
from core.database import DatabaseManager
from core.models import LegalDocument
import logging
from datetime import datetime
from typing import Optional
import re

logger = logging.getLogger(__name__)

class LawCrawler:
    def __init__(self):
        self.base_url = "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/x"  # URL gốc cho văn bản pháp luật
        self.db = DatabaseManager()

    def crawl(self, document_id: str, saving=False):
        try:
            url = f"{self.base_url}-{document_id}.aspx"
            response = requests.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Lấy các phần chính
            metadata_section = soup.find("div", {"id" : "divThuocTinh"})
            content_div = soup.find("div", class_ = "content1")

            data = {
                'document_number': self._extract_metadata(metadata_section, 'Số hiệu:'),
                'document_type': self._extract_metadata(metadata_section, 'Loại văn bản:'),
                'issuing_authority': self._extract_metadata(metadata_section, 'Nơi ban hành:'),
                'signer': self._extract_metadata(metadata_section, 'Người ký:'),
                'issue_date': self._extract_date(metadata_section, 'Ngày ban hành:'),
                'effective_date': self._extract_effective_date(metadata_section),
                'gazette_date': self._extract_gazette_info(metadata_section, 'date'),
                'gazette_number': self._extract_gazette_info(metadata_section, 'number'),
                'status': self._extract_status(metadata_section),
                'content_html': str(content_div) if content_div else None,
                'content_text': self._clean_content(content_div),
                'metadata_html': str(metadata_section) if metadata_section else None,
            }

            if saving:
                self._save_to_db(data)
            
            logger.info(f"Crawled document {document_id} successfully")
            return data

        except Exception as e:
            logger.error(f"Failed to crawl document {document_id}: {str(e)}")
            raise

    def _extract_metadata(self, metadata_section, label: str) -> str:
        """Trích xuất metadata từ bảng thuộc tính - Phiên bản đã sửa"""
        if not metadata_section:
            return ""
        
        try:
            # Tìm thẻ <b> chứa label chính xác
            label_b = metadata_section.find('b', string=lambda t: t and t.strip() == label)
            
            if label_b:
                # Đi đến thẻ <td> cha chứa label
                label_td = label_b.find_parent('td')
                
                if label_td:
                    # Di chuyển đến ô giá trị liền kề (td kế tiếp)
                    value_td = label_td.find_next_sibling('td')
                    
                    if value_td:
                        # Lọc các element con không cần thiết
                        for element in value_td.find_all(['span', 'a', 'div']):
                            element.decompose()
                        
                        # Lấy text và làm sạch
                        text = value_td.get_text(" ", strip=True)
                        
                        # Xử lý các trường hợp đặc biệt
                        if any(x in text for x in ["Đang cập nhật", "Chưa xác định"]):
                            return ""
                        
                        return re.sub(r'\s+', ' ', text).strip()
            
            return ""
        
        except Exception as e:
            logger.error(f"Lỗi trích xuất metadata '{label}': {str(e)}", exc_info=True)
            return ""

    def _extract_date(self, metadata_section, label: str) -> Optional[datetime]:
        """Trích xuất ngày tháng từ định dạng dd/mm/yyyy"""
        date_str = self._extract_metadata(metadata_section, label)
        
        # Xử lý các trường hợp đặc biệt
        if not date_str or date_str.lower() in ["đang cập nhật", "không xác định"]:
            return None
        
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except (ValueError, TypeError):
            logger.warning(f"Định dạng ngày không hợp lệ: {date_str}")
            return None

    def _extract_effective_date(self, metadata_section) -> Optional[datetime]:
        """Trích xuất ngày hiệu lực theo cấu trúc mới"""
        effective_str = self._extract_metadata(metadata_section, 'Ngày hiệu lực:')
        
        # Xử lý giá trị mặc định
        if effective_str in ["Đã biết", "Liên hệ"]:
            return None
        
        # Trích xuất từ các định dạng phức tạp
        match = re.search(r"\d{2}/\d{2}/\d{4}", effective_str)
        return datetime.strptime(match.group(), "%d/%m/%Y") if match else None

    def _extract_gazette_info(self, metadata_section, info_type: str) -> str:
        """Trích xuất thông tin công báo phiên bản mới - Cập nhật cho cấu trúc HTML mới"""
        try:
            # Tìm tất cả các thẻ td chứa label
            tds = metadata_section.find_all('td', string=lambda t: t and t.strip() in ['Ngày công báo:', 'Số công báo:'])
            
            info_map = {}
            
            for td in tds:
                label = td.get_text(strip=True).replace(':', '').lower()
                value_td = td.find_next_sibling('td')
                
                if value_td:
                    # Làm sạch dữ liệu
                    value = value_td.get_text(" ", strip=True)
                    info_map[label] = value if value not in ["Đang cập nhật", "Chưa công bố"] else ""
            
            # Xử lý theo info_type yêu cầu
            if info_type == 'date':
                return info_map.get('ngày công báo', "")
            elif info_type == 'number':
                return info_map.get('số công báo', "")
            
            return ""
        
        except Exception as e:
            logger.error(f"Lỗi trích xuất thông tin công báo: {str(e)}", exc_info=True)
            return ""

    def _extract_status(self, metadata_section) -> str:
        """Phân loại trạng thái hiệu lực theo tiêu chí mới"""
        status_str = self._extract_metadata(metadata_section, 'Tình trạng:').lower()
        
        status_map = {
            'còn hiệu lực': 'valid',
            'hết hiệu lực': 'expired',
            'đã biết': 'unknown',
            'đang cập nhật': 'pending'
        }
        
        return status_map.get(status_str, 'unknown')

    def _clean_content(self, content_div) -> str:
        """Phiên bản cải tiến làm sạch nội dung"""
        if not content_div:
            return ""
        
        # Loại bỏ các thành phần không cần thiết
        unwanted = content_div.find_all(['script', 'style', 'iframe', 'nav', 'footer', 'aside'])
        for tag in unwanted:
            tag.decompose()
        
        # Xóa các thuộc tính style và class
        for tag in content_div.find_all(True):
            tag.attrs = {}
        
        # Chuẩn hóa khoảng trắng và định dạng
        text = content_div.get_text('\n', strip=True)
        cleaned_lines = []
        for line in text.splitlines():
            line = re.sub(r'\s+', ' ', line).strip()
            if line:
                cleaned_lines.append(line)
        
        return '\n\n'.join(cleaned_lines)

    def _save_to_db(self, data: dict):
        """Phiên bản cải tiến xử lý lưu dữ liệu"""
        with DatabaseManager() as db:
            try:
                # Xử lý dữ liệu ngày tháng
                date_fields = ['issue_date', 'effective_date', 'gazette_date']
                for field in date_fields:
                    if isinstance(data.get(field), str):
                        data[field] = self._parse_flexible_date(data[field])
                
                # Xử lý giá trị mặc định
                data.setdefault('status', 'unknown')
                data['gazette_number'] = data.get('gazette_number') or ""
                
                document = LegalDocument(**data)
                db.insert_data(document)
                logger.info(f"Đã lưu văn bản {data['document_number']}")
                
            except Exception as e:
                logger.error(f"Lỗi khi lưu văn bản: {str(e)}")
                raise

    def _parse_flexible_date(self, date_str: str) -> Optional[datetime]:
        """Xử lý các định dạng ngày tháng linh hoạt"""
        if not date_str:
            return None
        
        formats = [
            "%d/%m/%Y", "%Y-%m-%d", "%d %m %Y",
            "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None