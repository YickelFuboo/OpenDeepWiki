from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from src.models.base import BaseEntity


class Role(BaseEntity):
    """角色模型"""
    __tablename__ = "roles"

    name = Column(String(50), nullable=False, unique=True, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system_role = Column(Boolean, default=False, comment="是否为系统角色")

    # 关系
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    warehouse_roles = relationship("WarehouseRole", back_populates="role", cascade="all, delete-orphan")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class UserRole(BaseEntity):
    """用户角色关联模型"""
    __tablename__ = "user_roles"

    user_id = Column(String(36), nullable=False, comment="用户ID")
    role_id = Column(String(36), nullable=False, comment="角色ID")

    # 关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class WarehouseRole(BaseEntity):
    """仓库角色关联模型"""
    __tablename__ = "warehouse_roles"

    warehouse_id = Column(String(36), nullable=False, comment="仓库ID")
    role_id = Column(String(36), nullable=False, comment="角色ID")
    is_read_only = Column(Boolean, default=False, comment="只读权限")
    is_write = Column(Boolean, default=False, comment="写权限")
    is_delete = Column(Boolean, default=False, comment="删除权限")

    # 关系
    warehouse = relationship("Warehouse", back_populates="warehouse_roles")
    role = relationship("Role", back_populates="warehouse_roles")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "warehouse_id": self.warehouse_id,
            "role_id": self.role_id,
            "is_read_only": self.is_read_only,
            "is_write": self.is_write,
            "is_delete": self.is_delete,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 