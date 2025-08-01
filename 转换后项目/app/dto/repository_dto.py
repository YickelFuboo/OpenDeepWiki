from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CreateRepositoryDto(BaseModel):
    """创建仓库DTO"""
    organization_name: str = Field(..., description="组织名称")
    name: str = Field(..., description="仓库名称")
    description: str = Field(default="", description="仓库描述")
    address: str = Field(..., description="仓库地址")
    git_username: Optional[str] = Field(None, description="Git用户名")
    git_password: Optional[str] = Field(None, description="Git密码")
    email: Optional[str] = Field(None, description="邮箱")
    type: str = Field(default="git", description="仓库类型")
    branch: str = Field(default="main", description="分支")
    prompt: Optional[str] = Field(None, description="构建提示词")
    
    @validator('organization_name', 'name', 'address')
    def validate_required_fields(cls, v):
        if not v.strip():
            raise ValueError("必填字段不能为空")
        return v.strip()


class UpdateRepositoryDto(BaseModel):
    """更新仓库DTO"""
    description: Optional[str] = Field(None, description="仓库描述")
    is_recommended: Optional[bool] = Field(None, description="是否推荐")
    prompt: Optional[str] = Field(None, description="构建提示词")


class RepositoryInfoDto(BaseModel):
    """仓库信息DTO"""
    id: str = Field(..., description="仓库ID")
    organization_name: str = Field(..., description="组织名称")
    name: str = Field(..., description="仓库名称")
    description: str = Field(..., description="仓库描述")
    address: str = Field(..., description="仓库地址")
    type: Optional[str] = Field(None, description="仓库类型")
    branch: Optional[str] = Field(None, description="分支")
    status: int = Field(..., description="仓库状态")
    error: Optional[str] = Field(None, description="错误信息")
    prompt: Optional[str] = Field(None, description="构建提示词")
    version: Optional[str] = Field(None, description="仓库版本")
    is_embedded: bool = Field(..., description="是否嵌入完成")
    is_recommended: bool = Field(..., description="是否推荐")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True 