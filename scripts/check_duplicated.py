import sys
import os
import logging
import pandas as pd
from sqlalchemy import func, text
from collections import Counter

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import DatabaseManager
from core.models import LegalDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_duplicate_document_numbers():
    """Kiểm tra document_number xuất hiện nhiều lần trong bảng legal_documents"""
    try:
        with DatabaseManager() as db:
            # Cách 1: Sử dụng SQLAlchemy ORM
            duplicates = db.session.query(
                LegalDocument.document_number,
                func.count(LegalDocument.id).label('count')
            ).group_by(
                LegalDocument.document_number
            ).having(
                func.count(LegalDocument.id) > 1
            ).order_by(
                func.count(LegalDocument.id).desc()
            ).all()
            
            # Cách 2: Sử dụng raw SQL (nếu cách 1 có vấn đề)
            # query = text("""
            #     SELECT document_number, COUNT(id) as count
            #     FROM legal_documents
            #     GROUP BY document_number
            #     HAVING COUNT(id) > 1
            #     ORDER BY COUNT(id) DESC;
            # """)
            # duplicates = db.session.execute(query).fetchall()
            
            # In kết quả
            if not duplicates:
                logger.info("Không tìm thấy document_number trùng lặp")
                return
                
            logger.info(f"Tìm thấy {len(duplicates)} document_number bị trùng lặp")
            
            # In top 10 document_number trùng lặp nhiều nhất
            logger.info("Top 10 document_number trùng lặp nhiều nhất:")
            for doc_num, count in duplicates:
                logger.info(f"Document Number: {doc_num} - Số lần xuất hiện: {count}")
                
            '''# Lấy chi tiết về các bản ghi trùng lặp (Top 3 document number trùng lặp nhiều nhất)
            logger.info("\nChi tiết về các bản ghi trùng lặp (Top 3):")
            for doc_num, count in duplicates[:3]:
                duplicate_docs = db.session.query(LegalDocument).filter(
                    LegalDocument.document_number == doc_num
                ).all()
                
                logger.info(f"\n=== Chi tiết cho document_number: {doc_num} ===")
                for doc in duplicate_docs:
                    logger.info(f"ID: {doc.id}, Document Number: {doc.document_number}, Type: {doc.document_type}, Authority: {doc.issuing_authority}, Issue Date: {doc.issue_date}")
            ''' 
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra document_number trùng lặp: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    check_duplicate_document_numbers()