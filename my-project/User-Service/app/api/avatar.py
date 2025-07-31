"""
头像相关API
"""

import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db.database.factory import get_db
from ..db.storage.factory import get_storage
from ..service.user_mgmt.user_service import UserService
from ..service.user_mgmt.avatar_service import AvatarService
from ..api.schemes.user import UserResponse
from ..logger.logger import logger

router = APIRouter()

@router.post("/upload/{user_id}")
async def upload_avatar(
    user_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传用户头像
    
    Args:
        user_id: 用户ID
        file: 上传的文件
    
    Returns:
        用户信息（包含头像URL）
    """
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只能上传图片文件")
        
        # 验证文件大小（限制为5MB）
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
        
        # 获取存储服务
        storage = get_storage()
        
        # 上传文件
        file_id = storage.upload_file(
            file_data=file.file,
            file_name=file.filename,
            content_type=file.content_type,
            bucket_name="avatars"
        )
        
        # 更新用户头像
        user_service = UserService(db)
        user = user_service.update_user_avatar(user_id, file_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 获取头像URL
        avatar_url = storage.get_file_url(file_id, bucket_name="avatars")
        
        return {
            "message": "头像上传成功",
            "user_id": user_id,
            "file_id": file_id,
            "avatar_url": avatar_url,
            "user": UserResponse.from_orm(user)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传头像失败: {e}")
        raise HTTPException(status_code=500, detail="上传头像失败")

@router.get("/{file_id}")
async def get_avatar(file_id: str):
    """
    获取头像文件
    
    Args:
        file_id: 文件ID
    
    Returns:
        头像文件
    """
    try:
        storage = get_storage()
        
        # 检查文件是否存在
        if not storage.file_exists(file_id, bucket_name="avatars"):
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        # 获取文件
        file_data = storage.download_file(file_id, bucket_name="avatars")
        
        if not file_data:
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        # 获取文件元数据
        metadata = storage.get_file_metadata(file_id, bucket_name="avatars")
        content_type = metadata.get('content_type', 'image/jpeg') if metadata else 'image/jpeg'
        
        # 返回文件
        return FileResponse(
            file_data,
            media_type=content_type,
            filename=f"avatar_{file_id}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取头像失败: {e}")
        raise HTTPException(status_code=500, detail="获取头像失败")

@router.delete("/{file_id}")
async def delete_avatar(
    file_id: str,
    db: Session = Depends(get_db)
):
    """
    删除头像文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
    
    Returns:
        删除结果
    """
    try:
        storage = get_storage()
        
        # 检查文件是否存在
        if not storage.file_exists(file_id, bucket_name="avatars"):
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        # 删除文件
        success = storage.delete_file(file_id, bucket_name="avatars")
        
        if not success:
            raise HTTPException(status_code=500, detail="删除头像失败")
        
        # 更新用户头像字段（如果有用户使用此头像）
        user_service = UserService(db)
        user_service.clear_user_avatar_by_file_id(file_id)
        
        return {"message": "头像删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除头像失败: {e}")
        raise HTTPException(status_code=500, detail="删除头像失败")

@router.get("/{file_id}/metadata")
async def get_avatar_metadata(file_id: str):
    """
    获取头像文件元数据
    
    Args:
        file_id: 文件ID
    
    Returns:
        文件元数据
    """
    try:
        storage = get_storage()
        
        # 检查文件是否存在
        if not storage.file_exists(file_id, bucket_name="avatars"):
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        # 获取文件元数据
        metadata = storage.get_file_metadata(file_id, bucket_name="avatars")
        
        if not metadata:
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        return {
            "file_id": file_id,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取头像元数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取头像元数据失败") 