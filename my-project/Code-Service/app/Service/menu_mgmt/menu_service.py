import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime

from models.user import User, UserInRole, Role
from schemas.role import MenuItem, UserMenu, UserInfo
from utils.auth import check_user_permission

logger = logging.getLogger(__name__)

class MenuService:
    """菜单管理服务类，负责菜单管理的核心业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_menu(self, user_id: str) -> UserMenu:
        """获取当前用户的菜单"""
        try:
            # 获取用户信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # 获取用户角色
            user_role_ids = self.db.query(UserInRole.role_id).filter(
                UserInRole.user_id == user_id
            ).all()
            user_role_ids = [role_id[0] for role_id in user_role_ids]
            
            user_roles = self.db.query(Role).filter(
                and_(
                    Role.id.in_(user_role_ids),
                    Role.is_active == True
                )
            ).all()
            
            user_role_names = [role.name for role in user_roles]
            
            # 构建用户信息
            user_info = UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                role=",".join(user_role_names)
            )
            
            # 构建菜单
            menus = self._build_user_menus(user_role_names)
            
            return UserMenu(
                user=user_info,
                menus=menus
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取用户菜单失败: UserId={user_id}, Error={e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取用户菜单失败: {str(e)}"
            )
    
    def get_system_menus(self) -> List[MenuItem]:
        """获取系统菜单结构（管理员权限）"""
        try:
            return self._get_system_menu_structure()
        except Exception as e:
            logger.error(f"获取系统菜单失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取系统菜单失败: {str(e)}"
            )
    
    def check_user_path_permission(self, path: str, user_id: Optional[str] = None) -> bool:
        """检查用户是否有访问指定路径的权限"""
        try:
            if not user_id:
                return False
            
            # 获取用户角色
            user_role_ids = self.db.query(UserInRole.role_id).filter(
                UserInRole.user_id == user_id
            ).all()
            user_role_ids = [role_id[0] for role_id in user_role_ids]
            
            user_roles = self.db.query(Role).filter(
                and_(
                    Role.id.in_(user_role_ids),
                    Role.is_active == True
                )
            ).all()
            
            user_role_names = [role.name for role in user_roles]
            
            # 查找路径对应的菜单项
            all_menus = self._get_system_menu_structure()
            menu_item = self._find_menu_by_path(all_menus, path)
            
            if menu_item is None:
                # 如果路径不在菜单定义中，默认允许访问（比如动态路由）
                return True
            
            # 检查权限
            return not menu_item.required_roles or any(role in user_role_names for role in menu_item.required_roles)
            
        except Exception as e:
            logger.error(f"检查用户路径权限失败: Path={path}, UserId={user_id}, Error={e}")
            return False
    
    def _build_user_menus(self, user_roles: List[str]) -> List[MenuItem]:
        """构建用户菜单"""
        all_menus = self._get_system_menu_structure()
        user_menus = []
        
        for menu in all_menus:
            filtered_menu = self._filter_menu_by_roles(menu, user_roles)
            if filtered_menu:
                user_menus.append(filtered_menu)
        
        return user_menus
    
    def _filter_menu_by_roles(self, menu: MenuItem, user_roles: List[str]) -> Optional[MenuItem]:
        """根据角色过滤菜单"""
        # 检查当前菜单项是否有权限访问
        has_access = not menu.required_roles or any(role in user_roles for role in menu.required_roles)
        
        if not has_access:
            return None
        
        # 过滤子菜单
        filtered_children = []
        for child in menu.children or []:
            filtered_child = self._filter_menu_by_roles(child, user_roles)
            if filtered_child:
                filtered_children.append(filtered_child)
        
        # 如果当前菜单有权限但所有子菜单都没权限，仍然显示当前菜单
        return MenuItem(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            order=menu.order,
            required_roles=menu.required_roles,
            children=filtered_children
        )
    
    def _get_system_menu_structure(self) -> List[MenuItem]:
        """获取系统菜单结构定义"""
        return [
            # 首页
            MenuItem(
                id="dashboard",
                name="首页",
                path="/",
                icon="dashboard",
                order=1,
                required_roles=[],
                children=[]
            ),
            
            # 仓库管理
            MenuItem(
                id="repositories",
                name="仓库管理",
                path="/repositories",
                icon="repository",
                order=2,
                required_roles=[],
                children=[
                    MenuItem(
                        id="repository-list",
                        name="仓库列表",
                        path="/repositories",
                        order=1,
                        required_roles=[],
                        children=[]
                    ),
                    MenuItem(
                        id="repository-create",
                        name="创建仓库",
                        path="/repositories/create",
                        order=2,
                        required_roles=["admin"],
                        children=[]
                    )
                ]
            ),
            
            # 用户管理
            MenuItem(
                id="users",
                name="用户管理",
                path="/admin/users",
                icon="user",
                order=3,
                required_roles=["admin"],
                children=[]
            ),
            
            # 角色管理
            MenuItem(
                id="roles",
                name="角色管理",
                path="/admin/roles",
                icon="role",
                order=4,
                required_roles=["admin"],
                children=[]
            ),
            
            # 权限管理
            MenuItem(
                id="permissions",
                name="权限管理",
                path="/admin/permissions",
                icon="permission",
                order=5,
                required_roles=["admin"],
                children=[
                    MenuItem(
                        id="role-permissions",
                        name="角色权限",
                        path="/admin/permissions/roles",
                        order=1,
                        required_roles=["admin"],
                        children=[]
                    ),
                    MenuItem(
                        id="user-roles",
                        name="用户角色",
                        path="/admin/permissions/users",
                        order=2,
                        required_roles=["admin"],
                        children=[]
                    )
                ]
            ),
            
            # 系统设置
            MenuItem(
                id="settings",
                name="系统设置",
                path="/admin/settings",
                icon="setting",
                order=6,
                required_roles=["admin"],
                children=[
                    MenuItem(
                        id="general-settings",
                        name="基本设置",
                        path="/admin/settings/general",
                        order=1,
                        required_roles=["admin"],
                        children=[]
                    ),
                    MenuItem(
                        id="system-info",
                        name="系统信息",
                        path="/admin/settings/system",
                        order=2,
                        required_roles=["admin"],
                        children=[]
                    )
                ]
            ),
            
            # 微调管理
            MenuItem(
                id="finetune",
                name="微调管理",
                path="/admin/finetune",
                icon="finetune",
                order=7,
                required_roles=["admin"],
                children=[]
            ),
            
            # 统计分析
            MenuItem(
                id="statistics",
                name="统计分析",
                path="/admin/statistics",
                icon="statistics",
                order=8,
                required_roles=["admin"],
                children=[]
            ),
            
            # 个人设置
            MenuItem(
                id="profile",
                name="个人设置",
                path="/settings",
                icon="profile",
                order=99,
                required_roles=[],
                children=[]
            )
        ]
    
    def _find_menu_by_path(self, menus: List[MenuItem], path: str) -> Optional[MenuItem]:
        """根据路径查找菜单项"""
        for menu in menus:
            if menu.path == path:
                return menu
            
            if menu.children:
                child_result = self._find_menu_by_path(menu.children, path)
                if child_result:
                    return child_result
        
        return None
    
    def get_menu_breadcrumb(self, menus: List[MenuItem], current_path: str) -> List[MenuItem]:
        """获取面包屑路径"""
        breadcrumb = []
        
        def find_path(items: List[MenuItem], path: str, current: List[MenuItem]) -> bool:
            for item in items:
                new_path = current + [item]
                
                if item.path == path:
                    breadcrumb.extend(new_path)
                    return True
                
                if item.children:
                    if find_path(item.children, path, new_path):
                        return True
            
            return False
        
        find_path(menus, current_path, [])
        return breadcrumb
    
    def is_menu_active(self, menu: MenuItem, current_path: str) -> bool:
        """检查菜单是否激活（当前路径或子路径）"""
        if menu.path == current_path:
            return True
        
        # 检查是否有子菜单激活
        if menu.children:
            return any(self.is_menu_active(child, current_path) for child in menu.children)
        
        return False
    
    def flatten_menus(self, menus: List[MenuItem]) -> List[MenuItem]:
        """扁平化菜单结构"""
        flattened = []
        
        def flatten(items: List[MenuItem]):
            for item in items:
                flattened.append(item)
                if item.children:
                    flatten(item.children)
        
        flatten(menus)
        return flattened
    
    def get_admin_menu_list(self) -> List[MenuItem]:
        """获取管理员菜单列表（用于权限配置）"""
        return [
            MenuItem(
                id="admin",
                name="系统管理",
                path="/admin",
                icon="admin",
                order=1,
                required_roles=["admin"],
                children=[
                    MenuItem(
                        id="admin-users",
                        name="用户管理",
                        path="/admin/users",
                        icon="user",
                        order=1,
                        required_roles=["admin"],
                        children=[]
                    ),
                    MenuItem(
                        id="admin-roles",
                        name="角色管理",
                        path="/admin/roles",
                        icon="role",
                        order=2,
                        required_roles=["admin"],
                        children=[]
                    ),
                    MenuItem(
                        id="admin-permissions",
                        name="权限管理",
                        path="/admin/permissions",
                        icon="permission",
                        order=3,
                        required_roles=["admin"],
                        children=[
                            MenuItem(
                                id="admin-role-permissions",
                                name="角色权限",
                                path="/admin/permissions/roles",
                                order=1,
                                required_roles=["admin"],
                                children=[]
                            ),
                            MenuItem(
                                id="admin-user-roles",
                                name="用户角色",
                                path="/admin/permissions/users",
                                order=2,
                                required_roles=["admin"],
                                children=[]
                            )
                        ]
                    ),
                    MenuItem(
                        id="admin-repositories",
                        name="仓库管理",
                        path="/admin/repositories",
                        icon="repository",
                        order=4,
                        required_roles=["admin"],
                        children=[]
                    ),
                    MenuItem(
                        id="admin-settings",
                        name="系统设置",
                        path="/admin/settings",
                        icon="setting",
                        order=5,
                        required_roles=["admin"],
                        children=[]
                    )
                ]
            )
        ] 