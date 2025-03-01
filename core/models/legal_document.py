from sqlalchemy import Column, Integer, String, Date, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.models.base import Base
from datetime import datetime as dt, date

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_number = Column(String(255), nullable=False)
    document_type = Column(String(255))
    issuing_authority = Column(String(255))
    signer = Column(String(255))
    issue_date = Column(Date)
    effective_date = Column(String(50))
    gazette_date = Column(Date)
    gazette_number = Column(String(100))
    status = Column(String(100))
    metadata_html = Column(Text)
    content_html = Column(Text)  
    content_text = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    related_judgments = relationship(
        "Judgment",
        secondary="judgment_document_relations",
        back_populates="related_documents"
    )
    
    process_trackers = relationship("ProcessTracker", back_populates="document")
    processed_articles = relationship("ProcessedArticle", back_populates="document")
    
    def to_dict(self):
        return {
            "id": self.id,
            "document_number": self.document_number,
            "document_type": self.document_type,
            "issuing_authority": self.issuing_authority,
            "issue_date": self.issue_date.isoformat() if self.issue_date else None,
            "status": self.status,
            "effective_date": self.effective_date,
            "gazette_date": self.gazette_date.isoformat() if self.gazette_date else None,
            "gazette_number": self.gazette_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Thêm các trường khác nếu cần
        }