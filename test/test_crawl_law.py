# File: tests/test_crawl_law.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.crawlers.law_crawler import LawCrawler
import argparse
import logging
from datetime import datetime

def main():
    # Thiết lập logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Xử lý argument
    parser = argparse.ArgumentParser(description='Test crawler for legal documents')
    parser.add_argument('document_id', type=str, help='ID or path of the legal document to crawl')
    args = parser.parse_args()

    # Khởi tạo crawler
    crawler = LawCrawler()
    
    try:
        # Thực hiện crawl
        result = crawler.crawl(args.document_id, saving=False)
        
        # Hiển thị kết quả
        print("\n=== THÔNG TIN VĂN BẢN ===")
        print(f"Số hiệu: {result.get('document_number', 'N/A')}")
        print(f"Loại văn bản: {result.get('document_type', 'N/A')}")
        print(f"Cơ quan ban hành: {result.get('issuing_authority', 'N/A')}")
        print(f"Người ký: {result.get('signer', 'N/A')}")
        print(f"Ngày ban hành: {result['issue_date'].strftime('%d/%m/%Y') if result.get('issue_date') else 'N/A'}")
        print(f"Ngày hiệu lực: {result['effective_date'] if result.get('effective_date') else 'N/A'}")
        print(f"Ngày công báo: {result['gazette_date'].strftime('%d/%m/%Y') if result.get('gazette_date') else 'N/A'}")
        print(f"Số công báo: {result.get('gazette_number', 'N/A')}")
        print(f"Trạng thái: {result.get('status', 'N/A')}")
        
        print("\n=== NỘI DUNG XEM TRƯỚC ===")
        content = result.get('content_text', '')
        preview = (content[:300] + '...') if len(content) > 300 else content
        print(preview or "Không có nội dung")
        
        print("\n=== THÔNG TIN LƯU TRỮ ===")
        print(f"Đã lưu database: {'Thành công' if 'document_number' in result else 'Thất bại'}")
        print(f"Thời gian crawl: {datetime.now().strftime('%H:%M:%S')}")

    except Exception as e:
        logging.error(f"Crawl failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()