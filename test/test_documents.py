import sys
import os
import logging
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import DatabaseManager
from core.models import (  # Thêm import các model
    LegalDocument,
    LegalQA,
    Judgment,
    JudgmentDocumentRelation
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        with DatabaseManager() as db:
            # Kiểm tra trạng thái các bảng
            status = db.check_tables_data()
            logger.info("\n=== TRẠNG THÁI BẢNG ===")
            for table, info in status.items():
                logger.info(f"{table}: {info['status']} ({info['count']} bản ghi)")

            # Lấy và hiển thị mẫu
            samples = db.get_random_samples()
            print_samples(samples)
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)

def print_samples(samples):
    """Hàm phụ trợ in kết quả mẫu"""
    for table, data in samples.items():
        print(f"\n=== {table.upper().replace('_', ' ')} ===")
        if isinstance(data, str):
            print(data)
        else:
            for item in data:
                print("-" * 50)
                if table == 'relations':
                    print(f"Relation ID: {item['relation'].id}")
                    print(f"Judgment: {item['judgment'].to_dict() if item['judgment'] else 'Không tồn tại'}")
                    print(f"Document: {item['document'].to_dict() if item['document'] else 'Không tồn tại'}")
                else:
                    print(json.dumps(
                        item.to_dict(),
                        indent=2,
                        ensure_ascii=False,
                        default=str  # Xử lý các trường hợp đặc biệt còn lại
                    ))

if __name__ == "__main__":
    main()