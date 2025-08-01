from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator


class LoginDto(BaseModel):
    """登录DTO"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=1, description="密码")
    
    @validator('password')
    def validate_password(cls, v):
        if not v.strip():
            raise ValueError("密码不能为空")
        return v


class RegisterDto(BaseModel):
    """注册DTO"""
    name: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()
    
    @validator('password')
    def validate_password(cls, v):
        if not v.strip():
            raise ValueError("密码不能为空")
        return v
    
    @validator('confirm_password')
    def validate_confirm_password(cls, v, values):
        if not v.strip():
            raise ValueError("确认密码不能为空")
        if 'password' in values and v != values['password']:
            raise ValueError("两次输入的密码不一致")
        return v


class TokenDto(BaseModel):
    """令牌DTO"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class RefreshTokenDto(BaseModel):
    """刷新令牌DTO"""
    refresh_token: str = Field(..., description="刷新令牌") 