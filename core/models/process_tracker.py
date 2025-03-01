from sqlalchemy import Column, String, DateTime, Integer, Enum, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from core.models.base import Base
from datetime import datetime

class ProcessTracker(Base):
    __tablename__ = 'process_tracker'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('legal_documents.id'), nullable=False)  # ForeignKey đến legal_documents.id
    document_type = Column(Enum('law', 'judgment', 'qa', name='doc_type'), nullable=False)
    status = Column(Enum('pending', 'processing', 'success', 'failed', name='process_status'), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    retry_count = Column(Integer, default=0)
    error_log = Column(Text)

    
    document = relationship("LegalDocument", back_populates="process_trackers")
    crawl_tracker_id = Column(Integer, ForeignKey('crawl_tracker.id'), nullable=True, comment="ID của CrawlTracker liên kết")
    crawl_record = relationship("CrawlTracker", back_populates="process_records")
    processed_articles = relationship("ProcessedArticle", back_populates="process_tracker")
    
    # Index cho các trường thường xuyên được truy vấn
    __table_args__ = (
        Index('ix_proc_tracker_doc_id', 'document_id'),
        Index('ix_proc_tracker_status', 'status'),
        Index('ix_proc_tracker_type', 'document_type'),
    )

    def __repr__(self):
        return f"<ProcessTracker {self.document_type}-{self.document_id} [{self.status}]>"