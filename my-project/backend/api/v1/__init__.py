from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .documents import router as documents_router
from .ai import router as ai_router
from .permissions import router as permissions_router
from .menus import router as menus_router
from .document_catalogs import router as document_catalogs_router

# 创建主路由
router = APIRouter(prefix="/v1")

# 注册子路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(users_router, prefix="/users", tags=["用户管理"])
router.include_router(roles_router, prefix="/roles", tags=["角色管理"])
router.include_router(documents_router, prefix="/documents", tags=["文档管理"])
router.include_router(ai_router, prefix="/ai", tags=["AI功能"])
router.include_router(permissions_router, prefix="/permissions", tags=["权限管理"])
router.include_router(menus_router, prefix="/menus", tags=["菜单管理"])
router.include_router(document_catalogs_router, prefix="/document-catalogs", tags=["文档目录"])

# 注册仓库路由（从warehouse模块导入）
from warehouse.api.warehouse_routes import router as warehouse_router
router.include_router(warehouse_router, tags=["仓库管理"])

__all__ = ["router"] 