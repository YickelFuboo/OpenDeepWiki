from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status, UploadFile
import uuid
import os
import io
import json
from PIL import Image
import logging

from db.database.models.user import User, UserInRole, Role
from api.schemes.user import UserCreate, UserUpdate, UserResponse
from api.schemes.common import PaginationParams, PaginatedResponse
from service.user_mgmt.password import hash_password, verify_password
from db.storage.factory import get_storage

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_users(self, pagination: PaginationParams) -> PaginatedResponse[UserResponse]:
        """获取用户列表"""
        query = self.db.query(User)
        
        # 关键词搜索
        if pagination.keyword:
            query = query.filter(
                or_(
                    User.name.contains(pagination.keyword),
                    User.email.contains(pagination.keyword)
                )
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        users = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
        
        # 转换为响应模型
        user_responses = []
        for user in users:
            # 获取用户角色
            user_roles = self.db.query(UserInRole).filter(UserInRole.user_id == user.id).all()
            role_ids = [ur.role_id for ur in user_roles]
            roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
            role_names = [role.name for role in roles]
            
            # 获取头像URL
            avatar_url = None
            if user.avatar:
                try:
                    storage = get_storage()
                    avatar_url = storage.get_file_url(user.avatar)
                except Exception as e:
                    logger.warning(f"获取用户头像URL失败: {e}")
            
            user_response = UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                avatar=avatar_url,  # 使用URL而不是file_id
                last_login_at=user.last_login_at,
                last_login_ip=user.last_login_ip,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
                roles=role_names
            )
            user_responses.append(user_response)
        
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=user_responses
        )
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_name_or_email(self, username: str) -> Optional[User]:
        """根据用户名或邮箱获取用户"""
        return self.db.query(User).filter(
            (User.name == username) | (User.email == username)
        ).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名和邮箱是否已存在
        existing_user = self.get_user_by_name_or_email(user_data.name)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名或邮箱已存在"
            )
        
        # 创建用户
        user = User(
            id=str(uuid.uuid4()),
            name=user_data.name,
            email=user_data.email,
            password=hash_password(user_data.password),
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """更新用户"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新用户信息
        if user_data.name:
            user.name = user_data.name
        if user_data.email:
            user.email = user_data.email
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 删除用户角色关联
            self.db.query(UserInRole).filter(UserInRole.user_id == user_id).delete()
            
            # 删除用户
            self.db.delete(user)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            return False
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # 验证旧密码
            if not verify_password(old_password, user.password):
                return False
            
            # 更新密码
            user.password = hash_password(new_password)
            self.db.commit()
            
            return True
        except Exception as e:
            self.db.rollback()
            return False
    
    def get_or_create_role(self, name: str, description: str = None) -> Role:
        """获取或创建角色"""
        role = self.db.query(Role).filter(Role.name == name).first()
        if not role:
            role = Role(
                id=str(uuid.uuid4()),
                name=name,
                description=description
            )
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
        
        return role
    
    def get_or_create_admin_user(self, username: str, email: str, password: str) -> User:
        """获取或创建管理员用户"""
        user = self.get_user_by_name_or_email(username)
        if not user:
            # 创建管理员角色
            admin_role = self.get_or_create_role("admin", "管理员")
            user_role = self.get_or_create_role("user", "普通用户")
            
            # 创建用户
            user = User(
                id=str(uuid.uuid4()),
                name=username,
                email=email,
                password=hash_password(password),
                is_active=True
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # 分配管理员角色
            user_admin_role = UserInRole(
                id=str(uuid.uuid4()),
                user_id=user.id,
                role_id=admin_role.id
            )
            self.db.add(user_admin_role)
            self.db.commit()
        
        return user
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """为用户分配角色"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查是否已经分配了该角色
        existing_role = self.db.query(UserInRole).filter(
            UserInRole.user_id == user_id,
            UserInRole.role_id == role.id
        ).first()
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已拥有该角色"
            )
        
        # 分配角色
        user_role = UserInRole(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role_id=role.id
        )
        self.db.add(user_role)
        self.db.commit()
        
        return True
    
    def remove_role_from_user(self, user_id: str, role_name: str) -> bool:
        """移除用户角色"""
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 删除角色关联
        self.db.query(UserInRole).filter(
            UserInRole.user_id == user_id,
            UserInRole.role_id == role.id
        ).delete()
        self.db.commit()
        
        return True
    
    def get_avatar_url(self, user_id: str) -> Optional[str]:
        """获取用户头像URL"""
        user = self.get_user_by_id(user_id)
        if not user or not user.avatar:
            return None
        
        try:
            storage = get_storage()
            return storage.get_file_url(user.avatar)
        except Exception as e:
            logger.error(f"获取头像URL失败: {e}")
            return None

    def upload_avatar(self, user_id: str, file: UploadFile) -> str:
        """上传用户头像"""
        try:
            # 验证文件类型
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只支持图片文件"
                )
            
            # 验证文件大小 (最大5MB)
            file_size = 0
            file_content = io.BytesIO()
            for chunk in file.file:
                file_content.write(chunk)
                file_size += len(chunk)
                if file_size > 5 * 1024 * 1024:  # 5MB
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="文件大小不能超过5MB"
                    )
            
            file_content.seek(0)
            
            # 处理图片
            try:
                image = Image.open(file_content)
                # 转换为RGB模式
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # 调整图片大小
                max_size = (300, 300)
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # 保存处理后的图片
                processed_image = io.BytesIO()
                image.save(processed_image, format='JPEG', quality=85)
                processed_image.seek(0)
                
                # 生成文件名
                file_extension = os.path.splitext(file.filename)[1] or '.jpg'
                avatar_filename = f"avatar_{user_id}{file_extension}"
                
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="图片格式不支持"
                )
            
            # 获取存储实例
            storage = get_storage()
            
            # 上传文件到存储
            file_id = storage.upload_file(
                file_data=processed_image,
                file_name=avatar_filename,
                content_type='image/jpeg'
            )
            
            # 更新用户头像信息 - 存储file_id
            user = self.get_user_by_id(user_id)
            if user:
                user.avatar = file_id  # 存储文件ID
                self.db.commit()
            
            # 返回访问URL供前端使用
            avatar_url = storage.get_file_url(file_id)
            return avatar_url
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="上传头像失败"
            ) 