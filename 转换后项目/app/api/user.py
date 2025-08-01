from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_admin, require_user
from src.dto.user_dto import (
    CreateUserDto, UpdateUserDto, UserInfoDto, 
    UpdateProfileDto, VerifyPasswordDto, ChangePasswordDto
)
from src.services.user_service import UserService
from src.models.user import User

user_router = APIRouter()


@user_router.get("/list", response_model=List[UserInfoDto])
@require_admin()
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表（管理员）"""
    user_service = UserService(db)
    users, total = await user_service.get_user_list(page, page_size, keyword)
    
    return [user_service.user_to_dto(user) for user in users]


@user_router.get("/current", response_model=UserInfoDto)
@require_user()
async def get_current_user(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    user_service = UserService(db)
    return user_service.user_to_dto(current_user)


@user_router.put("/profile", response_model=UserInfoDto)
@require_user()
async def update_profile(
    update_profile_dto: UpdateProfileDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户资料"""
    user_service = UserService(db)
    
    try:
        user = await user_service.update_profile(current_user.id, update_profile_dto)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user_service.user_to_dto(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.post("/verify-password")
@require_user()
async def verify_password(
    verify_password_dto: VerifyPasswordDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """验证当前密码"""
    user_service = UserService(db)
    
    is_valid = await user_service.verify_password(current_user.id, verify_password_dto)
    return {"is_valid": is_valid}


@user_router.post("/change-password")
@require_user()
async def change_password(
    change_password_dto: ChangePasswordDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    user_service = UserService(db)
    
    try:
        success = await user_service.change_password(current_user.id, change_password_dto)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.post("/create", response_model=UserInfoDto)
@require_admin()
async def create_user(
    create_user_dto: CreateUserDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建用户（管理员）"""
    user_service = UserService(db)
    
    try:
        user = await user_service.create_user(create_user_dto)
        return user_service.user_to_dto(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.put("/{user_id}", response_model=UserInfoDto)
@require_admin()
async def update_user(
    user_id: str,
    update_user_dto: UpdateUserDto,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新用户（管理员）"""
    user_service = UserService(db)
    
    try:
        user = await user_service.update_user(user_id, update_user_dto)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user_service.user_to_dto(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@user_router.delete("/{user_id}")
@require_admin()
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除用户（管理员）"""
    user_service = UserService(db)
    
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
 