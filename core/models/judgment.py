from sqlalchemy import Column, Integer, String, Date, Text, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.models.base import Base
from datetime import datetime as dt, date

class Judgment(Base):
    __tablename__ = "judgments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String(255))  # Thêm trường tên bản án
    case_number = Column(String(255))
    issuing_authority = Column(String(255))  # Đổi tên từ court
    trial_level = Column(String(50))  # Thêm cấp xét xử
    field = Column(String(100))  # Thêm lĩnh vực
    judgment_date = Column(Date)
    keywords = Column(JSON)  # Thêm trường từ khóa
    metadata_html = Column(Text)  # Thêm trường này
    content_html = Column(Text)   # Thêm trường này
    content_text = Column(Text)
    related_parties = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    related_documents = relationship(
        "LegalDocument",
        secondary="judgment_document_relations",
        back_populates="related_judgments"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "case_name": self.case_name,
            "case_number": self.case_number,
            "issuing_authority": self.issuing_authority,
            "trial_level": self.trial_level,
            "field": self.field,
            "judgment_date": self.judgment_date.isoformat() if self.judgment_date else None,
            "keywords": self.keywords or []
        }