import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name=__name__, log_file="legal_crawler.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Tạo thư mục logs nếu chưa tồn tại
    os.makedirs("logs", exist_ok=True)

    # File handler với xoay vòng log
    file_handler = RotatingFileHandler(
        f"logs/{log_file}",
        maxBytes=1024*1024*10,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger