from fastapi import APIRouter
from .auth import auth_router
from .user import user_router
from .repository import repository_router
from .warehouse import warehouse_router
from .statistics import statistics_router
from .ai import ai_router
from .role import role_router
from .permission import permission_router
from .menu import menu_router
from .app_config import app_config_router
from .code_map import code_map_router
from .document_catalog import document_catalog_router
from .mcp import mcp_router
from .mem0 import mem0_router
from .koala_warehouse import koala_warehouse_router
from .document_pending import document_pending_router
from .fine_tuning import fine_tuning_router

# 创建主路由
api_router = APIRouter()

# 包含子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(user_router, prefix="/user", tags=["用户"])
api_router.include_router(repository_router, prefix="/repository", tags=["仓库"])
api_router.include_router(warehouse_router, prefix="/warehouse", tags=["知识仓库"])
api_router.include_router(statistics_router, prefix="/statistics", tags=["统计"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI服务"])
api_router.include_router(role_router, prefix="/role", tags=["角色管理"])
api_router.include_router(permission_router, prefix="/permission", tags=["权限管理"])
api_router.include_router(menu_router, prefix="/menu", tags=["菜单管理"])
api_router.include_router(app_config_router, prefix="/appconfig", tags=["应用配置"])
api_router.include_router(code_map_router, prefix="/codemap", tags=["代码映射"])
api_router.include_router(document_catalog_router, prefix="/documentcatalog", tags=["文档目录"])
api_router.include_router(mcp_router, prefix="/mcp", tags=["MCP服务"])
api_router.include_router(mem0_router, prefix="/mem0", tags=["Mem0服务"])
api_router.include_router(koala_warehouse_router, prefix="/koalawarehouse", tags=["Koala仓库服务"])
api_router.include_router(document_pending_router, prefix="/documentpending", tags=["文档待处理"])
api_router.include_router(fine_tuning_router, prefix="/finetuning", tags=["微调管理"])

__all__ = ["api_router"] 