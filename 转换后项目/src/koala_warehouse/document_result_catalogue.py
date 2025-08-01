from typing import List, Optional
from datetime import datetime


class DocumentResultCatalogue:
    """文档结果目录模型"""
    
    def __init__(self):
        self.id: str = ""
        self.document_id: str = ""
        self.catalogue_content: str = ""
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None 