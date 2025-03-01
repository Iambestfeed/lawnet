from sqlalchemy import Column, String, DateTime, Integer, Enum
from core.models.base import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class CrawlTracker(Base):
    __tablename__ = 'crawl_tracker'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(255), nullable=False)
    document_type = Column(Enum('law', 'judgment', name='doc_type'), nullable=False)
    status = Column(Enum('pending', 'success', 'failed', name='crawl_status'), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    last_attempt = Column(DateTime)
    retry_count = Column(Integer, default=0)
    error_log = Column(String(500))
    
    process_records = relationship("ProcessTracker", back_populates="crawl_record")
    
    def __repr__(self):
        return f"<CrawlTracker {self.document_type}-{self.document_id} [{self.status}]>"