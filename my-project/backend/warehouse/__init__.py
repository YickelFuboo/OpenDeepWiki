"""
仓库管理模块
提供仓库的创建、更新、删除、权限管理等功能
"""

__all__ = [
    "WarehouseService",
    "warehouse_routes"
]

from .services.warehouse_service import WarehouseService
from .api.warehouse_routes import router as warehouse_routes 