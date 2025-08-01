from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from src.models.base import Base


# 用户角色关联表
user_in_role = Table(
    "user_in_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id"), primary_key=True)
)


class UserInRole(Base):
    """用户角色关联模型"""
    __tablename__ = "user_in_roles"
    
    # 复合主键
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("roles.id"), primary_key=True)
    
    # 关联关系
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users") 