from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY

from src.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    avatar = Column(String, default="")
    roles = Column(ARRAY(String), default=["user"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)
    
    # 关系
    repositories = relationship("Repository", back_populates="user")
    documents = relationship("Document", back_populates="user")
    warehouses = relationship("Warehouse", back_populates="user")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.roles:
            self.roles = ["user"]
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "email": self.email,
            "avatar": self.avatar,
            "roles": self.roles,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
        }
    
    def has_role(self, role: str) -> bool:
        """检查用户是否有指定角色"""
        return role in self.roles
    
    def is_admin(self) -> bool:
        """检查用户是否是管理员"""
        return "admin" in self.roles 