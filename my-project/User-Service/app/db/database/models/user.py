"""
用户相关数据模型
"""

from sqlalchemy import Column, String, Boolean, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional

from .base import Base, TimestampMixin

class User(Base, TimestampMixin):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)  # 允许为空，支持第三方登录
    phone = Column(String(20), unique=True, index=True, nullable=True)   # 手机号
    hashed_password = Column(String(255), nullable=True)  # 允许为空，支持第三方登录
    full_name = Column(String(100), nullable=True)
    avatar = Column(String(255), nullable=True)  # 头像文件ID
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # 第三方登录信息
    github_id = Column(String(100), unique=True, index=True, nullable=True)
    google_id = Column(String(100), unique=True, index=True, nullable=True)
    wechat_id = Column(String(100), unique=True, index=True, nullable=True)
    alipay_id = Column(String(100), unique=True, index=True, nullable=True)
    
    # 用户状态
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    registration_method = Column(String(20), default="email")  # email, phone, github, google, wechat, alipay
    
    # 关联关系
    user_roles = relationship("UserInRole", back_populates="user")
    files = relationship("FileMetadata", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

class Role(Base, TimestampMixin):
    """角色模型"""
    __tablename__ = "roles"
    
    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON格式的权限列表
    is_active = Column(Boolean, default=True)
    
    # 关联关系
    user_roles = relationship("UserInRole", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"

class UserInRole(Base, TimestampMixin):
    """用户角色关联模型"""
    __tablename__ = "user_roles"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False)
    
    # 关联关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserInRole(user_id={self.user_id}, role_id={self.role_id})>"

class OAuthProvider(Base, TimestampMixin):
    """OAuth提供商配置"""
    __tablename__ = "oauth_providers"
    
    id = Column(String(36), primary_key=True, index=True)
    provider = Column(String(20), unique=True, nullable=False)  # github, google, wechat, alipay
    client_id = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    redirect_uri = Column(String(255), nullable=False)
    auth_url = Column(String(255), nullable=False)
    token_url = Column(String(255), nullable=False)
    user_info_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<OAuthProvider(provider={self.provider})>" 