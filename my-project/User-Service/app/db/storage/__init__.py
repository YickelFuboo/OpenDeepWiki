"""
存储模块 - 提供通用文件存储能力
"""

from .base import StorageInterface
from .factory import get_storage

__all__ = ["StorageInterface", "get_storage"] 