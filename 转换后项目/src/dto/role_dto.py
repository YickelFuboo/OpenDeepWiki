from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CreateRoleDto(BaseModel):
    """角色创建DTO"""
    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: bool = Field(True, description="是否启用")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


class UpdateRoleDto(BaseModel):
    """角色更新DTO"""
    name: str = Field(..., min_length=2, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: bool = Field(True, description="是否启用")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("角色名称不能为空")
        return v.strip()


class RoleInfoDto(BaseModel):
    """角色信息DTO"""
    id: str = Field(..., description="角色ID")
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(True, description="是否启用")
    is_system_role: bool = Field(False, description="是否为系统角色")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user_count: int = Field(0, description="用户数量")
    warehouse_permission_count: int = Field(0, description="仓库权限数量")


class WarehousePermissionDto(BaseModel):
    """仓库权限DTO"""
    warehouse_id: str = Field(..., description="仓库ID")
    is_read_only: bool = Field(False, description="只读权限")
    is_write: bool = Field(False, description="写权限")
    is_delete: bool = Field(False, description="删除权限")


class RolePermissionDto(BaseModel):
    """角色权限DTO"""
    role_id: str = Field(..., description="角色ID")
    warehouse_permissions: List[WarehousePermissionDto] = Field(default_factory=list, description="仓库权限列表")


class WarehousePermissionTreeDto(BaseModel):
    """仓库权限树DTO"""
    id: str = Field(..., description="仓库ID")
    name: str = Field(..., description="仓库名称")
    type: str = Field(..., description="仓库类型")
    is_selected: bool = Field(False, description="是否选中")
    permission: Optional[WarehousePermissionDto] = Field(None, description="权限信息")
    children: List['WarehousePermissionTreeDto'] = Field(default_factory=list, description="子仓库")


class UserRoleDto(BaseModel):
    """用户角色DTO"""
    user_id: str = Field(..., description="用户ID")
    role_ids: List[str] = Field(default_factory=list, description="角色ID列表")


class WarehousePermissionDetailDto(WarehousePermissionDto):
    """仓库权限详情DTO"""
    organization_name: str = Field(..., description="组织名称")
    warehouse_name: str = Field(..., description="仓库名称")
    warehouse_description: str = Field(..., description="仓库描述")


class RoleDetailDto(RoleInfoDto):
    """角色详情DTO"""
    users: List['UserInfoDto'] = Field(default_factory=list, description="用户列表")
    warehouse_permissions: List[WarehousePermissionDetailDto] = Field(default_factory=list, description="仓库权限列表")


# 导入UserInfoDto以避免循环导入
from src.dto.user_dto import UserInfoDto 