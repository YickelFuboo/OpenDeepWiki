"""
用户相关的Pydantic模型
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    """用户基础模型"""
    username: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    """用户创建模型"""
    password: Optional[str] = None  # 第三方登录时可以为空
    registration_method: str = "email"  # email, phone, github, google, wechat, alipay

class UserUpdate(BaseModel):
    """用户更新模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """用户响应模型"""
    id: str
    email_verified: bool = False
    phone_verified: bool = False
    registration_method: str = "email"
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """用户登录模型"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    login_method: str = "password"  # password, github, google, wechat, alipay

class UserPasswordChange(BaseModel):
    """用户密码修改模型"""
    current_password: str
    new_password: str

class OAuthLogin(BaseModel):
    """OAuth登录模型"""
    provider: str  # github, google, wechat, alipay, oidc
    code: str
    state: Optional[str] = None

class OAuthBind(BaseModel):
    """OAuth绑定模型"""
    provider: str
    access_token: str
    user_id: str

class OIDCLogin(BaseModel):
    """OIDC登录模型"""
    issuer: str
    code: str
    state: Optional[str] = None
    id_token: Optional[str] = None

class OAuthProviderInfo(BaseModel):
    """OAuth提供商信息"""
    provider: str
    display_name: str
    icon: str
    auth_url: str
    is_active: bool

class UserList(BaseModel):
    """用户列表模型"""
    users: List[UserResponse]
    total: int
    page: int
    size: int 