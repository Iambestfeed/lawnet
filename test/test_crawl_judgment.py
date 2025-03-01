import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import từ core
from core.crawlers.judgment_crawler import JudgmentCrawler
from core.models.judgment import Judgment
import argparse
import logging

def main():
    # Thiết lập logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Xử lý argument
    parser = argparse.ArgumentParser(description='Test crawler for judgments')
    parser.add_argument('judgment_id', type=str, help='ID of the judgment to crawl')
    args = parser.parse_args()

    # Khởi tạo crawler
    crawler = JudgmentCrawler()
    
    try:
        # Thực hiện crawl
        result = crawler.crawl(args.judgment_id, saving = True)
        
        # Hiển thị kết quả
        print("\n=== METADATA ===")
        print(f"Tên bản án: {result.get('case_name', 'N/A')}")
        print(f"Số hiệu: {result.get('case_number', 'N/A')}")
        print(f"Cơ quan ban hành: {result.get('issuing_authority', 'N/A')}")
        print(f"Cấp xét xử: {result.get('trial_level', 'N/A')}")
        print(f"Lĩnh vực: {result.get('field', 'N/A')}")
        print(f"Ngày ban hành: {result['judgment_date'].strftime('%d/%m/%Y') if result.get('judgment_date') else 'N/A'}")
        print(f"Từ khóa: {', '.join(result.get('keywords', [])) or 'N/A'}")
        
        print("\n=== NỘI DUNG XEM TRƯỚC ===")
        content = result.get('content_text', '')
        preview = (content[:200] + '...') if len(content) > 200 else content
        print(preview or "Không có nội dung")
        
    except Exception as e:
        logging.error(f"Crawl failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()