from typing import List, Optional
from loguru import logger

from src.dto.menu_dto import MenuItemDto, UserMenuDto
from src.dto.user_dto import UserInfoDto
from src.services.user_service import UserService


class MenuService:
    """菜单管理服务"""
    
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def get_user_menu(self, user_id: str) -> UserMenuDto:
        """获取用户菜单"""
        try:
            # 获取用户信息
            user_info = await self.user_service.get_user_info(user_id)
            if not user_info:
                raise ValueError("用户不存在")
            
            # 获取用户角色
            user_roles = user_info.role.split(',') if user_info.role else []
            
            # 构建菜单
            menus = self._build_user_menus(user_roles)
            
            return UserMenuDto(
                user=user_info,
                menus=menus
            )
        except Exception as ex:
            logger.error(f"获取用户菜单失败: UserId={user_id}, Error={ex}")
            raise
    
    async def get_system_menus(self) -> List[MenuItemDto]:
        """获取系统菜单结构"""
        try:
            return self._get_system_menu_structure()
        except Exception as ex:
            logger.error(f"获取系统菜单失败: Error={ex}")
            raise
    
    def _build_user_menus(self, user_roles: List[str]) -> List[MenuItemDto]:
        """构建用户菜单"""
        all_menus = self._get_system_menu_structure()
        user_menus = []
        
        for menu in all_menus:
            filtered_menu = self._filter_menu_by_roles(menu, user_roles)
            if filtered_menu:
                user_menus.append(filtered_menu)
        
        return user_menus
    
    def _filter_menu_by_roles(self, menu: MenuItemDto, user_roles: List[str]) -> Optional[MenuItemDto]:
        """根据角色过滤菜单"""
        # 检查当前菜单项是否有权限访问
        if menu.required_roles and not any(role in user_roles for role in menu.required_roles):
            return None
        
        # 过滤子菜单
        filtered_children = []
        for child in menu.children:
            filtered_child = self._filter_menu_by_roles(child, user_roles)
            if filtered_child:
                filtered_children.append(filtered_child)
        
        # 创建过滤后的菜单项
        filtered_menu = MenuItemDto(
            id=menu.id,
            name=menu.name,
            path=menu.path,
            icon=menu.icon,
            order=menu.order,
            is_hidden=menu.is_hidden,
            required_roles=menu.required_roles,
            children=filtered_children
        )
        
        return filtered_menu
    
    def _get_system_menu_structure(self) -> List[MenuItemDto]:
        """获取系统菜单结构"""
        return [
            # 首页
            MenuItemDto(
                id="dashboard",
                name="首页",
                path="/",
                icon="dashboard",
                order=1,
                required_roles=[]
            ),
            
            # 仓库管理
            MenuItemDto(
                id="repositories",
                name="仓库管理",
                path="/repositories",
                icon="repository",
                order=2,
                required_roles=[],
                children=[
                    MenuItemDto(
                        id="repository-list",
                        name="仓库列表",
                        path="/repositories",
                        order=1,
                        required_roles=[]
                    ),
                    MenuItemDto(
                        id="repository-create",
                        name="创建仓库",
                        path="/repositories/create",
                        order=2,
                        required_roles=["admin"]
                    )
                ]
            ),
            
            # 用户管理
            MenuItemDto(
                id="users",
                name="用户管理",
                path="/admin/users",
                icon="user",
                order=3,
                required_roles=["admin"]
            ),
            
            # 角色管理
            MenuItemDto(
                id="roles",
                name="角色管理",
                path="/admin/roles",
                icon="team",
                order=4,
                required_roles=["admin"]
            ),
            
            # 权限管理
            MenuItemDto(
                id="permissions",
                name="权限管理",
                path="/admin/permissions",
                icon="safety",
                order=5,
                required_roles=["admin"]
            ),
            
            # 系统设置
            MenuItemDto(
                id="settings",
                name="系统设置",
                path="/admin/settings",
                icon="setting",
                order=6,
                required_roles=["admin"]
            ),
            
            # AI服务
            MenuItemDto(
                id="ai",
                name="AI服务",
                path="/ai",
                icon="robot",
                order=7,
                required_roles=[]
            ),
            
            # 统计报表
            MenuItemDto(
                id="statistics",
                name="统计报表",
                path="/statistics",
                icon="bar-chart",
                order=8,
                required_roles=["admin"]
            )
        ] 