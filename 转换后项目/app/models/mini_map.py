from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from src.models.base import Base


class MiniMap(Base):
    """迷你地图模型"""
    __tablename__ = "mini_maps"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # 仓库ID
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), nullable=False)
    
    # 思维导图数据（JSON格式）
    value = Column(Text, nullable=False, default="")
    
    # 创建时间
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # 更新时间
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # 关联关系
    warehouse = relationship("Warehouse", back_populates="mini_maps") 