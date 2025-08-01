from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from src.core.database import Base


class Warehouse(Base):
    """知识仓库模型"""
    __tablename__ = "warehouses"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    type = Column(String, default="knowledge")
    
    # 仓库配置
    config = Column(Text, default="")  # JSON格式存储配置
    settings = Column(Text, default="")  # JSON格式存储设置
    
    # 状态信息
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    
    # 统计信息
    document_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="warehouses")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "config": self.config,
            "settings": self.settings,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "document_count": self.document_count,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 