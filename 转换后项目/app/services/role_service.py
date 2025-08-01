from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from loguru import logger

from src.models.role import Role, UserRole, WarehouseRole
from src.models.user import User
from src.models.warehouse import Warehouse
from src.dto.role_dto import (
    CreateRoleDto, UpdateRoleDto, RoleInfoDto, RoleDetailDto,
    UserRoleDto, RolePermissionDto, WarehousePermissionDto
)


class RoleService:
    """角色管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_role_list(self, page: int = 1, page_size: int = 20, 
                           keyword: Optional[str] = None, is_active: Optional[bool] = None) -> dict:
        """获取角色列表"""
        try:
            # 构建查询
            query = select(Role)
            
            # 关键词搜索
            if keyword and keyword.strip():
                query = query.where(
                    Role.name.contains(keyword.strip()) | 
                    Role.description.contains(keyword.strip())
                )
            
            # 状态筛选
            if is_active is not None:
                query = query.where(Role.is_active == is_active)
            
            # 按创建时间降序排序
            query = query.order_by(Role.created_at.desc())
            
            # 计算总数
            count_query = select(func.count(Role.id))
            if keyword and keyword.strip():
                count_query = count_query.where(
                    Role.name.contains(keyword.strip()) | 
                    Role.description.contains(keyword.strip())
                )
            if is_active is not None:
                count_query = count_query.where(Role.is_active == is_active)
            
            total = await self.db.scalar(count_query)
            
            # 分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            roles = await self.db.execute(query)
            roles = roles.scalars().all()
            
            # 构建返回数据
            role_infos = []
            for role in roles:
                role_info = RoleInfoDto(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    is_active=role.is_active,
                    is_system_role=role.is_system_role,
                    created_at=role.created_at,
                    updated_at=role.updated_at,
                    user_count=0,
                    warehouse_permission_count=0
                )
                
                # 计算用户数量
                user_count = await self.db.scalar(
                    select(func.count(UserRole.id)).where(UserRole.role_id == role.id)
                )
                role_info.user_count = user_count or 0
                
                # 计算仓库权限数量
                warehouse_count = await self.db.scalar(
                    select(func.count(WarehouseRole.id)).where(WarehouseRole.role_id == role.id)
                )
                role_info.warehouse_permission_count = warehouse_count or 0
                
                role_infos.append(role_info)
            
            return {
                "total": total,
                "items": role_infos,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"获取角色列表失败: {e}")
            raise
    
    async def get_role_detail(self, role_id: str) -> Optional[RoleDetailDto]:
        """获取角色详情"""
        try:
            # 获取角色信息
            result = await self.db.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                return None
            
            # 获取角色关联的用户
            user_roles = await self.db.execute(
                select(UserRole).where(UserRole.role_id == role_id)
            )
            user_roles = user_roles.scalars().all()
            
            users = []
            for user_role in user_roles:
                user_result = await self.db.execute(
                    select(User).where(User.id == user_role.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    users.append(user.to_dict())
            
            # 获取角色关联的仓库权限
            warehouse_roles = await self.db.execute(
                select(WarehouseRole).where(WarehouseRole.role_id == role_id)
            )
            warehouse_roles = warehouse_roles.scalars().all()
            
            warehouse_permissions = []
            for warehouse_role in warehouse_roles:
                warehouse_result = await self.db.execute(
                    select(Warehouse).where(Warehouse.id == warehouse_role.warehouse_id)
                )
                warehouse = warehouse_result.scalar_one_or_none()
                if warehouse:
                    permission = WarehousePermissionDto(
                        warehouse_id=warehouse_role.warehouse_id,
                        is_read_only=warehouse_role.is_read_only,
                        is_write=warehouse_role.is_write,
                        is_delete=warehouse_role.is_delete
                    )
                    warehouse_permissions.append(permission)
            
            # 构建角色详情
            role_detail = RoleDetailDto(
                id=role.id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                created_at=role.created_at,
                updated_at=role.updated_at,
                user_count=len(users),
                warehouse_permission_count=len(warehouse_permissions),
                users=users,
                warehouse_permissions=warehouse_permissions
            )
            
            return role_detail
            
        except Exception as e:
            logger.error(f"获取角色详情失败: {e}")
            raise
    
    async def create_role(self, role_data: CreateRoleDto) -> RoleInfoDto:
        """创建角色"""
        try:
            # 检查角色名称是否已存在
            existing_role = await self.db.execute(
                select(Role).where(Role.name == role_data.name)
            )
            if existing_role.scalar_one_or_none():
                raise ValueError("角色名称已存在")
            
            # 创建新角色
            new_role = Role(
                name=role_data.name,
                description=role_data.description,
                is_active=role_data.is_active
            )
            
            self.db.add(new_role)
            await self.db.commit()
            await self.db.refresh(new_role)
            
            return RoleInfoDto(
                id=new_role.id,
                name=new_role.name,
                description=new_role.description,
                is_active=new_role.is_active,
                is_system_role=new_role.is_system_role,
                created_at=new_role.created_at,
                updated_at=new_role.updated_at,
                user_count=0,
                warehouse_permission_count=0
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建角色失败: {e}")
            raise
    
    async def update_role(self, role_id: str, role_data: UpdateRoleDto) -> Optional[RoleInfoDto]:
        """更新角色"""
        try:
            # 获取角色
            result = await self.db.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                return None
            
            # 检查角色名称是否已存在（排除当前角色）
            existing_role = await self.db.execute(
                select(Role).where(
                    and_(Role.name == role_data.name, Role.id != role_id)
                )
            )
            if existing_role.scalar_one_or_none():
                raise ValueError("角色名称已存在")
            
            # 更新角色信息
            role.name = role_data.name
            role.description = role_data.description
            role.is_active = role_data.is_active
            
            await self.db.commit()
            await self.db.refresh(role)
            
            return RoleInfoDto(
                id=role.id,
                name=role.name,
                description=role.description,
                is_active=role.is_active,
                is_system_role=role.is_system_role,
                created_at=role.created_at,
                updated_at=role.updated_at,
                user_count=0,
                warehouse_permission_count=0
            )
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新角色失败: {e}")
            raise
    
    async def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        try:
            # 获取角色
            result = await self.db.execute(
                select(Role).where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            
            if not role:
                return False
            
            # 检查是否为系统角色
            if role.is_system_role:
                raise ValueError("系统角色不能删除")
            
            # 删除角色
            await self.db.delete(role)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除角色失败: {e}")
            raise
    
    async def get_all_roles(self) -> List[RoleInfoDto]:
        """获取所有角色"""
        try:
            result = await self.db.execute(
                select(Role).where(Role.is_active == True).order_by(Role.name)
            )
            roles = result.scalars().all()
            
            role_infos = []
            for role in roles:
                role_info = RoleInfoDto(
                    id=role.id,
                    name=role.name,
                    description=role.description,
                    is_active=role.is_active,
                    is_system_role=role.is_system_role,
                    created_at=role.created_at,
                    updated_at=role.updated_at,
                    user_count=0,
                    warehouse_permission_count=0
                )
                role_infos.append(role_info)
            
            return role_infos
            
        except Exception as e:
            logger.error(f"获取所有角色失败: {e}")
            raise
    
    async def batch_update_role_status(self, role_ids: List[str], is_active: bool) -> bool:
        """批量更新角色状态"""
        try:
            # 获取角色列表
            result = await self.db.execute(
                select(Role).where(Role.id.in_(role_ids))
            )
            roles = result.scalars().all()
            
            # 更新状态
            for role in roles:
                if not role.is_system_role:  # 系统角色不能修改状态
                    role.is_active = is_active
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"批量更新角色状态失败: {e}")
            raise
    
    async def assign_user_roles(self, user_role_data: UserRoleDto) -> bool:
        """分配用户角色"""
        try:
            # 删除用户现有角色
            await self.db.execute(
                select(UserRole).where(UserRole.user_id == user_role_data.user_id)
            )
            existing_roles = await self.db.execute(
                select(UserRole).where(UserRole.user_id == user_role_data.user_id)
            )
            existing_roles = existing_roles.scalars().all()
            
            for role in existing_roles:
                await self.db.delete(role)
            
            # 添加新角色
            for role_id in user_role_data.role_ids:
                user_role = UserRole(
                    user_id=user_role_data.user_id,
                    role_id=role_id
                )
                self.db.add(user_role)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"分配用户角色失败: {e}")
            raise
    
    async def assign_role_permissions(self, role_permission_data: RolePermissionDto) -> bool:
        """分配角色权限"""
        try:
            # 删除角色现有权限
            existing_permissions = await self.db.execute(
                select(WarehouseRole).where(WarehouseRole.role_id == role_permission_data.role_id)
            )
            existing_permissions = existing_permissions.scalars().all()
            
            for permission in existing_permissions:
                await self.db.delete(permission)
            
            # 添加新权限
            for permission in role_permission_data.warehouse_permissions:
                warehouse_role = WarehouseRole(
                    role_id=role_permission_data.role_id,
                    warehouse_id=permission.warehouse_id,
                    is_read_only=permission.is_read_only,
                    is_write=permission.is_write,
                    is_delete=permission.is_delete
                )
                self.db.add(warehouse_role)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"分配角色权限失败: {e}")
            raise 