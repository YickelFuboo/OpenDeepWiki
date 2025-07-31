"""
User-Service 数据库模块

包含数据库连接工厂和模型
"""

from .factory import init_database, get_db, close_db
from .models import Base, User, Role, UserInRole

__all__ = [
    "init_database",
    "get_db", 
    "close_db",
    "Base",
    "User",
    "Role", 
    "UserInRole"
] 