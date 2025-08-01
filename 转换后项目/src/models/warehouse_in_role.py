from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base


class WarehouseInRole(Base):
    """仓库角色关联模型"""
    __tablename__ = "warehouse_in_roles"
    
    # 复合主键
    warehouse_id = Column(String(36), ForeignKey("warehouses.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    
    # 权限设置
    is_read_only = Column(Boolean, nullable=False, default=False)
    is_write = Column(Boolean, nullable=False, default=False)
    is_delete = Column(Boolean, nullable=False, default=False)
    
    # 关联关系
    warehouse = relationship("Warehouse", back_populates="roles")
    role = relationship("Role", back_populates="warehouses") 