import sys
import os
import logging
import json
import hashlib
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database import DatabaseManager
from core.models import LegalDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def json_serializer(obj):
    """Hàm hỗ trợ chuyển đổi các kiểu dữ liệu không phải JSON sang string"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

def extract_full_document_data(doc, include_content=True):
    """
    Trích xuất tất cả thông tin từ đối tượng LegalDocument mà không phụ thuộc vào to_dict()
    
    Args:
        doc: Đối tượng LegalDocument
        include_content (bool): Có bao gồm nội dung hay không
        
    Returns:
        dict: Dictionary chứa thông tin đầy đủ của document
    """
    # Thông tin cơ bản luôn được trích xuất
    data = {
        "id": doc.id,
        "document_number": doc.document_number,
        "document_type": doc.document_type,
        "issuing_authority": doc.issuing_authority,
        "signer": doc.signer,
        "issue_date": doc.issue_date.isoformat() if doc.issue_date else None,
        "status": doc.status,
        "effective_date": doc.effective_date,
        "gazette_date": doc.gazette_date.isoformat() if doc.gazette_date else None,
        "gazette_number": doc.gazette_number,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }
    
    # Chỉ thêm nội dung khi include_content=True
    if include_content:
        data.update({
            "metadata_html": doc.metadata_html,
            "content_html": doc.content_html,
            "content_text": doc.content_text
        })
    
    return data

def generate_object_id():
    """
    Tạo một MongoDB ObjectId chuẩn theo định dạng 24 ký tự hex
    """
    # Tạo giá trị ngẫu nhiên cho ObjectId
    random_value = uuid.uuid4().hex[:24]
    return random_value

def generate_query_id(document_id):
    """
    Tạo query_id bằng cách hash document_id 
    """
    # Sử dụng MD5 để tạo query_id từ document_id
    return hashlib.md5(document_id.encode('utf-8')).hexdigest()

def find_documents_by_number_list(file_path, output_file="found_documents.json", include_content=True, mongo_format_output=None):
    """
    Tìm tất cả document trong bảng legal_documents có document_number trong file
    
    Args:
        file_path (str): Đường dẫn đến file document_numbers.txt
        output_file (str): Tên file JSON output
        include_content (bool): Có bao gồm nội dung HTML và text hay không
        mongo_format_output (str): Nếu có giá trị, sẽ tạo file output theo định dạng MongoDB
    """
    try:
        # Đọc danh sách document_numbers từ file
        with open(file_path, 'r', encoding='utf-8') as f:
            document_numbers = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Đã đọc {len(document_numbers)} document numbers từ file {file_path}")
        
        # Tìm các document trong database
        found_documents = []
        not_found_numbers = list(document_numbers)  # Bản sao để theo dõi các số không tìm thấy
        documents_by_number = {}  # Theo dõi những document number có nhiều document
        
        # Danh sách document_ids để tạo format MongoDB
        document_ids = []
        
        with DatabaseManager() as db:
            for doc_num in document_numbers:
                documents = db.session.query(LegalDocument).filter(
                    LegalDocument.document_number == doc_num
                ).all()
                
                if documents:
                    # Theo dõi document_number được tìm thấy
                    if doc_num in not_found_numbers:
                        not_found_numbers.remove(doc_num)
                    
                    # Lưu số lượng document cho mỗi document_number
                    documents_by_number[doc_num] = len(documents)
                    
                    # Trích xuất thông tin đầy đủ cho mỗi document
                    for doc in documents:
                        doc_data = extract_full_document_data(doc, include_content)
                        found_documents.append(doc_data)
                        
                        # Tạo document_id từ document_number và id
                        document_id = f"{doc.document_number}#{doc.id}"
                        document_ids.append(document_id)
                    
                    logger.info(f"Tìm thấy {len(documents)} document với document_number: {doc_num}")
                else:
                    logger.warning(f"Không tìm thấy document nào với document_number: {doc_num}")
        
        # Ghi kết quả ra file JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_found": len(found_documents),
                "total_searched": len(document_numbers),
                "not_found_count": len(not_found_numbers),
                "not_found_numbers": not_found_numbers,
                "timestamp": datetime.now().isoformat(),
                "include_content": include_content,
                "documents": found_documents
            }, f, ensure_ascii=False, indent=2, default=json_serializer)
        
        logger.info(f"Đã tìm thấy tổng cộng {len(found_documents)} documents")
        logger.info(f"Kết quả đã được lưu vào file {output_file}")
        
        # Tạo báo cáo tóm tắt
        create_summary_report(document_numbers, found_documents, not_found_numbers, documents_by_number)
        
        # Tạo output theo định dạng MongoDB nếu được yêu cầu
        if mongo_format_output:
            create_mongo_format_output(document_ids, mongo_format_output)
            
    except FileNotFoundError:
        logger.error(f"Không tìm thấy file {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Lỗi khi tìm documents: {str(e)}")
        sys.exit(1)

def create_mongo_format_output(document_ids, output_file):
    """
    Tạo file output theo định dạng MongoDB với _id, document_id và query_id
    
    Args:
        document_ids (list): Danh sách các document_id
        output_file (str): Tên file output
    """
    try:
        # Tạo mảng kết quả
        result = []
        
        for doc_id in document_ids:
            record = {
                "_id": {
                    "$oid": generate_object_id()
                },
                "document_id": doc_id
            }
            result.append(record)
        
        # Ghi kết quả ra file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Đã tạo file MongoDB format với {len(result)} bản ghi và lưu vào file {output_file}")
        
        # In mẫu 2 bản ghi đầu tiên
        if result:
            logger.info("Mẫu output MongoDB format:")
            sample = json.dumps(result[:2], ensure_ascii=False, indent=2)
            logger.info(sample)
            
    except Exception as e:
        logger.error(f"Lỗi khi tạo MongoDB format output: {str(e)}")

def create_summary_report(document_numbers, found_documents, not_found_numbers, documents_by_number):
    """Tạo báo cáo tóm tắt kết quả tìm kiếm"""
    # Tạo báo cáo
    report = {
        "total_document_numbers": len(document_numbers),
        "found_document_numbers": len(documents_by_number),
        "not_found_document_numbers": len(not_found_numbers),
        "not_found_list": not_found_numbers,
        "documents_with_duplicates": [num for num, count in documents_by_number.items() if count > 1],
        "summary_by_document_type": {},
        "summary_by_issuing_authority": {},
        "summary_by_year": {},
        "documents_by_number": documents_by_number
    }
    
    # Thống kê theo loại văn bản và cơ quan ban hành
    for doc in found_documents:
        doc_type = doc.get('document_type', 'Không xác định')
        authority = doc.get('issuing_authority', 'Không xác định')
        
        # Xử lý thống kê theo năm
        issue_date = doc.get('issue_date')
        year = "Không xác định"
        if issue_date:
            try:
                year = issue_date.split('-')[0]  # Lấy năm từ chuỗi ISO format (YYYY-MM-DD)
            except:
                pass
        
        # Cập nhật thống kê
        if doc_type in report["summary_by_document_type"]:
            report["summary_by_document_type"][doc_type] += 1
        else:
            report["summary_by_document_type"][doc_type] = 1
            
        if authority in report["summary_by_issuing_authority"]:
            report["summary_by_issuing_authority"][authority] += 1
        else:
            report["summary_by_issuing_authority"][authority] = 1
            
        if year in report["summary_by_year"]:
            report["summary_by_year"][year] += 1
        else:
            report["summary_by_year"][year] = 1
    
    # Lưu báo cáo ra file
    with open("documents_search_report.json", 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Báo cáo tóm tắt đã được lưu vào file documents_search_report.json")
    
    # In một số thông tin quan trọng
    logger.info(f"\n=== TÓM TẮT KẾT QUẢ TÌM KIẾM ===")
    logger.info(f"Tổng số document_number cần tìm: {len(document_numbers)}")
    logger.info(f"Số document_number tìm thấy: {len(documents_by_number)} ({len(documents_by_number)/len(document_numbers)*100:.2f}%)")
    logger.info(f"Số document_number không tìm thấy: {len(not_found_numbers)} ({len(not_found_numbers)/len(document_numbers)*100:.2f}%)")
    
    duplicate_count = len([num for num, count in documents_by_number.items() if count > 1])
    if duplicate_count > 0:
        logger.info(f"Có {duplicate_count} document_number có nhiều hơn 1 document")
        
        # Liệt kê document_number có nhiều bản ghi nhất
        duplicate_docs = sorted([(num, count) for num, count in documents_by_number.items() if count > 1], 
                              key=lambda x: x[1], reverse=True)
        
        # In top 5 document_number có nhiều bản ghi nhất
        if duplicate_docs:
            logger.info("Top document_number có nhiều bản ghi nhất:")
            for i, (num, count) in enumerate(duplicate_docs[:5], 1):
                logger.info(f"{i}. {num}: {count} bản ghi")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Vui lòng cung cấp đường dẫn đến file document_numbers.txt")
        logger.info("Sử dụng: python script.py document_numbers.txt [output_file.json] [include_content] [mongo_format_output]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "found_documents.json"
    
    # Xác định có bao gồm nội dung hay không
    include_content = True
    if len(sys.argv) > 3:
        include_content = sys.argv[3].lower() in ['true', '1', 't', 'y', 'yes']
    
    # Xác định tên file MongoDB format output
    mongo_format_output = None
    if len(sys.argv) > 4:
        mongo_format_output = sys.argv[4]
    
    find_documents_by_number_list(input_file, output_file, include_content, mongo_format_output)