from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import JSONB  # Sử dụng JSONB cho PostgreSQL
from sqlalchemy.orm import relationship
from core.models.base import Base
from datetime import datetime

class ProcessedArticle(Base):
    __tablename__ = 'processed_articles'
    
    # Khóa chính
    article_id = Column(String(150), primary_key=True, comment="ID bài viết: Format LAW-1234-ART-45")
    
    # Tham chiếu đến văn bản luật
    document_id = Column(Integer, ForeignKey('legal_documents.id'), nullable=False, comment="ID của tài liệu luật")
    
    content = Column(Text, comment="Nội dung đã chuẩn hóa")
    
    # Metadata cấu trúc
    structural_metadata = Column(JSONB, comment="""
    JSON metadata:
    {
        "hierarchy": ["Phần I", "Chương 2", "Mục 3"], 
        "prefix": "Phần I/Chương 2/Mục 3/",
        "article_number": "Điều 45"
    }
    """)
    
    # Thông tin xử lý
    process_tracker_id = Column(Integer, ForeignKey('process_tracker.id'), comment="ID tham chiếu đến Process Tracker")
    processed_at = Column(DateTime, default=datetime.now, comment="Thời điểm xử lý")
    
    # Quan hệ với LegalDocument và ProcessTracker
    document = relationship("LegalDocument", back_populates="processed_articles")
    process_tracker = relationship("ProcessTracker", back_populates="processed_articles")
    
    # Index
    __table_args__ = (
        # Index trên structural_metadata['hierarchy'] (dành cho PostgreSQL JSONB)
        Index('ix_article_hierarchy', structural_metadata, postgresql_using='gin'),
        # Index trên thời gian xử lý
        Index('ix_processed_at', 'processed_at'),
    )

    def __repr__(self):
        return f"<ProcessedArticle {self.article_id} (Document: {self.document_id})>"