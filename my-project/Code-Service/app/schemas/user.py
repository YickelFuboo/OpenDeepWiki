from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from .common import TimestampMixin


class UserBase(BaseModel):
    """用户基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱")


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, description="密码")


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    password: Optional[str] = Field(None, min_length=6, description="密码")
    avatar: Optional[str] = Field(None, description="头像")


class UserResponse(UserBase, TimestampMixin):
    """用户响应模型"""
    id: str = Field(..., description="用户ID")
    avatar: Optional[str] = Field(None, description="头像")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
    is_active: bool = Field(..., description="是否激活")
    roles: List[str] = Field(default_factory=list, description="用户角色")


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应模型"""
    success: bool = Field(..., description="是否成功")
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    user: UserResponse = Field(..., description="用户信息")
    message: Optional[str] = Field(None, description="消息")


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型"""
    success: bool = Field(..., description="是否成功")
    access_token: str = Field(..., description="新的访问令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    message: Optional[str] = Field(None, description="消息") 