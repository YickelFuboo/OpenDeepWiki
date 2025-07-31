from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.connection import get_db
from services.role_service import RoleService
from schemas.common import BaseResponse, PaginationParams, PaginatedResponse
from utils.auth import get_current_active_user
from models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def get_roles(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取角色列表"""
    try:
        role_service = RoleService(db)
        result = role_service.get_roles(pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
        )


@router.get("/{role_id}", response_model=BaseResponse)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取角色详情"""
    try:
        role_service = RoleService(db)
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return BaseResponse(
            success=True,
            message="获取角色详情成功",
            data=role
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}"
        )


@router.post("/", response_model=BaseResponse)
async def create_role(
    role_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建角色"""
    try:
        role_service = RoleService(db)
        role = role_service.create_role(role_data)
        return BaseResponse(
            success=True,
            message="创建角色成功",
            data={"role_id": role.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建角色失败: {str(e)}"
        )


@router.put("/{role_id}", response_model=BaseResponse)
async def update_role(
    role_id: str,
    role_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新角色"""
    try:
        role_service = RoleService(db)
        role = role_service.update_role(role_id, role_data)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return BaseResponse(
            success=True,
            message="更新角色成功",
            data={"role_id": role.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新角色失败: {str(e)}"
        )


@router.delete("/{role_id}", response_model=BaseResponse)
async def delete_role(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除角色"""
    try:
        role_service = RoleService(db)
        success = role_service.delete_role(role_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        return BaseResponse(
            success=True,
            message="删除角色成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除角色失败: {str(e)}"
        )


@router.get("/{role_id}/users", response_model=BaseResponse)
async def get_role_users(
    role_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取角色的用户列表"""
    try:
        role_service = RoleService(db)
        users = role_service.get_role_users(role_id)
        return BaseResponse(
            success=True,
            message="获取角色用户列表成功",
            data={"users": users}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色用户列表失败: {str(e)}"
        )


@router.post("/{role_id}/users", response_model=BaseResponse)
async def add_users_to_role(
    role_id: str,
    user_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """为角色添加用户"""
    try:
        role_service = RoleService(db)
        success = role_service.add_users_to_role(role_id, user_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="添加用户到角色失败"
            )
        return BaseResponse(
            success=True,
            message="添加用户到角色成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加用户到角色失败: {str(e)}"
        )


@router.delete("/{role_id}/users", response_model=BaseResponse)
async def remove_users_from_role(
    role_id: str,
    user_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """从角色移除用户"""
    try:
        role_service = RoleService(db)
        success = role_service.remove_users_from_role(role_id, user_ids)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="从角色移除用户失败"
            )
        return BaseResponse(
            success=True,
            message="从角色移除用户成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从角色移除用户失败: {str(e)}"
        ) 