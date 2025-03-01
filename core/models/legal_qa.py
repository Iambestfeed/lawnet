from sqlalchemy import Column, Integer, Text, String, JSON, DateTime
from sqlalchemy.sql import func
from core.models.base import Base

class LegalQA(Base):
    __tablename__ = "legal_qa"
    
    id = Column(Integer, primary_key=True, index=True)
    question_html = Column(Text)
    answer_html = Column(Text)
    category = Column(String(255))
    author = Column(String(255))
    tags = Column(JSON)
    related_documents = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "author": self.author,
            "tags": self.tags,
            "related_documents": self.related_documents,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "question_html": self.question_html,
            "answer_html": self.answer_html
        }