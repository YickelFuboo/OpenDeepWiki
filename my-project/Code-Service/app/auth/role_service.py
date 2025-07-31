from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid

from models.user import Role, UserInRole
from schemas.common import PaginationParams, PaginatedResponse


class RoleService:
    """角色服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_roles(self, pagination: PaginationParams) -> PaginatedResponse:
        """获取角色列表"""
        query = self.db.query(Role)
        
        # 关键词搜索
        if pagination.keyword:
            query = query.filter(Role.name.contains(pagination.keyword))
        
        # 计算总数
        total = query.count()
        
        # 分页
        roles = query.offset((pagination.page - 1) * pagination.page_size).limit(pagination.page_size).all()
        
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages,
            items=roles
        )
    
    def get_role_by_id(self, role_id: str) -> Optional[Role]:
        """根据ID获取角色"""
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return self.db.query(Role).filter(Role.name == name).first()
    
    def create_role(self, name: str, description: str = None) -> Role:
        """创建角色"""
        # 检查角色名是否已存在
        existing_role = self.get_role_by_name(name)
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )
        
        role = Role(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        
        return role
    
    def update_role(self, role_id: str, name: str = None, description: str = None) -> Role:
        """更新角色"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        if name is not None:
            # 检查新角色名是否已被其他角色使用
            existing_role = self.db.query(Role).filter(
                Role.name == name,
                Role.id != role_id
            ).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="角色名已存在"
                )
            role.name = name
        
        if description is not None:
            role.description = description
        
        self.db.commit()
        self.db.refresh(role)
        
        return role
    
    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = self.get_role_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="角色不存在"
            )
        
        # 检查是否有用户使用该角色
        user_count = self.db.query(UserInRole).filter(UserInRole.role_id == role_id).count()
        if user_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该角色正在被用户使用，无法删除"
            )
        
        # 删除角色
        self.db.delete(role)
        self.db.commit()
        
        return True
    
    def get_or_create_role(self, name: str, description: str = None) -> Role:
        """获取或创建角色"""
        role = self.get_role_by_name(name)
        if not role:
            role = self.create_role(name, description)
        
        return role
    
    def get_role_users(self, role_id: str) -> List:
        """获取角色的用户列表"""
        from models.user import User
        
        user_roles = self.db.query(UserInRole).filter(UserInRole.role_id == role_id).all()
        user_ids = [ur.user_id for ur in user_roles]
        users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        
        return users 