from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re


class CreateUserDto(BaseModel):
    """用户创建DTO"""
    name: str = Field(..., min_length=1, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, description="密码")
    role: str = Field(default="user", description="角色")
    avatar: Optional[str] = Field(None, description="头像")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()


class UpdateUserDto(BaseModel):
    """用户更新DTO"""
    name: str = Field(..., min_length=1, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: Optional[str] = Field(None, min_length=6, description="密码")
    role: str = Field(default="user", description="角色")
    avatar: Optional[str] = Field(None, description="头像")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()


class UserInfoDto(BaseModel):
    """用户信息DTO（返回给前端）"""
    id: str = Field(..., description="用户ID")
    name: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    role: str = Field(..., description="角色")
    avatar: Optional[str] = Field(None, description="头像")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    last_login_ip: Optional[str] = Field(None, description="最后登录IP")
    
    class Config:
        from_attributes = True


class UpdateProfileDto(BaseModel):
    """更新用户资料DTO"""
    name: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    avatar: Optional[str] = Field(None, description="头像")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("用户名不能为空")
        return v.strip()


class VerifyPasswordDto(BaseModel):
    """验证密码DTO"""
    password: str = Field(..., min_length=1, description="密码")
    
    @validator('password')
    def validate_password(cls, v):
        if not v.strip():
            raise ValueError("密码不能为空")
        return v


class ChangePasswordDto(BaseModel):
    """修改密码DTO"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    
    @validator('current_password')
    def validate_current_password(cls, v):
        if not v.strip():
            raise ValueError("当前密码不能为空")
        return v
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not v.strip():
            raise ValueError("新密码不能为空")
        
        # 检查密码复杂度
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$', v):
            raise ValueError("新密码必须包含大小写字母和数字，长度至少8位")
        
        return v 