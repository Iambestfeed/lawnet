from .legal_document import LegalDocument
from .legal_qa import LegalQA
from .judgment import Judgment
from .judgment_document_relation import JudgmentDocumentRelation
from .base import Base
from .crawl_tracker import CrawlTracker
from .process_tracker import ProcessTracker
from .processed_articles import ProcessedArticle

__all__ = [
    "LegalDocument",
    "LegalQA",
    "Judgment",
    "JudgmentDocumentRelation",
    "CrawlTracker",
    "ProcessTracker",
    "ProcessedArticle",
]