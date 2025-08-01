from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.models.base import Base


class DocumentOverview(Base):
    """文档概述模型"""
    __tablename__ = "document_overviews"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # 绑定的文档ID
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    
    # 内容
    content = Column(Text, nullable=False, default="")
    
    # 标题
    title = Column(String(200), nullable=False, default="")
    
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 更新时间
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    document = relationship("Document", back_populates="overview") 