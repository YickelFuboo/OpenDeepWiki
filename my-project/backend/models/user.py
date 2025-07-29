from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    avatar = Column(String(500))
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    # 关系
    user_roles = relationship("UserInRole", back_populates="user")
    warehouses = relationship("Warehouse", back_populates="creator")


class Role(Base, TimestampMixin):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # 关系
    user_roles = relationship("UserInRole", back_populates="role")
    warehouse_roles = relationship("WarehouseInRole", back_populates="role")


class UserInRole(Base, TimestampMixin):
    """用户角色关联模型"""
    __tablename__ = "user_in_roles"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=False)
    role_id = Column(String(50), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles") 