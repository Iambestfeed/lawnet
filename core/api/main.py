from fastapi import FastAPI, Depends
from core.database import get_db
from core.models import LegalDocument
from typing import List

app = FastAPI()

@app.get("/documents", response_model=List[LegalDocument])
async def get_documents(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return db.query(LegalDocument).offset(skip).limit(limit).all()

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str, db=Depends(get_db)):
    return db.query(LegalDocument).filter(LegalDocument.document_number == doc_id).first()