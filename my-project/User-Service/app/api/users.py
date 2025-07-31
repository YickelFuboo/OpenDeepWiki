from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from db.database.factory import get_db
from service.user_mgmt.user_service import UserService
from api.schemes.user import UserCreate, UserUpdate, UserResponse, ChangePasswordRequest
from api.schemes.common import PaginationParams, PaginatedResponse, BaseResponse
from service.user_mgmt.auth_service import get_current_active_user
from db.database.models.user import User

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def get_users(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    try:
        user_service = UserService(db)
        result = user_service.get_users(pagination)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.get("/{user_id}", response_model=BaseResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户详情"""
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return BaseResponse(
            success=True,
            message="获取用户详情成功",
            data=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户详情失败: {str(e)}"
        )


@router.post("/", response_model=BaseResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建用户"""
    try:
        user_service = UserService(db)
        user = user_service.create_user(user_data)
        return BaseResponse(
            success=True,
            message="创建用户成功",
            data={"user_id": user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建用户失败: {str(e)}"
        )


@router.put("/{user_id}", response_model=BaseResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户"""
    try:
        user_service = UserService(db)
        user = user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return BaseResponse(
            success=True,
            message="更新用户成功",
            data={"user_id": user.id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )


@router.delete("/{user_id}", response_model=BaseResponse)
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除用户"""
    try:
        user_service = UserService(db)
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return BaseResponse(
            success=True,
            message="删除用户成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )


@router.post("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        user_service = UserService(db)
        success = user_service.change_password(
            current_user.id,
            password_data.old_password,
            password_data.new_password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="原密码错误"
            )
        return BaseResponse(
            success=True,
            message="密码修改成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密码修改失败: {str(e)}"
        )


@router.post("/upload-avatar", response_model=BaseResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """上传头像"""
    try:
        user_service = UserService(db)
        avatar_url = user_service.upload_avatar(current_user.id, file)
        return BaseResponse(
            success=True,
            message="头像上传成功",
            data={"avatar_url": avatar_url}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"头像上传失败: {str(e)}"
        )


@router.get("/profile/me", response_model=BaseResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取我的个人资料"""
    try:
        user_service = UserService(db)
        profile = user_service.get_user_profile(current_user.id)
        return BaseResponse(
            success=True,
            message="获取个人资料成功",
            data=profile
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个人资料失败: {str(e)}"
        )


@router.put("/profile/me", response_model=BaseResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新我的个人资料"""
    try:
        user_service = UserService(db)
        user = user_service.update_user_profile(current_user.id, user_data)
        return BaseResponse(
            success=True,
            message="更新个人资料成功",
            data={"user_id": user.id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新个人资料失败: {str(e)}"
        ) 