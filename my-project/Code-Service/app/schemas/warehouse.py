from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

from schemas.common import TimestampMixin

class WarehouseStatus(str, Enum):
    """仓库状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class WarehouseType(str, Enum):
    """仓库类型枚举"""
    GIT = "git"
    FILE = "file"

class WarehouseBase(BaseModel):
    """仓库基础模型"""
    name: str = Field(..., description="仓库名称")
    organization_name: str = Field(..., description="组织名称")
    address: str = Field(..., description="仓库地址")
    description: Optional[str] = Field(None, description="仓库描述")
    type: WarehouseType = Field(WarehouseType.GIT, description="仓库类型")
    branch: Optional[str] = Field("main", description="分支名称")
    git_user_name: Optional[str] = Field(None, description="Git用户名")
    git_password: Optional[str] = Field(None, description="Git密码")
    email: Optional[str] = Field(None, description="邮箱")

class WarehouseCreate(WarehouseBase):
    """创建仓库请求模型"""
    pass

class WarehouseUpdate(BaseModel):
    """更新仓库请求模型"""
    name: Optional[str] = Field(None, description="仓库名称")
    organization_name: Optional[str] = Field(None, description="组织名称")
    address: Optional[str] = Field(None, description="仓库地址")
    description: Optional[str] = Field(None, description="仓库描述")
    type: Optional[WarehouseType] = Field(None, description="仓库类型")
    branch: Optional[str] = Field(None, description="分支名称")
    git_user_name: Optional[str] = Field(None, description="Git用户名")
    git_password: Optional[str] = Field(None, description="Git密码")
    email: Optional[str] = Field(None, description="邮箱")

class WarehouseResponse(WarehouseBase, TimestampMixin):
    """仓库响应模型"""
    id: str = Field(..., description="仓库ID")
    status: WarehouseStatus = Field(..., description="仓库状态")
    version: Optional[str] = Field(None, description="版本")
    error: Optional[str] = Field(None, description="错误信息")
    prompt: Optional[str] = Field(None, description="提示词")
    is_embedded: bool = Field(False, description="是否嵌入完成")
    is_recommended: bool = Field(False, description="是否推荐")
    optimized_directory_structure: Optional[str] = Field(None, description="优化过的目录结构")
    creator_id: Optional[str] = Field(None, description="创建者ID")

    class Config:
        from_attributes = True

class CreateRepositoryDto(BaseModel):
    """创建仓库DTO"""
    organization: str = Field(..., description="组织名称")
    repository_name: str = Field(..., description="仓库名称")
    address: str = Field(..., description="仓库地址")
    branch: Optional[str] = Field("main", description="分支名称")
    git_user_name: Optional[str] = Field(None, description="Git用户名")
    git_password: Optional[str] = Field(None, description="Git密码")
    email: Optional[str] = Field(None, description="邮箱")

class UpdateRepositoryDto(BaseModel):
    """更新仓库DTO"""
    description: Optional[str] = Field(None, description="仓库描述")
    is_recommended: Optional[bool] = Field(None, description="是否推荐")
    prompt: Optional[str] = Field(None, description="提示词")

class RepositoryInfoDto(BaseModel):
    """仓库信息DTO"""
    id: str = Field(..., description="仓库ID")
    name: str = Field(..., description="仓库名称")
    organization_name: str = Field(..., description="组织名称")
    address: str = Field(..., description="仓库地址")
    description: Optional[str] = Field(None, description="仓库描述")
    status: str = Field(..., description="仓库状态")
    type: str = Field(..., description="仓库类型")
    branch: Optional[str] = Field(None, description="分支名称")
    version: Optional[str] = Field(None, description="版本")
    is_recommended: bool = Field(False, description="是否推荐")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

class WarehouseInRoleBase(BaseModel):
    """仓库角色关系基础模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    role_id: str = Field(..., description="角色ID")
    is_read: bool = Field(True, description="是否有读取权限")
    is_write: bool = Field(False, description="是否有写入权限")
    is_delete: bool = Field(False, description="是否有删除权限")

class WarehouseInRoleCreate(WarehouseInRoleBase):
    """创建仓库角色关系请求模型"""
    pass

class WarehouseInRoleUpdate(BaseModel):
    """更新仓库角色关系请求模型"""
    is_read: Optional[bool] = Field(None, description="是否有读取权限")
    is_write: Optional[bool] = Field(None, description="是否有写入权限")
    is_delete: Optional[bool] = Field(None, description="是否有删除权限")

class WarehouseInRoleResponse(WarehouseInRoleBase, TimestampMixin):
    """仓库角色关系响应模型"""
    id: str = Field(..., description="关系ID")

    class Config:
        from_attributes = True 