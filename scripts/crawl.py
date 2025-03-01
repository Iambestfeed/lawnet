import argparse
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.crawlers.search_crawler import SearchCrawler
from core.crawlers.crawl_manager import CrawlProcessingService
import logging

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Legal Document Crawling System')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Crawl IDs command
    crawl_ids_parser = subparsers.add_parser('crawl-ids', help='Crawl new document IDs')
    crawl_ids_parser.add_argument('type', choices=['law', 'judgment'])
    crawl_ids_parser.add_argument('--start-page', type=int, default=1, 
                                help='Trang bắt đầu (mặc định: 1)')
    crawl_ids_parser.add_argument('--end-page', type=int, default=None,
                                help='Trang kết thúc (nếu không chỉ định sẽ crawl đến khi hết)')
    crawl_ids_parser.add_argument('--max-empty', type=int, default=3,
                                help='Số trang trống liên tiếp tối đa (mặc định: 3)')
    crawl_ids_parser.add_argument('--num-worker', type=int, default=4,
                                help='Số processor (mặc định: 4)')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process pending documents')
    process_parser.add_argument('type', choices=['law', 'judgment'])
    process_parser.add_argument('--batch-size', type=int, default=100)
    process_parser.add_argument('--max-retries', type=int, default=3)
    process_parser.add_argument('--num-worker', type=int, default=8)

    args = parser.parse_args()

    if args.command == 'crawl-ids':
        crawler = SearchCrawler(args.type)
        crawler.crawl_ids(
            start_page=args.start_page,
            end_page=args.end_page, 
            max_empty_pages=args.max_empty,
            num_processes=args.num_worker
        )
    elif args.command == 'process':
        processor = CrawlProcessingService(
            doc_type=args.type,
            batch_size=args.batch_size,
            max_retries=args.max_retries,
            num_processes=args.num_worker,
        )
        processor.process_pending()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    main()