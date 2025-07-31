"""
文档管理模块

包含文档管理和目录功能
"""

from .services import DocumentService
from .catalog_service import DocumentCatalogService

__all__ = [
    "DocumentService",
    "DocumentCatalogService"
] 