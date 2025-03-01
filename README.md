# LawNet: Legal Document Crawling & Processing System

## 1. Introduction
LawNet is a legal document collection, processing, and management system. It consists of the following main components:
- **Crawler**: Collects data from legal sources.
- **Database**: Stores legal document data.
- **Processing**: Cleans and extracts information from collected data.
- **API**: Provides an interface for querying data.

## 2. Installation

### 2.1. **Clone the Repository**
```sh
git clone https://github.com/Iambestfeed/lawnet.git
cd lawnet
```

### 2.2. **Create a Conda Virtual Environment**
```sh
conda env create -f environment.yml
conda activate lawnet
```

## 3. Quickstart

Run the following commands to initialize the database and start crawling data immediately.

### **Step 1: Initialize Database**
```sh
python main.py initdb
```

### **Step 2: Start Crawling Data**
```sh
python scripts/crawl.py crawl-ids law --start-page 1 --end-page 10
python scripts/crawl.py process law --batch-size 100 --max-retries 3 --num-worker 8
```

## 4. Directory Structure

```
├── alembic/                # Database migration management
├── cache/                  # Temporary storage
├── config/                 # System configurations
├── core/                   # Main system components
│   ├── api/                # API services
│   ├── crawlers/           # Crawling components
│   ├── models/             # ORM models definition
│   ├── processors/         # Data processing components
│   ├── utils/              # Utility functions
├── scripts/                # Helper scripts
```

## 5. Crawling System

### 5.1. **Crawlers Overview**
The `core/crawlers/` directory contains components responsible for data collection:
- `crawl_manager.py`: Manages the overall crawling process.
- `judgment_crawler.py`: Crawls court judgments.
- `law_crawler.py`: Crawls legal documents.
- `qa_crawler.py`: Crawls legal Q&A.
- `search_crawler.py`: Handles document search crawling.

### 5.2. **Crawl Process**
The crawl process consists of two main steps:
1. **Crawl IDs**: Collects document IDs from legal sources.
2. **Crawl Posts**: Fetches detailed content for each document based on collected IDs.

#### **Step 1: Crawling Document IDs**
```sh
python scripts/crawl.py crawl-ids law --start-page 1 --end-page 10
```

#### **Step 2: Crawling Document Content (Posts)**
```sh
python scripts/crawl.py process law --batch-size 100 --max-retries 3 --num-worker 8
```

### 5.3. **Crawl Manager**
The `CrawlProcessingService` in `crawl_manager.py` is responsible for managing and processing document crawling tasks.

## 6. Database and Processing

### **6.1. Database Schema**
The system uses PostgreSQL for data storage. The main models in `core/models/` include:
- `legal_document.py`: Stores legal documents.
- `judgment.py`: Stores court judgments.
- `legal_qa.py`: Stores legal Q&A.

Run database migration with:
```sh
alembic upgrade head
```

### **6.2. Data Processing**
The `core/processors/` directory contains scripts for processing data:
- `legal_processor.py`: Cleans and structures legal documents.
- `add_item.py`: Supports inserting new data into the system.

## 7. API Services
The main API is defined in `core/api/main.py` using FastAPI.
Start the API server:
```sh
uvicorn core.api.main:app --host 0.0.0.0 --port 8000
```

## 8. Usage Guide

### **8.1. Initialize Database**
```sh
python main.py initdb
```

### **8.2. Add Sample Data**
```sh
python main.py adddata
```

### **8.3. Clear Database** (For development only)
```sh
python main.py cleardb
```

### **8.4. Export/Import Data**
```sh
python main.py io export --file output.json
python main.py io import --file input.json
```

## 9. Conclusion
LawNet provides an efficient solution for collecting and managing legal documents. If any issues arise, please update the documentation or report errors!

