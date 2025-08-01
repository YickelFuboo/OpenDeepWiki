from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_admin
from src.dto.role_dto import (
    CreateRoleDto, UpdateRoleDto, RoleInfoDto, RoleDetailDto,
    UserRoleDto, RolePermissionDto
)
from src.services.role_service import RoleService
from src.models.user import User

role_router = APIRouter()


@role_router.get("/list", response_model=dict)
@require_admin()
async def get_role_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取角色列表"""
    role_service = RoleService(db)
    
    try:
        result = await role_service.get_role_list(
            page=page,
            page_size=page_size,
            keyword=keyword,
            is_active=is_active
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )


@role_router.get("/{role_id}", response_model=RoleDetailDto)
@require_admin()
async def get_role_detail(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取角色详情"""
    role_service = RoleService(db)
    
    try:
        role_detail = await role_service.get_role_detail(role_id)
        if not role_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}"
        )


@role_router.post("/", response_model=RoleInfoDto)
@require_admin()
async def create_role(
    role_data: CreateRoleDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建角色"""
    role_service = RoleService(db)
    
    try:
        role_info = await role_service.create_role(role_data)
        return role_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )


@role_router.put("/{role_id}", response_model=RoleInfoDto)
@require_admin()
async def update_role(
    role_id: str,
    role_data: UpdateRoleDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新角色"""
    role_service = RoleService(db)
    
    try:
        role_info = await role_service.update_role(role_id, role_data)
        if not role_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return role_info
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失败: {str(e)}"
        )


@role_router.delete("/{role_id}")
@require_admin()
async def delete_role(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除角色"""
    role_service = RoleService(db)
    
    try:
        success = await role_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除角色失败: {str(e)}"
        )


@role_router.get("/all/list", response_model=List[RoleInfoDto])
async def get_all_roles(
    db: AsyncSession = Depends(get_db)
):
    """获取所有角色（公开接口）"""
    role_service = RoleService(db)
    
    try:
        roles = await role_service.get_all_roles()
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取所有角色失败: {str(e)}"
        )


@role_router.post("/batch/status")
@require_admin()
async def batch_update_role_status(
    role_ids: List[str],
    is_active: bool,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """批量更新角色状态"""
    role_service = RoleService(db)
    
    try:
        success = await role_service.batch_update_role_status(role_ids, is_active)
        if success:
            return {"message": "批量更新成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="批量更新失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新角色状态失败: {str(e)}"
        )


@role_router.post("/user/assign")
@require_admin()
async def assign_user_roles(
    user_role_data: UserRoleDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分配用户角色"""
    role_service = RoleService(db)
    
    try:
        success = await role_service.assign_user_roles(user_role_data)
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


@role_router.post("/permission/assign")
@require_admin()
async def assign_role_permissions(
    role_permission_data: RolePermissionDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """分配角色权限"""
    role_service = RoleService(db)
    
    try:
        success = await role_service.assign_role_permissions(role_permission_data)
        if success:
            return {"message": "分配角色权限成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分配角色权限失败"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配角色权限失败: {str(e)}"
        ) 