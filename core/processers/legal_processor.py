from bs4 import BeautifulSoup
import re
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from core.models import LegalDocument, ProcessTracker, ProcessedArticle
from core.database import SessionLocal
from datetime import datetime
from core.database import DatabaseManager

class LawDocumentProcessor:
    def __init__(self, doc: LegalDocument):
        self.doc = doc
        self.session = SessionLocal()
        self.structure_rules = self._load_structure_rules()

    def process(self):
        try:
            parsed_structure = self._parse_html_structure(self.doc.content_html)
            normalized = self._normalize_structure(parsed_structure)
            articles = self._extract_articles(normalized)
            self._save_articles(articles)
            self._update_process_tracker("success")
        except Exception as e:
            self._handle_processing_error(e)
        finally:
            self.session.close()

    def _parse_html_structure(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html.replace('\r\n', " "), 'html.parser')
        root = {"type": "root", "children": []}

        structure_patterns = {
            "PHẦN": r"^PHẦN\s+[A-Z]+",
            "CHƯƠNG": r"^Chương\s+[IVXLCDM]+",
            "MỤC": r"^Mục\s+\d+",
            "ĐIỀU": r"^Điều\s+\d+[\.:]?",  # Cải tiến regex để chỉ bắt đầu bằng Điều
            "KHOẢN": r"^\d+\.",  
            "ĐIỂM": r"^[a-z]\)" 
        }

        stack = [root]

        for element in soup.find_all(["p"]):
            text = element.get_text().strip()
            if not text:
                continue
            
            found_structure = False
            for key, pattern in structure_patterns.items():
                if re.match(pattern, text, re.IGNORECASE):
                    node = {
                        "type": key,
                        "number": self._extract_number(text, key),
                        "content": text,
                        "children": []
                    }
                    # Kiểm tra phân cấp
                    while len(stack) > 1 and not self._is_valid_parent(stack[-1]["type"], key):
                        stack.pop()
                    stack[-1]["children"].append(node)
                    stack.append(node)
                    found_structure = True
                    break
                    
            if not found_structure:
                content_node = {
                    "type": "CONTENT",
                    "content": text,
                    "children": []
                }
                if stack:
                    stack[-1]["children"].append(content_node)

        return root["children"]

    def _extract_articles(self, structure: List) -> List[Dict]:
        articles = []
        current_article = None

        def _traverse(node):
            nonlocal current_article
            if node["type"] == "ĐIỀU":
                # Tạo article mới
                current_article = {
                    "article_id": f"{self.doc.document_number}-ART-{node['number']}",
                    "number": node["number"],
                    "full_text": node["content"],
                    "content": [],
                }
                articles.append(current_article)
            elif current_article:
                # Xử lý nội dung sửa đổi
                if node["type"] in ["KHOẢN", "ĐIỂM", "CONTENT"]:
                    content = node["content"]
                    current_article["content"].append(content)

            for child in node.get("children", []):
                _traverse(child)

        for node in structure:
            _traverse(node)
            
        return articles
    
    def _infer_type(self, text: str) -> Optional[str]:
        """Infer cấu trúc type dựa trên nội dung text."""
        type_patterns = {
            "PHẦN": r"^PHẦN\s+[A-Z]+",
            "CHƯƠNG": r"^Chương\s+[IVXLCDM]+",
            "MỤC": r"^Mục\s+\d+",
            # "ĐIỀU": r"^Điều\s+\d+[\.:]?",  #  "ĐIỀU" should already be identified in parsing
            # "KHOẢN": r"^\d+\.",          # "KHOẢN" and "ĐIỂM" are usually within "ĐIỀU"
            # "ĐIỂM": r"^[a-z]\)"
        }
        for key, pattern in type_patterns.items():
            if re.match(pattern, text, re.IGNORECASE):
                return key
        return "CONTENT"  # Default to CONTENT if no structure type is inferred
    
    def _normalize_structure(self, raw_structure: List) -> List:
        """Chuẩn hóa cấu trúc theo Nghị định 34/2016 và 154/2020"""
        normalized = []
        hierarchy_levels = ["PHẦN", "CHƯƠNG", "MỤC", "TIỂU_MỤC", "ĐIỀU", "KHOẢN", "ĐIỂM"]
        
        # Stack để theo dõi phân cấp hiện tại
        stack = []
        
        for node in raw_structure:
            current = node
            
            # Tự động điền các cấp thiếu
            if current["type"] not in hierarchy_levels:
                current["type"] = self._infer_type(current["content"])
            
            # Xác định cấp hiện tại
            current_level = hierarchy_levels.index(current["type"]) if current["type"] in hierarchy_levels else -1
            
            # Xử lý stack để tìm parent phù hợp
            while stack:
                top_level = hierarchy_levels.index(stack[-1]["type"]) if stack[-1]["type"] in hierarchy_levels else -1
                
                # Nếu cấp hiện tại cao hơn hoặc bằng cấp trên cùng stack, pop stack
                if current_level <= top_level:
                    stack.pop()
                else:
                    break
            
            # Thêm node vào parent phù hợp
            if stack:
                stack[-1]["children"].append(current)
            else:
                normalized.append(current)
            
            # Đẩy node hiện tại vào stack nếu nó có thể là parent của các node tiếp theo
            if current["type"] in hierarchy_levels:
                stack.append(current)
        
        return normalized

    def _save_articles(self, articles: List[Dict]):
        for article in articles:
            existing = self.session.query(ProcessedArticle).filter_by(
                id=article["article_id"]
            ).first()
            
            if not existing:
                processed = ProcessedArticle(
                    id=article["article_id"],
                    document_id=self.doc.id,
                    article_number=article["number"],
                    original_text='\n'.join(article["content"]),
                    clean_text=self._clean_content(article["content"]),
                    processing_history=[
                        {"step": "parse", "timestamp": datetime.now().isoformat()}
                    ]
                )
                self.session.add(processed)

                tracker = ProcessTracker(
                    document_id=self.doc.id,
                    article_id=article["article_id"],
                    status='success',
                    completed_steps={"parsing": datetime.now().isoformat()},
                )
                self.session.add(tracker)
        
        self.session.commit()

    # Các hàm hỗ trợ giữ nguyên
    def _extract_number(self, text: str, element_type: str) -> str:
        patterns = {
            "ĐIỀU": r"Điều\s+(\d+)",
            "KHOẢN": r"^(\d+)\.",
            "CHƯƠNG": r"Chương\s+([IVXLCDM]+)",
            "ĐIỂM": r"^([a-z])\)"
        }
        match = re.search(patterns.get(element_type, r"(\d+)"), text)
        return match.group(1) if match else ""

    def _is_valid_parent(self, parent_type: str, current_type: str) -> bool:
        hierarchy = ["PHẦN", "CHƯƠNG", "MỤC", "ĐIỀU", "KHOẢN", "ĐIỂM"]
        try:
            return hierarchy.index(parent_type) < hierarchy.index(current_type)
        except ValueError:
            return False

    def _clean_content(self, content: List[str]) -> str:
        cleaned = []
        for text in content:
            text = re.sub(r"\s+", " ", text)
            text = re.sub(r"(?i)(điều\s+\d+)(?=\s)", r"[REF:\1]", text)  # Đánh dấu các tham chiếu
            cleaned.append(text.strip())
        return '\n'.join(cleaned)

    def _update_process_tracker(self, status: str):
        """Cập nhật trạng thái tổng thể"""
        tracker = self.session.query(ProcessTracker).filter_by(
            document_id=self.doc.id
        ).first()
        
        if tracker:
            tracker.status = status
            tracker.last_attempt = datetime.now()

    def _handle_processing_error(self, error: Exception):
        """Xử lý lỗi và ghi log"""
        error_msg = f"[{datetime.now()}] Error processing {self.doc.id}: {str(error)}"
        
        tracker = ProcessTracker(
            document_id=self.doc.id,
            status='failed',
            error_log=error_msg,
            retry_count=1
        )
        self.session.add(tracker)
        self.session.commit()

# Sử dụng thuật toán
def process_all_documents():
    session = SessionLocal()
    try:
        documents = session.query(LegalDocument).filter(
            LegalDocument.content_html.isnot(None)
        ).all()
        
        for doc in documents:
            processor = LawDocumentProcessor(doc)
            processor.process()
            
    finally:
        session.close()