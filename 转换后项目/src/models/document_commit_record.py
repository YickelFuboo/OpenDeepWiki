from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.models.base import Base


class DocumentCommitRecord(Base):
    """文档提交记录模型"""
    __tablename__ = "document_commit_records"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # 仓库ID
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    
    # 提交ID
    commit_id = Column(String(100), nullable=False, default="")
    
    # 提交消息
    commit_message = Column(String(1000), nullable=False, default="")
    
    # 标题
    title = Column(String(200), nullable=False, default="")
    
    # 作者
    author = Column(String(100), nullable=False, default="")
    
    # 最后更新时间
    last_update = Column(DateTime, nullable=False, default=func.now())
    
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 更新时间
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    warehouse = relationship("Warehouse", back_populates="commit_records") 