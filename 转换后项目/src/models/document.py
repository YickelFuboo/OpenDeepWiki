from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

from src.core.database import Base


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=True)
    
    # 基本信息
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    file_path = Column(String, nullable=True)
    file_size = Column(String, nullable=True)
    
    # 文档信息
    document_type = Column(String, default="markdown")
    language = Column(String, default="zh-CN")
    tags = Column(Text, default="")  # JSON格式存储标签
    
    # 状态信息
    is_public = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    view_count = Column(String, default="0")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="documents")
    repository = relationship("Repository", back_populates="documents")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "repository_id": self.repository_id,
            "title": self.title,
            "content": self.content,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "document_type": self.document_type,
            "language": self.language,
            "tags": self.tags,
            "is_public": self.is_public,
            "is_featured": self.is_featured,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        } 