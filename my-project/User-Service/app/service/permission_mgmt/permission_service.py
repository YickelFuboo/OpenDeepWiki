"""
权限管理服务
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from db.models.user import User, Role, Permission
from api.schemes.user import PermissionCreate, PermissionResponse

logger = logging.getLogger(__name__)

class PermissionService:
    """权限管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_user_permission(self, user_id: str, permission_name: str) -> bool:
        """检查用户是否有指定权限"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 获取用户角色
            user_roles = user.roles
            if not user_roles:
                return False
            
            # 检查角色权限
            for role in user_roles:
                if role.permissions:
                    for permission in role.permissions:
                        if permission.name == permission_name and permission.is_active:
                            return True
            
            return False
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            return False
    
    def get_user_permissions(self, user_id: str) -> List[PermissionResponse]:
        """获取用户所有权限"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return []
            
            permissions = []
            for role in user.roles:
                if role.permissions:
                    for permission in role.permissions:
                        if permission.is_active:
                            permissions.append(PermissionResponse(
                                id=permission.id,
                                name=permission.name,
                                description=permission.description,
                                resource=permission.resource,
                                action=permission.action
                            ))
            
            return permissions
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return []
    
    def create_permission(self, permission_data: PermissionCreate) -> Permission:
        """创建权限"""
        try:
            permission = Permission(
                name=permission_data.name,
                description=permission_data.description,
                resource=permission_data.resource,
                action=permission_data.action,
                is_active=True
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            logger.info(f"创建权限成功: {permission.name}")
            return permission
        except Exception as e:
            logger.error(f"创建权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建权限失败"
            )
    
    def assign_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """为角色分配权限"""
        try:
            role = self.db.query(Role).filter(Role.id == role_id).first()
            permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
            
            if not role or not permission:
                return False
            
            if permission not in role.permissions:
                role.permissions.append(permission)
                self.db.commit()
                logger.info(f"为角色 {role.name} 分配权限 {permission.name}")
                return True
            
            return True
        except Exception as e:
            logger.error(f"分配权限失败: {e}")
            return False 