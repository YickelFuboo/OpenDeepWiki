from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class CreateWarehouseDto(BaseModel):
    """创建知识仓库DTO"""
    name: str = Field(..., description="仓库名称")
    description: str = Field(default="", description="仓库描述")
    type: str = Field(default="knowledge", description="仓库类型")
    config: Optional[str] = Field(None, description="仓库配置")
    settings: Optional[str] = Field(None, description="仓库设置")
    is_public: bool = Field(default=False, description="是否公开")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("仓库名称不能为空")
        return v.strip()


class UpdateWarehouseDto(BaseModel):
    """更新知识仓库DTO"""
    name: Optional[str] = Field(None, description="仓库名称")
    description: Optional[str] = Field(None, description="仓库描述")
    type: Optional[str] = Field(None, description="仓库类型")
    config: Optional[str] = Field(None, description="仓库配置")
    settings: Optional[str] = Field(None, description="仓库设置")
    is_public: Optional[bool] = Field(None, description="是否公开")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError("仓库名称不能为空")
        return v.strip() if v else v


class WarehouseInfoDto(BaseModel):
    """知识仓库信息DTO"""
    id: str = Field(..., description="仓库ID")
    name: str = Field(..., description="仓库名称")
    description: str = Field(..., description="仓库描述")
    type: str = Field(..., description="仓库类型")
    config: Optional[str] = Field(None, description="仓库配置")
    settings: Optional[str] = Field(None, description="仓库设置")
    is_active: bool = Field(..., description="是否激活")
    is_public: bool = Field(..., description="是否公开")
    document_count: int = Field(..., description="文档数量")
    view_count: int = Field(..., description="查看次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True 