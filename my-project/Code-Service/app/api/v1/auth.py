from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session


from app.auth.services import AuthService
from app.db.connection import get_db
from app.db.models.user import User
from app.schemas.common import BaseResponse, ErrorResponse
from app.schemas.user import LoginRequest, LoginResponse, UserCreate, RefreshTokenRequest, RefreshTokenResponse
from app.utils.auth import get_current_user


router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        result = auth_service.login(login_data.username, login_data.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/register", response_model=BaseResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        auth_service = AuthService(db)
        user = auth_service.register(user_data)
        return BaseResponse(
            success=True,
            message="注册成功",
            data={"user_id": user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        auth_service = AuthService(db)
        result = auth_service.refresh_token(refresh_data.refresh_token)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刷新令牌失败: {str(e)}"
        )


@router.post("/logout", response_model=BaseResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    try:
        auth_service = AuthService(db)
        auth_service.logout(current_user.id)
        return BaseResponse(
            success=True,
            message="登出成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登出失败: {str(e)}"
        )


@router.get("/me", response_model=BaseResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    try:
        return BaseResponse(
            success=True,
            message="获取用户信息成功",
            data={
                "id": current_user.id,
                "username": current_user.username,
                "email": current_user.email,
                "is_active": current_user.is_active
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        ) 