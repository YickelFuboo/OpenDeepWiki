from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum

from src.core.database import Base


class WarehouseStatus(Enum):
    """仓库状态枚举"""
    PENDING = 0      # 待处理
    PROCESSING = 1   # 处理中
    COMPLETED = 2    # 已完成
    CANCELED = 3     # 已取消
    UNAUTHORIZED = 4 # 未授权
    FAILED = 99      # 已失败


class Repository(Base):
    """仓库模型"""
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 基本信息
    organization_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    address = Column(String, nullable=False)
    
    # Git配置
    git_username = Column(String, nullable=True)
    git_password = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # 仓库信息
    type = Column(String, default="git")
    branch = Column(String, default="main")
    status = Column(Integer, default=WarehouseStatus.PENDING.value)
    error = Column(Text, nullable=True)
    
    # 构建信息
    prompt = Column(Text, nullable=True)
    version = Column(String, nullable=True)
    is_embedded = Column(Boolean, default=False)
    is_recommended = Column(Boolean, default=False)
    
    # 优化信息
    optimized_directory_structure = Column(Text, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="repositories")
    documents = relationship("Document", back_populates="repository")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status is None:
            self.status = WarehouseStatus.PENDING.value
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "organization_name": self.organization_name,
            "name": self.name,
            "description": self.description,
            "address": self.address,
            "git_username": self.git_username,
            "email": self.email,
            "type": self.type,
            "branch": self.branch,
            "status": self.status,
            "error": self.error,
            "prompt": self.prompt,
            "version": self.version,
            "is_embedded": self.is_embedded,
            "is_recommended": self.is_recommended,
            "optimized_directory_structure": self.optimized_directory_structure,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_status_name(self) -> str:
        """获取状态名称"""
        status_map = {
            WarehouseStatus.PENDING.value: "待处理",
            WarehouseStatus.PROCESSING.value: "处理中",
            WarehouseStatus.COMPLETED.value: "已完成",
            WarehouseStatus.CANCELED.value: "已取消",
            WarehouseStatus.UNAUTHORIZED.value: "未授权",
            WarehouseStatus.FAILED.value: "已失败",
        }
        return status_map.get(self.status, "未知状态") 