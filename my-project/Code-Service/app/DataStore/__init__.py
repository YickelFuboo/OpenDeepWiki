"""
数据存储适配层
支持关系数据库、RAG数据库、图数据库、S3存储等
"""

from .DB.factory import DatabaseFactory, init_database, get_database_session, close_database

__all__ = [
    'DatabaseFactory',
    'init_database', 
    'get_database_session',
    'close_database'
] 