from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.user_in_role import UserInRole
from src.models.warehouse_in_role import WarehouseInRole
from src.infrastructure.user_context import UserContext


class WarehousePermissionService:
    """仓库权限管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def check_warehouse_access(self, warehouse_id: str, user_id: Optional[str] = None) -> bool:
        """检查用户对指定仓库的访问权限"""
        try:
            # 检查仓库是否存在权限分配
            warehouse_permission_result = await self.db.execute(
                select(WarehouseInRole).where(WarehouseInRole.warehouse_id == warehouse_id)
            )
            has_permission_assignment = warehouse_permission_result.scalar_one_or_none() is not None
            
            # 如果仓库没有权限分配，则是公共仓库，所有人都可以访问
            if not has_permission_assignment:
                return True
            
            # 如果用户未登录，无法访问有权限分配的仓库
            if not user_id:
                return False
            
            # 获取用户的角色ID列表
            user_roles_result = await self.db.execute(
                select(UserInRole.role_id).where(UserInRole.user_id == user_id)
            )
            user_role_ids = [row[0] for row in user_roles_result.fetchall()]
            
            # 如果用户没有任何角色，无法访问有权限分配的仓库
            if not user_role_ids:
                return False
            
            # 检查用户角色是否有该仓库的权限
            warehouse_access_result = await self.db.execute(
                select(WarehouseInRole).where(
                    WarehouseInRole.warehouse_id == warehouse_id,
                    WarehouseInRole.role_id.in_(user_role_ids)
                )
            )
            
            return warehouse_access_result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"检查仓库访问权限失败: {str(e)}")
            return False
    
    async def check_warehouse_manage_access(self, warehouse_id: str, user_id: Optional[str] = None) -> bool:
        """检查用户对指定仓库的管理权限"""
        try:
            # 如果用户未登录，无管理权限
            if not user_id:
                return False
            
            # 检查仓库是否存在权限分配
            warehouse_permission_result = await self.db.execute(
                select(WarehouseInRole).where(WarehouseInRole.warehouse_id == warehouse_id)
            )
            has_permission_assignment = warehouse_permission_result.scalar_one_or_none() is not None
            
            # 如果仓库没有权限分配，只有管理员可以管理
            if not has_permission_assignment:
                # 这里需要检查用户是否为管理员
                return await self._check_admin_permission(user_id)
            
            # 获取用户的角色ID列表
            user_roles_result = await self.db.execute(
                select(UserInRole.role_id).where(UserInRole.user_id == user_id)
            )
            user_role_ids = [row[0] for row in user_roles_result.fetchall()]
            
            # 如果用户没有任何角色，无管理权限
            if not user_role_ids:
                return False
            
            # 检查用户角色是否有该仓库的管理权限
            warehouse_manage_result = await self.db.execute(
                select(WarehouseInRole).where(
                    WarehouseInRole.warehouse_id == warehouse_id,
                    WarehouseInRole.role_id.in_(user_role_ids)
                )
            )
            
            return warehouse_manage_result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"检查仓库管理权限失败: {str(e)}")
            return False
    
    async def _check_admin_permission(self, user_id: str) -> bool:
        """检查用户是否为管理员"""
        try:
            # 获取用户的角色ID列表
            user_roles_result = await self.db.execute(
                select(UserInRole.role_id).where(UserInRole.user_id == user_id)
            )
            user_role_ids = [row[0] for row in user_roles_result.fetchall()]
            
            # 检查是否有管理员角色（假设角色ID为"admin"表示管理员）
            return "admin" in user_role_ids
            
        except Exception as e:
            logger.error(f"检查管理员权限失败: {str(e)}")
            return False
    
    async def get_user_accessible_warehouses(self, user_id: str) -> list:
        """获取用户可访问的仓库列表"""
        try:
            # 获取用户的角色ID列表
            user_roles_result = await self.db.execute(
                select(UserInRole.role_id).where(UserInRole.user_id == user_id)
            )
            user_role_ids = [row[0] for row in user_roles_result.fetchall()]
            
            # 获取用户角色有权限的仓库
            warehouse_permissions_result = await self.db.execute(
                select(WarehouseInRole.warehouse_id).where(
                    WarehouseInRole.role_id.in_(user_role_ids)
                )
            )
            accessible_warehouse_ids = [row[0] for row in warehouse_permissions_result.fetchall()]
            
            # 获取公共仓库（没有权限分配的仓库）
            public_warehouses_result = await self.db.execute(
                select(Warehouse.id).where(
                    ~Warehouse.id.in_(
                        select(WarehouseInRole.warehouse_id)
                    )
                )
            )
            public_warehouse_ids = [row[0] for row in public_warehouses_result.fetchall()]
            
            # 合并所有可访问的仓库ID
            all_accessible_ids = list(set(accessible_warehouse_ids + public_warehouse_ids))
            
            return all_accessible_ids
            
        except Exception as e:
            logger.error(f"获取用户可访问仓库失败: {str(e)}")
            return [] 