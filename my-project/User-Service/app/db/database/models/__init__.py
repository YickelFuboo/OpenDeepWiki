"""
User-Service 数据库模型模块
"""

from .user import User, UserInRole, Role
from .base import Base, TimestampMixin

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserInRole",
    "Role"
] 