from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from schemas.common import TimestampMixin

class RoleBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: bool = Field(True, description="是否启用")

class RoleCreate(RoleBase):
    """创建角色请求模型"""
    pass

class RoleUpdate(BaseModel):
    """更新角色请求模型"""
    name: Optional[str] = Field(None, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否启用")

class RoleResponse(RoleBase, TimestampMixin):
    """角色响应模型"""
    id: str = Field(..., description="角色ID")
    is_system_role: bool = Field(False, description="是否为系统角色")
    user_count: int = Field(0, description="用户数量")
    warehouse_permission_count: int = Field(0, description="仓库权限数量")

    class Config:
        from_attributes = True

class RoleDetailResponse(RoleResponse):
    """角色详情响应模型"""
    users: List[Dict[str, Any]] = Field(..., description="用户列表")
    warehouse_permissions: List[Dict[str, Any]] = Field(..., description="仓库权限列表")

class UserRoleAssign(BaseModel):
    """用户角色分配模型"""
    user_id: str = Field(..., description="用户ID")
    role_ids: List[str] = Field(..., description="角色ID列表")

class WarehousePermission(BaseModel):
    """仓库权限模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    is_read_only: bool = Field(True, description="是否只读权限")
    is_write: bool = Field(False, description="是否有写入权限")
    is_delete: bool = Field(False, description="是否有删除权限")

class RolePermission(BaseModel):
    """角色权限模型"""
    role_id: str = Field(..., description="角色ID")
    warehouse_permissions: List[WarehousePermission] = Field(..., description="仓库权限列表")

class WarehousePermissionTree(BaseModel):
    """仓库权限树模型"""
    key: str = Field(..., description="节点键")
    title: str = Field(..., description="节点标题")
    children: Optional[List['WarehousePermissionTree']] = Field(None, description="子节点")
    permission: Optional[WarehousePermission] = Field(None, description="权限信息")
    type: str = Field(..., description="节点类型")

class WarehousePermissionDetail(BaseModel):
    """仓库权限详情模型"""
    warehouse_id: str = Field(..., description="仓库ID")
    organization_name: str = Field(..., description="组织名称")
    warehouse_name: str = Field(..., description="仓库名称")
    warehouse_description: Optional[str] = Field(None, description="仓库描述")
    is_read_only: bool = Field(True, description="是否只读权限")
    is_write: bool = Field(False, description="是否有写入权限")
    is_delete: bool = Field(False, description="是否有删除权限")

class UserInfo(BaseModel):
    """用户信息模型"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    role: Optional[str] = Field(None, description="角色")

class MenuItem(BaseModel):
    """菜单项模型"""
    id: str = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    path: str = Field(..., description="菜单路径")
    icon: Optional[str] = Field(None, description="图标")
    order: int = Field(0, description="排序")
    required_roles: List[str] = Field(..., description="所需角色")
    children: Optional[List['MenuItem']] = Field(None, description="子菜单")

class UserMenu(BaseModel):
    """用户菜单模型"""
    user: UserInfo = Field(..., description="用户信息")
    menus: List[MenuItem] = Field(..., description="菜单列表")

# 解决循环引用
WarehousePermissionTree.model_rebuild()
MenuItem.model_rebuild() 