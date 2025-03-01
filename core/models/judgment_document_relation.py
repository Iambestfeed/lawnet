from sqlalchemy import Column, Integer, String, ForeignKey
from core.models.base import Base

class JudgmentDocumentRelation(Base):
    __tablename__ = "judgment_document_relations"
    
    id = Column(Integer, primary_key=True, index=True)
    judgment_id = Column(Integer, ForeignKey("judgments.id"))
    document_id = Column(Integer, ForeignKey("legal_documents.id"))
    relation_type = Column(String(100))
    
    def to_dict(self):
        return {
            "id": self.id,
            "judgment_id": self.judgment_id,
            "document_id": self.document_id,
            "relation_type": self.relation_type
        }