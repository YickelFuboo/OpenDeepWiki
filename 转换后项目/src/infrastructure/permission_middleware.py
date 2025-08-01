from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from src.models.user_in_role import UserInRole
from src.models.warehouse_in_role import WarehouseInRole
from src.infrastructure.user_context import UserContext


class PermissionMiddleware:
    """权限中间件"""
    
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
                # 暂时返回False，实际应该检查用户角色
                return False
            
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
    
    async def check_admin_permission(self, user_id: Optional[str] = None) -> bool:
        """检查用户是否为管理员"""
        try:
            if not user_id:
                return False
            
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


async def permission_middleware(request: Request, call_next):
    """权限中间件处理函数"""
    try:
        # 获取当前用户ID
        user_context = UserContext()
        current_user_id = user_context.get_current_user_id()
        
        # 检查是否需要权限验证
        path = request.url.path
        
        # 需要权限验证的路径
        protected_paths = [
            "/api/warehouse",
            "/api/document",
            "/api/user",
            "/api/role",
            "/api/permission"
        ]
        
        # 检查是否为受保护的路径
        is_protected = any(path.startswith(protected_path) for protected_path in protected_paths)
        
        if is_protected:
            # 这里应该从请求中获取数据库会话
            # 暂时跳过权限检查，实际应该实现完整的权限验证逻辑
            pass
        
        response = await call_next(request)
        return response
        
    except Exception as e:
        logger.error(f"权限中间件处理失败: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "权限验证失败"}
        ) 