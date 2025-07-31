import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime

from db.models.user import Role, UserInRole, User
from db.models.warehouse import Warehouse, WarehouseInRole
from api.schemes.role import (
    WarehousePermissionTree, WarehousePermissionDetail,
    RolePermission, WarehousePermission
)
from service.user_mgmt.auth import check_user_permission

logger = logging.getLogger(__name__)

class PermissionService:
    """权限管理服务类，负责权限管理的核心业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_warehouse_permission_tree(self, role_id: Optional[str] = None) -> List[WarehousePermissionTree]:
        """获取仓库权限树形结构"""
        try:
            # 获取所有仓库
            warehouses = self.db.query(Warehouse).filter(
                Warehouse.status.in_(["completed", "processing"])
            ).all()
            
            # 按组织分组
            organizations = {}
            for warehouse in warehouses:
                org_name = warehouse.organization_name
                if org_name not in organizations:
                    organizations[org_name] = []
                organizations[org_name].append(warehouse)
            
            # 构建树形结构
            tree = []
            for org_name, org_warehouses in organizations.items():
                # 组织节点
                org_node = WarehousePermissionTree(
                    key=f"org_{org_name}",
                    title=org_name,
                    type="organization",
                    children=[],
                    permission=None
                )
                
                # 仓库节点
                for warehouse in org_warehouses:
                    # 获取角色权限（如果指定了角色）
                    permission = None
                    if role_id:
                        warehouse_role = self.db.query(WarehouseInRole).filter(
                            and_(
                                WarehouseInRole.role_id == role_id,
                                WarehouseInRole.warehouse_id == warehouse.id
                            )
                        ).first()
                        
                        if warehouse_role:
                            permission = WarehousePermission(
                                warehouse_id=warehouse.id,
                                is_read_only=warehouse_role.is_read_only,
                                is_write=warehouse_role.is_write,
                                is_delete=warehouse_role.is_delete
                            )
                    
                    warehouse_node = WarehousePermissionTree(
                        key=warehouse.id,
                        title=warehouse.name,
                        type="warehouse",
                        children=None,
                        permission=permission
                    )
                    
                    org_node.children.append(warehouse_node)
                
                tree.append(org_node)
            
            return tree
            
        except Exception as e:
            logger.error(f"获取仓库权限树失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取仓库权限树失败: {str(e)}"
            )
    
    def set_role_permissions(self, role_permission_data: RolePermission) -> bool:
        """设置角色权限"""
        try:
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_permission_data.role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"角色不存在: {role_permission_data.role_id}"
                )
            
            if role.is_system_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="系统角色权限不能修改"
                )
            
            # 删除角色现有的所有仓库权限
            self.db.query(WarehouseInRole).filter(
                WarehouseInRole.role_id == role_permission_data.role_id
            ).delete()
            
            # 添加新的权限配置
            if role_permission_data.warehouse_permissions:
                warehouse_roles = []
                for permission in role_permission_data.warehouse_permissions:
                    warehouse_role = WarehouseInRole(
                        role_id=role_permission_data.role_id,
                        warehouse_id=permission.warehouse_id,
                        is_read_only=permission.is_read_only,
                        is_write=permission.is_write,
                        is_delete=permission.is_delete,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    warehouse_roles.append(warehouse_role)
                
                self.db.add_all(warehouse_roles)
            
            self.db.commit()
            
            logger.info(f"设置角色权限成功: RoleId={role_permission_data.role_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"设置角色权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"设置角色权限失败: {str(e)}"
            )
    
    def get_role_warehouse_permissions(self, role_id: str) -> List[WarehousePermissionDetail]:
        """获取角色的仓库权限列表"""
        try:
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"角色不存在: {role_id}"
                )
            
            # 获取角色权限
            permissions = self.db.query(WarehouseInRole).join(
                Warehouse, WarehouseInRole.warehouse_id == Warehouse.id
            ).filter(WarehouseInRole.role_id == role_id).all()
            
            permission_details = []
            for permission in permissions:
                detail = WarehousePermissionDetail(
                    warehouse_id=permission.warehouse_id,
                    organization_name=permission.warehouse.organization_name,
                    warehouse_name=permission.warehouse.name,
                    warehouse_description=permission.warehouse.description,
                    is_read_only=permission.is_read_only,
                    is_write=permission.is_write,
                    is_delete=permission.is_delete
                )
                permission_details.append(detail)
            
            return permission_details
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取角色仓库权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取角色仓库权限失败: {str(e)}"
            )
    
    def assign_user_roles(self, user_id: str, role_ids: List[str]) -> bool:
        """分配用户角色"""
        try:
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"用户不存在: {user_id}"
                )
            
            # 验证角色是否存在且有效
            valid_roles = self.db.query(Role).filter(
                and_(
                    Role.id.in_(role_ids),
                    Role.is_active == True
                )
            ).all()
            
            valid_role_ids = [role.id for role in valid_roles]
            
            # 删除用户现有的角色分配
            self.db.query(UserInRole).filter(UserInRole.user_id == user_id).delete()
            
            # 添加新的角色分配
            if valid_role_ids:
                user_roles = []
                for role_id in valid_role_ids:
                    user_role = UserInRole(
                        user_id=user_id,
                        role_id=role_id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    user_roles.append(user_role)
                
                self.db.add_all(user_roles)
            
            self.db.commit()
            
            logger.info(f"分配用户角色成功: UserId={user_id}, RoleIds={valid_role_ids}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"分配用户角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"分配用户角色失败: {str(e)}"
            )
    
    def get_user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的角色列表"""
        try:
            # 获取用户的角色
            user_roles = self.db.query(Role).join(
                UserInRole, Role.id == UserInRole.role_id
            ).filter(UserInRole.user_id == user_id).all()
            
            roles = []
            for role in user_roles:
                role_dict = {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "is_active": role.is_active,
                    "is_system_role": role.is_system_role,
                    "created_at": role.created_at,
                    "updated_at": role.updated_at
                }
                roles.append(role_dict)
            
            return roles
            
        except Exception as e:
            logger.error(f"获取用户角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户角色失败: {str(e)}"
            )
    
    def check_user_warehouse_permission(self, user_id: str, warehouse_id: str) -> Optional[Dict[str, bool]]:
        """检查用户对仓库的权限"""
        try:
            # 获取用户的所有角色
            user_role_ids = self.db.query(UserInRole.role_id).filter(
                UserInRole.user_id == user_id
            ).all()
            user_role_ids = [role_id[0] for role_id in user_role_ids]
            
            if not user_role_ids:
                return None
            
            # 获取用户通过角色可访问的仓库权限
            permissions = self.db.query(WarehouseInRole).filter(
                and_(
                    WarehouseInRole.role_id.in_(user_role_ids),
                    WarehouseInRole.warehouse_id == warehouse_id
                )
            ).all()
            
            if not permissions:
                return None
            
            # 合并权限（任一角色有权限则认为用户有权限）
            return {
                "is_read_only": any(p.is_read_only for p in permissions),
                "is_write": any(p.is_write for p in permissions),
                "is_delete": any(p.is_delete for p in permissions)
            }
            
        except Exception as e:
            logger.error(f"检查用户仓库权限失败: {e}")
            return None
    
    def get_user_accessible_warehouses(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户可访问的仓库"""
        try:
            # 获取用户的所有角色
            user_role_ids = self.db.query(UserInRole.role_id).filter(
                UserInRole.user_id == user_id
            ).all()
            user_role_ids = [role_id[0] for role_id in user_role_ids]
            
            if not user_role_ids:
                return []
            
            # 获取用户通过角色可访问的仓库
            accessible_warehouses = self.db.query(WarehouseInRole).join(
                Warehouse, WarehouseInRole.warehouse_id == Warehouse.id
            ).filter(WarehouseInRole.role_id.in_(user_role_ids)).all()
            
            # 按仓库分组并合并权限
            warehouse_permissions = {}
            for aw in accessible_warehouses:
                warehouse_id = aw.warehouse_id
                if warehouse_id not in warehouse_permissions:
                    warehouse_permissions[warehouse_id] = {
                        "warehouse_id": warehouse_id,
                        "organization_name": aw.warehouse.organization_name,
                        "warehouse_name": aw.warehouse.name,
                        "warehouse_description": aw.warehouse.description,
                        "is_read_only": False,
                        "is_write": False,
                        "is_delete": False
                    }
                
                warehouse_permissions[warehouse_id]["is_read_only"] |= aw.is_read_only
                warehouse_permissions[warehouse_id]["is_write"] |= aw.is_write
                warehouse_permissions[warehouse_id]["is_delete"] |= aw.is_delete
            
            return list(warehouse_permissions.values())
            
        except Exception as e:
            logger.error(f"获取用户可访问仓库失败: {e}")
            return []
    
    def set_organization_permissions(self, role_id: str, organization_name: str, permissions: WarehousePermission) -> bool:
        """批量设置组织权限（为角色设置某个组织下所有仓库的权限）"""
        try:
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"角色不存在: {role_id}"
                )
            
            if role.is_system_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="系统角色权限不能修改"
                )
            
            # 获取组织下所有仓库
            warehouses = self.db.query(Warehouse).filter(
                and_(
                    Warehouse.organization_name == organization_name,
                    Warehouse.status.in_(["completed", "processing"])
                )
            ).all()
            
            if not warehouses:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"组织下没有找到可用的仓库: {organization_name}"
                )
            
            # 删除该组织下所有仓库的现有权限
            warehouse_ids = [w.id for w in warehouses]
            self.db.query(WarehouseInRole).filter(
                and_(
                    WarehouseInRole.role_id == role_id,
                    WarehouseInRole.warehouse_id.in_(warehouse_ids)
                )
            ).delete()
            
            # 添加新的权限配置
            warehouse_roles = []
            for warehouse in warehouses:
                warehouse_role = WarehouseInRole(
                    role_id=role_id,
                    warehouse_id=warehouse.id,
                    is_read_only=permissions.is_read_only,
                    is_write=permissions.is_write,
                    is_delete=permissions.is_delete,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                warehouse_roles.append(warehouse_role)
            
            self.db.add_all(warehouse_roles)
            self.db.commit()
            
            logger.info(f"批量设置组织权限成功: RoleId={role_id}, Organization={organization_name}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"批量设置组织权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"批量设置组织权限失败: {str(e)}"
            ) 