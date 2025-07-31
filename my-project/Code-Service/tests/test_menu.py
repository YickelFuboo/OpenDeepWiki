import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from services.menu_service import MenuService
from schemas.role import MenuItem, UserMenu, UserInfo
from models.user import User, Role, UserInRole

class TestMenuService:
    """菜单服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def menu_service(self, mock_db):
        """创建菜单服务实例"""
        return MenuService(mock_db)

    @pytest.fixture
    def sample_user(self):
        """示例用户数据"""
        return User(
            id="test-user-id",
            username="testuser",
            email="test@example.com",
            is_active=True,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )

    @pytest.fixture
    def sample_roles(self):
        """示例角色数据"""
        return [
            Role(
                id="role-1",
                name="admin",
                description="管理员",
                is_active=True,
                is_system_role=True,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z"
            ),
            Role(
                id="role-2",
                name="user",
                description="普通用户",
                is_active=True,
                is_system_role=False,
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z"
            )
        ]

    def test_get_user_menu_success(self, menu_service, mock_db, sample_user, sample_roles):
        """测试成功获取用户菜单"""
        # 模拟用户查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        
        # 模拟用户角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = [("role-1",), ("role-2",)]
        
        # 模拟角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = sample_roles

        result = menu_service.get_user_menu("test-user-id")

        assert isinstance(result, UserMenu)
        assert result.user is not None
        assert result.user.id == "test-user-id"
        assert result.user.username == "testuser"
        assert "admin" in result.user.role
        assert "user" in result.user.role
        assert len(result.menus) > 0

    def test_get_user_menu_user_not_found(self, menu_service, mock_db):
        """测试获取不存在的用户菜单"""
        # 模拟用户不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            menu_service.get_user_menu("non-existent-user")

        assert exc_info.value.status_code == 404
        assert "用户不存在" in str(exc_info.value.detail)

    def test_get_system_menus_success(self, menu_service):
        """测试成功获取系统菜单"""
        result = menu_service.get_system_menus()

        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查菜单结构
        dashboard_menu = next((menu for menu in result if menu.id == "dashboard"), None)
        assert dashboard_menu is not None
        assert dashboard_menu.name == "首页"
        assert dashboard_menu.path == "/"

    def test_check_user_path_permission_public_path(self, menu_service, mock_db, sample_roles):
        """测试检查公共路径权限"""
        # 模拟用户角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = [("role-1",)]
        
        # 模拟角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = sample_roles

        result = menu_service.check_user_path_permission("/", "test-user-id")

        assert result == True

    def test_check_user_path_permission_admin_path(self, menu_service, mock_db, sample_roles):
        """测试检查管理员路径权限"""
        # 模拟用户角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = [("role-1",)]
        
        # 模拟角色查询
        mock_db.query.return_value.filter.return_value.all.return_value = sample_roles

        result = menu_service.check_user_path_permission("/admin/users", "test-user-id")

        assert result == True

    def test_check_user_path_permission_unauthorized(self, menu_service, mock_db):
        """测试检查未授权路径权限"""
        # 模拟用户没有角色
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = menu_service.check_user_path_permission("/admin/users", "test-user-id")

        assert result == False

    def test_check_user_path_permission_no_user(self, menu_service):
        """测试检查无用户路径权限"""
        result = menu_service.check_user_path_permission("/admin/users", None)

        assert result == False

    def test_filter_menu_by_roles_admin_user(self, menu_service):
        """测试管理员用户菜单过滤"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            required_roles=["admin"],
            children=[]
        )

        result = menu_service._filter_menu_by_roles(menu, ["admin", "user"])

        assert result is not None
        assert result.id == "test-menu"

    def test_filter_menu_by_roles_unauthorized_user(self, menu_service):
        """测试未授权用户菜单过滤"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            required_roles=["admin"],
            children=[]
        )

        result = menu_service._filter_menu_by_roles(menu, ["user"])

        assert result is None

    def test_filter_menu_by_roles_public_menu(self, menu_service):
        """测试公共菜单过滤"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            required_roles=[],
            children=[]
        )

        result = menu_service._filter_menu_by_roles(menu, ["user"])

        assert result is not None
        assert result.id == "test-menu"

    def test_find_menu_by_path_success(self, menu_service):
        """测试成功查找菜单路径"""
        menus = [
            MenuItem(
                id="menu-1",
                name="菜单1",
                path="/menu1",
                children=[
                    MenuItem(
                        id="menu-1-1",
                        name="子菜单1",
                        path="/menu1/sub1",
                        children=[]
                    )
                ]
            )
        ]

        result = menu_service._find_menu_by_path(menus, "/menu1/sub1")

        assert result is not None
        assert result.id == "menu-1-1"

    def test_find_menu_by_path_not_found(self, menu_service):
        """测试查找不存在的菜单路径"""
        menus = [
            MenuItem(
                id="menu-1",
                name="菜单1",
                path="/menu1",
                children=[]
            )
        ]

        result = menu_service._find_menu_by_path(menus, "/non-existent")

        assert result is None

    def test_get_menu_breadcrumb_success(self, menu_service):
        """测试成功获取面包屑"""
        menus = [
            MenuItem(
                id="menu-1",
                name="菜单1",
                path="/menu1",
                children=[
                    MenuItem(
                        id="menu-1-1",
                        name="子菜单1",
                        path="/menu1/sub1",
                        children=[]
                    )
                ]
            )
        ]

        result = menu_service.get_menu_breadcrumb(menus, "/menu1/sub1")

        assert len(result) == 2
        assert result[0].id == "menu-1"
        assert result[1].id == "menu-1-1"

    def test_get_menu_breadcrumb_not_found(self, menu_service):
        """测试获取不存在的面包屑"""
        menus = [
            MenuItem(
                id="menu-1",
                name="菜单1",
                path="/menu1",
                children=[]
            )
        ]

        result = menu_service.get_menu_breadcrumb(menus, "/non-existent")

        assert len(result) == 0

    def test_is_menu_active_exact_match(self, menu_service):
        """测试菜单激活状态精确匹配"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            children=[]
        )

        result = menu_service.is_menu_active(menu, "/test")

        assert result == True

    def test_is_menu_active_child_match(self, menu_service):
        """测试菜单激活状态子菜单匹配"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            children=[
                MenuItem(
                    id="test-sub-menu",
                    name="子菜单",
                    path="/test/sub",
                    children=[]
                )
            ]
        )

        result = menu_service.is_menu_active(menu, "/test/sub")

        assert result == True

    def test_is_menu_active_no_match(self, menu_service):
        """测试菜单激活状态无匹配"""
        menu = MenuItem(
            id="test-menu",
            name="测试菜单",
            path="/test",
            children=[]
        )

        result = menu_service.is_menu_active(menu, "/other")

        assert result == False

    def test_flatten_menus_success(self, menu_service):
        """测试成功扁平化菜单"""
        menus = [
            MenuItem(
                id="menu-1",
                name="菜单1",
                path="/menu1",
                children=[
                    MenuItem(
                        id="menu-1-1",
                        name="子菜单1",
                        path="/menu1/sub1",
                        children=[]
                    )
                ]
            )
        ]

        result = menu_service.flatten_menus(menus)

        assert len(result) == 2
        assert result[0].id == "menu-1"
        assert result[1].id == "menu-1-1"

    def test_get_admin_menu_list_success(self, menu_service):
        """测试成功获取管理员菜单列表"""
        result = menu_service.get_admin_menu_list()

        assert isinstance(result, list)
        assert len(result) > 0
        
        admin_menu = result[0]
        assert admin_menu.id == "admin"
        assert admin_menu.name == "系统管理"
        assert "admin" in admin_menu.required_roles

    def test_build_user_menus_with_admin_role(self, menu_service):
        """测试构建管理员用户菜单"""
        result = menu_service._build_user_menus(["admin"])

        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查是否包含管理员菜单
        admin_menus = [menu for menu in result if "admin" in menu.required_roles]
        assert len(admin_menus) > 0

    def test_build_user_menus_with_user_role(self, menu_service):
        """测试构建普通用户菜单"""
        result = menu_service._build_user_menus(["user"])

        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查是否不包含管理员菜单
        admin_menus = [menu for menu in result if "admin" in menu.required_roles]
        assert len(admin_menus) == 0

    def test_build_user_menus_with_no_roles(self, menu_service):
        """测试构建无角色用户菜单"""
        result = menu_service._build_user_menus([])

        assert isinstance(result, list)
        assert len(result) > 0
        
        # 检查是否只包含公共菜单
        public_menus = [menu for menu in result if not menu.required_roles]
        assert len(public_menus) > 0 