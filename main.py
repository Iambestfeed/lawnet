import argparse
import logging
import sys
from typing import Optional
from core.database import DatabaseManager, engine
import subprocess
from core.models import LegalDocument, LegalQA, Judgment, Base, CrawlTracker, ProcessTracker, ProcessedArticle
from datetime import datetime

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('legal_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def handle_migrations(command: str):
    """Xử lý các lệnh migration bằng Alembic với logging chi tiết"""
    try:
        logger.info(f"Executing migration command: alembic {command}")
        
        result = subprocess.run(
            ['alembic'] + command.split(),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ghi log chi tiết
        if result.stdout:
            logger.info("Migration output:\n" + result.stdout)
        if result.stderr:
            logger.debug("Migration debug info:\n" + result.stderr)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Migration failed with error code {e.returncode}")
        logger.error(f"Error details:\n{e.stderr}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Legal Database Management System',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid commands',
        dest='command',
        metavar='COMMAND'
    )

    # Lệnh khởi tạo database
    init_parser = subparsers.add_parser(
        'initdb',
        help='Khởi tạo cấu trúc database (Dùng Alembic migration)'
    )
    
    # Lệnh thêm dữ liệu mẫu
    sample_parser = subparsers.add_parser(
        'adddata',
        help='Thêm dữ liệu mẫu vào database'
    )
    
    # Lệnh xóa database
    clear_parser = subparsers.add_parser(
        'cleardb',
        help='⚠️ Xóa toàn bộ dữ liệu và cấu trúc (Chỉ dùng cho môi trường phát triển)'
    )
    
    # Lệnh import/export
    io_parser = subparsers.add_parser(
        'io',
        help='Thao tác import/export dữ liệu',
        description='Thực hiện các thao tác import/export dữ liệu'
    )
    io_parser.add_argument(
        'action',
        choices=['import', 'export'],
        help='Loại thao tác (import/export)'
    )
    # Thêm tùy chọn mới cho initdb
    init_parser.add_argument(
        '--table',
        help='Chỉ tạo bảng cụ thể (Dùng cho dev)'
    )
    init_parser.add_argument(
        '--safe',
        action='store_true',
        help='Chế độ an toàn - chỉ dùng Alembic migration'
    )
    io_parser.add_argument(
        '--file',
        required=True,
        help='Đường dẫn file dữ liệu'
    )

    # Lệnh migration
    migrate_parser = subparsers.add_parser(
        'migrate',
        help='Quản lý database migration',
        description='Thực hiện các thao tác migration với Alembic'
    )
    migrate_parser.add_argument(
        'action',
        nargs='?',
        default='upgrade',
        choices=['upgrade', 'downgrade'],
        help='Hành động migration (mặc định: upgrade)'
    )
    migrate_parser.add_argument(
        'revision',
        nargs='?',
        default='head',
        help='Phiên bản migration đích (mặc định: head)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        # Xử lý các lệnh migration
        if args.command == 'migrate':
            if args.action == 'upgrade':
                handle_migrations(f'upgrade {args.revision}')
            elif args.action == 'downgrade':
                handle_migrations(f'downgrade {args.revision}')
                
        # Xử lý các lệnh khác
        else:
            with DatabaseManager() as db:
                if args.command == 'initdb':
                    if args.safe:
                        logger.info("🚀 Khởi tạo database an toàn bằng Alembic...")
                        handle_migrations("upgrade head")
                    elif args.table:
                        logger.info(f"🛠 Tạo bảng {args.table} (chế độ dev)...")
                        try:
                            # Dynamic table creation
                            table_class = globals().get(args.table)
                            if not table_class:
                                raise ValueError(f"Không tìm thấy model {args.table}")
                            
                            table_class.__table__.create(bind=engine, checkfirst=True)
                            logger.info(f"✅ Đã tạo bảng {args.table}")
                        except Exception as e:
                            logger.error(f"❌ Lỗi khi tạo bảng: {str(e)}")
                            sys.exit(1)
                    else:
                        logger.warning("⚠️ Chế độ initdb mặc định chỉ dành cho dev!")
                        confirm = input("Bạn có chắc muốn tạo toàn bộ tables? (yes/no): ")
                        if confirm.lower() == 'yes':
                            Base.metadata.create_all(bind=engine)
                            logger.info("✅ Đã tạo tất cả bảng")
                        else:
                            logger.info("Hủy thao tác")
                    
                elif args.command == 'adddata':
                    # Thêm dữ liệu mẫu sử dụng ORM
                    from core.models import LegalDocument, LegalQA, Judgment
                    from datetime import datetime
                    
                    try:
                        with DatabaseManager() as session:
                            # Thêm văn bản luật
                            doc = LegalDocument(
                                document_number="174/QĐ-BVHTTDL",
                                document_type="Quyết định",
                                issuing_authority="Bộ Văn hoá, Thể thao và du lịch",
                                signer="Tạ Quang Đông",
                                issue_date=datetime(2025, 1, 21).date(),
                                effective_date="Đã biết",
                                content_html="<html>Nội dung mẫu văn bản...</html>"
                            )
                            session.add(doc)
                            
                            # Thêm QA
                            qa = LegalQA(
                                question_html="<p>Câu hỏi mẫu về luật du lịch?</p>",
                                answer_html="<div>Trả lời mẫu...</div>",
                                category="Luật Dân sự",
                                author="Nguyễn Văn A",
                                tags=["du lịch", "hành chính"],
                                related_documents=[1]
                            )
                            session.add(qa)
                            
                            # Thêm bản án
                            judgment = Judgment(
                                case_name="Vụ án tranh chấp hợp đồng xây dựng",
                                case_number="26/2024/KDTM-GĐT",
                                issuing_authority="Tòa án nhân dân cấp cao",
                                trial_level="Giám đốc thẩm",
                                field="Kinh tế",
                                judgment_date=datetime(2024, 9, 26).date(),
                                keywords=["hợp đồng xây dựng", "tranh chấp"],
                                content_html="<html>Nội dung bản án...</html>",
                                content_text="Nội dung văn bản đã được làm sạch...",
                                related_parties={
                                    "nguyen_don": "Công ty A",
                                    "bi_don": "Công ty B"
                                }
                            )
                            session.add(judgment)
                            
                            session.commit()
                            logger.info("Sample data inserted successfully")
                            
                    except Exception as e:
                        logger.error(f"Failed to insert sample data: {str(e)}")
                        sys.exit(1)
                    
                elif args.command == 'cleardb':
                    confirm = input("Bạn có chắc chắn muốn xóa toàn bộ dữ liệu? (yes/no): ")
                    if confirm.lower() == 'yes':
                        Base.metadata.drop_all(bind=engine)
                        logger.warning("Database cleared successfully")
                    else:
                        logger.info("Hủy thao tác xóa database")
                        
                elif args.command == 'io':
                    if args.action == 'export':
                        db.export_data(args.table, args.file)
                    else:
                        db.import_data(args.table, args.file)

    except Exception as e:
        logger.error(f"Operation failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()