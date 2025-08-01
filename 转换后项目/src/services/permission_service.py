from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from loguru import logger

from src.models.role import Role, UserRole, WarehouseRole
from src.models.user import User
from src.models.warehouse import Warehouse
from src.models.repository import WarehouseStatus
from src.dto.role_dto import (
    WarehousePermissionTreeDto, WarehousePermissionDto,
    WarehousePermissionDetailDto, RoleInfoDto, UserRoleDto,
    RolePermissionDto
)


class PermissionService:
    """权限管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_warehouse_permission_tree(self, role_id: Optional[str] = None) -> List[WarehousePermissionTreeDto]:
        """获取仓库权限树形结构"""
        try:
            # 获取所有已完成的仓库，按组织分组
            result = await self.db.execute(
                select(Warehouse)
                .where(Warehouse.status == WarehouseStatus.COMPLETED)
                .order_by(Warehouse.organization_name, Warehouse.name)
            )
            warehouses = result.scalars().all()
            
            # 获取角色的现有权限（如果提供了角色ID）
            existing_permissions = {}
            if role_id:
                permissions_result = await self.db.execute(
                    select(WarehouseRole).where(WarehouseRole.role_id == role_id)
                )
                permissions = permissions_result.scalars().all()
                existing_permissions = {p.warehouse_id: p for p in permissions}
            
            # 按组织分组构建树形结构
            tree = []
            org_groups = {}
            
            for warehouse in warehouses:
                org_name = warehouse.organization_name
                if org_name not in org_groups:
                    org_groups[org_name] = []
                org_groups[org_name].append(warehouse)
            
            for org_name, org_warehouses in org_groups.items():
                org_node = WarehousePermissionTreeDto(
                    id=f"org_{org_name}",
                    name=org_name,
                    type="organization",
                    is_selected=False,
                    children=[]
                )
                
                # 检查组织下是否所有仓库都被选中
                selected_warehouse_count = 0
                
                for warehouse in org_warehouses:
                    is_selected = warehouse.id in existing_permissions
                    if is_selected:
                        selected_warehouse_count += 1
                    
                    warehouse_node = WarehousePermissionTreeDto(
                        id=warehouse.id,
                        name=warehouse.name,
                        type="warehouse",
                        is_selected=is_selected
                    )
                    
                    # 如果选中，设置权限配置
                    if is_selected and warehouse.id in existing_permissions:
                        permission = existing_permissions[warehouse.id]
                        warehouse_node.permission = WarehousePermissionDto(
                            warehouse_id=warehouse.id,
                            is_read_only=permission.is_read_only,
                            is_write=permission.is_write,
                            is_delete=permission.is_delete
                        )
                    
                    org_node.children.append(warehouse_node)
                
                # 如果组织下所有仓库都被选中，则组织节点也被选中
                if selected_warehouse_count == len(org_warehouses) and len(org_warehouses) > 0:
                    org_node.is_selected = True
                
                tree.append(org_node)
            
            return tree
            
        except Exception as e:
            logger.error(f"获取仓库权限树失败: {e}")
            raise
    
    async def set_role_permissions(self, role_permission_data: RolePermissionDto) -> bool:
        """设置角色权限"""
        try:
            # 删除角色现有权限
            await self.db.execute(
                select(WarehouseRole).where(WarehouseRole.role_id == role_permission_data.role_id)
            )
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
            logger.error(f"设置角色权限失败: {e}")
            raise
    
    async def get_role_warehouse_permissions(self, role_id: str) -> List[WarehousePermissionDetailDto]:
        """获取角色的仓库权限列表"""
        try:
            # 获取角色的仓库权限
            result = await self.db.execute(
                select(WarehouseRole)
                .options(selectinload(WarehouseRole.warehouse))
                .where(WarehouseRole.role_id == role_id)
            )
            warehouse_roles = result.scalars().all()
            
            permissions = []
            for warehouse_role in warehouse_roles:
                if warehouse_role.warehouse:
                    permission = WarehousePermissionDetailDto(
                        warehouse_id=warehouse_role.warehouse_id,
                        is_read_only=warehouse_role.is_read_only,
                        is_write=warehouse_role.is_write,
                        is_delete=warehouse_role.is_delete,
                        organization_name=warehouse_role.warehouse.organization_name,
                        warehouse_name=warehouse_role.warehouse.name,
                        warehouse_description=warehouse_role.warehouse.description or ""
                    )
                    permissions.append(permission)
            
            return permissions
            
        except Exception as e:
            logger.error(f"获取角色仓库权限失败: {e}")
            raise
    
    async def assign_user_roles(self, user_role_data: UserRoleDto) -> bool:
        """分配用户角色"""
        try:
            # 删除用户现有角色
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
    
    async def get_user_roles(self, user_id: str) -> List[RoleInfoDto]:
        """获取用户的角色列表"""
        try:
            # 获取用户的角色
            result = await self.db.execute(
                select(UserRole)
                .options(selectinload(UserRole.role))
                .where(UserRole.user_id == user_id)
            )
            user_roles = result.scalars().all()
            
            roles = []
            for user_role in user_roles:
                if user_role.role:
                    role_info = RoleInfoDto(
                        id=user_role.role.id,
                        name=user_role.role.name,
                        description=user_role.role.description,
                        is_active=user_role.role.is_active,
                        is_system_role=user_role.role.is_system_role,
                        created_at=user_role.role.created_at,
                        updated_at=user_role.role.updated_at,
                        user_count=0,
                        warehouse_permission_count=0
                    )
                    roles.append(role_info)
            
            return roles
            
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            raise
    
    async def check_user_warehouse_permission(self, user_id: str, warehouse_id: str) -> Optional[WarehousePermissionDto]:
        """检查用户对仓库的权限"""
        try:
            # 获取用户的角色
            user_roles_result = await self.db.execute(
                select(UserRole).where(UserRole.user_id == user_id)
            )
            user_roles = user_roles_result.scalars().all()
            
            if not user_roles:
                return None
            
            role_ids = [ur.role_id for ur in user_roles]
            
            # 获取角色对仓库的权限
            permissions_result = await self.db.execute(
                select(WarehouseRole).where(
                    and_(
                        WarehouseRole.role_id.in_(role_ids),
                        WarehouseRole.warehouse_id == warehouse_id
                    )
                )
            )
            permissions = permissions_result.scalars().all()
            
            if not permissions:
                return None
            
            # 合并所有角色的权限（取最高权限）
            is_read_only = any(p.is_read_only for p in permissions)
            is_write = any(p.is_write for p in permissions)
            is_delete = any(p.is_delete for p in permissions)
            
            return WarehousePermissionDto(
                warehouse_id=warehouse_id,
                is_read_only=is_read_only,
                is_write=is_write,
                is_delete=is_delete
            )
            
        except Exception as e:
            logger.error(f"检查用户仓库权限失败: {e}")
            raise
    
    async def get_user_accessible_warehouses(self, user_id: str) -> List[WarehousePermissionDetailDto]:
        """获取用户可访问的仓库列表"""
        try:
            # 获取用户的角色
            user_roles_result = await self.db.execute(
                select(UserRole).where(UserRole.user_id == user_id)
            )
            user_roles = user_roles_result.scalars().all()
            
            if not user_roles:
                return []
            
            role_ids = [ur.role_id for ur in user_roles]
            
            # 获取角色对仓库的权限
            permissions_result = await self.db.execute(
                select(WarehouseRole)
                .options(selectinload(WarehouseRole.warehouse))
                .where(WarehouseRole.role_id.in_(role_ids))
            )
            permissions = permissions_result.scalars().all()
            
            # 按仓库分组，合并权限
            warehouse_permissions = {}
            for permission in permissions:
                warehouse_id = permission.warehouse_id
                if warehouse_id not in warehouse_permissions:
                    warehouse_permissions[warehouse_id] = {
                        'is_read_only': False,
                        'is_write': False,
                        'is_delete': False,
                        'warehouse': permission.warehouse
                    }
                
                warehouse_permissions[warehouse_id]['is_read_only'] |= permission.is_read_only
                warehouse_permissions[warehouse_id]['is_write'] |= permission.is_write
                warehouse_permissions[warehouse_id]['is_delete'] |= permission.is_delete
            
            # 构建返回数据
            accessible_warehouses = []
            for warehouse_id, perm_data in warehouse_permissions.items():
                if perm_data['warehouse']:
                    warehouse = perm_data['warehouse']
                    permission = WarehousePermissionDetailDto(
                        warehouse_id=warehouse_id,
                        is_read_only=perm_data['is_read_only'],
                        is_write=perm_data['is_write'],
                        is_delete=perm_data['is_delete'],
                        organization_name=warehouse.organization_name,
                        warehouse_name=warehouse.name,
                        warehouse_description=warehouse.description or ""
                    )
                    accessible_warehouses.append(permission)
            
            return accessible_warehouses
            
        except Exception as e:
            logger.error(f"获取用户可访问仓库失败: {e}")
            raise
    
    async def set_organization_permissions(self, role_id: str, organization_name: str, 
                                         permission: WarehousePermissionDto) -> bool:
        """批量设置组织权限"""
        try:
            # 获取组织下的所有仓库
            warehouses_result = await self.db.execute(
                select(Warehouse).where(
                    and_(
                        Warehouse.organization_name == organization_name,
                        Warehouse.status == WarehouseStatus.COMPLETED
                    )
                )
            )
            warehouses = warehouses_result.scalars().all()
            
            # 删除角色对该组织的现有权限
            warehouse_ids = [w.id for w in warehouses]
            existing_permissions = await self.db.execute(
                select(WarehouseRole).where(
                    and_(
                        WarehouseRole.role_id == role_id,
                        WarehouseRole.warehouse_id.in_(warehouse_ids)
                    )
                )
            )
            existing_permissions = existing_permissions.scalars().all()
            
            for perm in existing_permissions:
                await self.db.delete(perm)
            
            # 为组织下的所有仓库设置权限
            for warehouse in warehouses:
                warehouse_role = WarehouseRole(
                    role_id=role_id,
                    warehouse_id=warehouse.id,
                    is_read_only=permission.is_read_only,
                    is_write=permission.is_write,
                    is_delete=permission.is_delete
                )
                self.db.add(warehouse_role)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"设置组织权限失败: {e}")
            raise 