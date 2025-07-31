"""
数据库相关操作
包含数据库结构定义和不同数据库的连接
"""

from .factory import DatabaseFactory, init_database, get_database_session, close_database
from .connection import get_db

__all__ = [
    'DatabaseFactory',
    'init_database',
    'get_database_session', 
    'close_database',
    'get_db'
] 