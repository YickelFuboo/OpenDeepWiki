from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
import enum
from .base import Base, TimestampMixin


class WarehouseStatus(enum.Enum):
    """仓库状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class WarehouseType(enum.Enum):
    """仓库类型枚举"""
    GIT = "git"
    ZIP = "zip"
    FILE = "file"


class Warehouse(Base, TimestampMixin):
    """仓库模型"""
    __tablename__ = "warehouses"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    organization_name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    type = Column(Enum(WarehouseType), default=WarehouseType.GIT)
    status = Column(Enum(WarehouseStatus), default=WarehouseStatus.PENDING)
    branch = Column(String(100), default="main")
    version = Column(String(100))
    git_user_name = Column(String(100))
    git_password = Column(String(255))
    optimized_directory_structure = Column(Text)
    creator_id = Column(String(50))
    
    # 关系
    creator = relationship("User", back_populates="warehouses")
    warehouse_roles = relationship("WarehouseInRole", back_populates="warehouse")
    documents = relationship("Document", back_populates="warehouse")


class WarehouseInRole(Base, TimestampMixin):
    """仓库角色关联模型"""
    __tablename__ = "warehouse_in_roles"
    
    id = Column(String(50), primary_key=True)
    warehouse_id = Column(String(50), nullable=False)
    role_id = Column(String(50), nullable=False)
    
    # 关系
    warehouse = relationship("Warehouse", back_populates="warehouse_roles")
    role = relationship("Role", back_populates="warehouse_roles") 