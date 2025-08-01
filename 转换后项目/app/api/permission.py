from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_admin
from src.dto.role_dto import (
    WarehousePermissionTreeDto, WarehousePermissionDto,
    WarehousePermissionDetailDto, UserRoleDto, RolePermissionDto
)
from src.services.permission_service import PermissionService
from src.models.user import User

permission_router = APIRouter()


@permission_router.get("/warehouse/tree", response_model=List[WarehousePermissionTreeDto])
@require_admin()
async def get_warehouse_permission_tree(
    role_id: Optional[str] = Query(None, description="角色ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库权限树形结构"""
    permission_service = PermissionService(db)
    
    try:
        tree = await permission_service.get_warehouse_permission_tree(role_id)
        return tree
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取仓库权限树失败: {str(e)}"
        )


@permission_router.post("/role/set")
@require_admin()
async def set_role_permissions(
    role_permission_data: RolePermissionDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """设置角色权限"""
    permission_service = PermissionService(db)
    
    try:
        success = await permission_service.set_role_permissions(role_permission_data)
        if success:
            return {"message": "设置角色权限成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设置角色权限失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置角色权限失败: {str(e)}"
        )


@permission_router.get("/role/{role_id}/warehouses", response_model=List[WarehousePermissionDetailDto])
@require_admin()
async def get_role_warehouse_permissions(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取角色的仓库权限列表"""
    permission_service = PermissionService(db)
    
    try:
        permissions = await permission_service.get_role_warehouse_permissions(role_id)
        return permissions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色仓库权限失败: {str(e)}"
        )


@permission_router.post("/user/assign")
@require_admin()
async def assign_user_roles(
    user_role_data: UserRoleDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分配用户角色"""
    permission_service = PermissionService(db)
    
    try:
        success = await permission_service.assign_user_roles(user_role_data)
        if success:
            return {"message": "分配用户角色成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分配用户角色失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配用户角色失败: {str(e)}"
        )


@permission_router.get("/user/{user_id}/roles", response_model=List[RoleInfoDto])
@require_admin()
async def get_user_roles(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的角色列表"""
    permission_service = PermissionService(db)
    
    try:
        roles = await permission_service.get_user_roles(user_id)
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户角色失败: {str(e)}"
        )


@permission_router.get("/user/{user_id}/warehouse/{warehouse_id}/check", response_model=Optional[WarehousePermissionDto])
async def check_user_warehouse_permission(
    user_id: str,
    warehouse_id: str,
    db: AsyncSession = Depends(get_db)
):
    """检查用户对仓库的权限（公开接口）"""
    permission_service = PermissionService(db)
    
    try:
        permission = await permission_service.check_user_warehouse_permission(user_id, warehouse_id)
        return permission
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查用户仓库权限失败: {str(e)}"
        )


@permission_router.get("/user/{user_id}/warehouses", response_model=List[WarehousePermissionDetailDto])
async def get_user_accessible_warehouses(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取用户可访问的仓库列表（公开接口）"""
    permission_service = PermissionService(db)
    
    try:
        warehouses = await permission_service.get_user_accessible_warehouses(user_id)
        return warehouses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户可访问仓库失败: {str(e)}"
        )


@permission_router.post("/organization/{role_id}/{organization_name}/set")
@require_admin()
async def set_organization_permissions(
    role_id: str,
    organization_name: str,
    permission: WarehousePermissionDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """批量设置组织权限"""
    permission_service = PermissionService(db)
    
    try:
        success = await permission_service.set_organization_permissions(role_id, organization_name, permission)
        if success:
            return {"message": "设置组织权限成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="设置组织权限失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"设置组织权限失败: {str(e)}"
        ) 