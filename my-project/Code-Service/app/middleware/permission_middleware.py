"""
权限中间件

处理用户权限验证和访问控制
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.connection import get_db
from models.user import User, UserInRole
from models.role import Role
from models.warehouse import Warehouse
from services.permission_service import PermissionService

logger = logging.getLogger(__name__)

class PermissionMiddleware:
    """权限中间件"""
    
    def __init__(self):
        self.permission_service = PermissionService()
    
    async def __call__(self, request: Request, call_next):
        """中间件处理逻辑"""
        try:
            # 跳过不需要权限验证的路径
            if self._should_skip_permission_check(request.url.path):
                return await call_next(request)
            
            # 获取当前用户
            current_user = await self._get_current_user(request)
            if not current_user:
                return await call_next(request)
            
            # 检查用户权限
            has_permission = await self._check_permission(request, current_user)
            if not has_permission:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"message": "权限不足"}
                )
            
            # 继续处理请求
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"权限中间件处理异常: {str(e)}")
            return await call_next(request)
    
    def _should_skip_permission_check(self, path: str) -> bool:
        """检查是否应该跳过权限验证"""
        skip_paths = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/health",
            "/metrics"
        ]
        
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """获取当前用户"""
        try:
            # 从请求头获取token
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None
            
            token = authorization.replace("Bearer ", "")
            
            # 验证token并获取用户信息
            from utils.auth import verify_token
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # 获取数据库会话
            db = next(get_db())
            
            # 查询用户信息
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "roles": self._get_user_roles(db, user.id)
            }
            
        except Exception as e:
            logger.error(f"获取当前用户异常: {str(e)}")
            return None
    
    def _get_user_roles(self, db: Session, user_id: str) -> list:
        """获取用户角色"""
        try:
            user_roles = db.query(UserInRole).filter(UserInRole.user_id == user_id).all()
            role_ids = [ur.role_id for ur in user_roles]
            
            roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
            return [role.name for role in roles]
            
        except Exception as e:
            logger.error(f"获取用户角色异常: {str(e)}")
            return []
    
    async def _check_permission(self, request: Request, user: Dict[str, Any]) -> bool:
        """检查用户权限"""
        try:
            path = request.url.path
            method = request.method
            
            # 管理员拥有所有权限
            if "admin" in user.get("roles", []):
                return True
            
            # 检查路径权限
            if path.startswith("/api/v1/warehouses"):
                return await self._check_warehouse_permission(request, user)
            
            elif path.startswith("/api/v1/documents"):
                return await self._check_document_permission(request, user)
            
            elif path.startswith("/api/v1/users") or path.startswith("/api/v1/roles"):
                # 用户管理和角色管理需要管理员权限
                return "admin" in user.get("roles", [])
            
            # 其他路径默认允许访问
            return True
            
        except Exception as e:
            logger.error(f"检查权限异常: {str(e)}")
            return False
    
    async def _check_warehouse_permission(self, request: Request, user: Dict[str, Any]) -> bool:
        """检查仓库权限"""
        try:
            # 从路径中提取仓库ID
            path_parts = request.url.path.split("/")
            warehouse_id = None
            
            for i, part in enumerate(path_parts):
                if part == "warehouses" and i + 1 < len(path_parts):
                    warehouse_id = path_parts[i + 1]
                    break
            
            if not warehouse_id:
                return True  # 如果没有指定仓库ID，允许访问
            
            # 检查用户是否有该仓库的权限
            db = next(get_db())
            warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            
            if not warehouse:
                return False
            
            # 检查用户是否有该仓库的权限
            has_permission = self.permission_service.check_warehouse_permission(
                user_id=user["id"],
                warehouse_id=warehouse_id,
                permission_type="read"
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"检查仓库权限异常: {str(e)}")
            return False
    
    async def _check_document_permission(self, request: Request, user: Dict[str, Any]) -> bool:
        """检查文档权限"""
        try:
            # 从路径中提取文档ID
            path_parts = request.url.path.split("/")
            document_id = None
            
            for i, part in enumerate(path_parts):
                if part == "documents" and i + 1 < len(path_parts):
                    document_id = path_parts[i + 1]
                    break
            
            if not document_id:
                return True  # 如果没有指定文档ID，允许访问
            
            # 检查用户是否有该文档的权限
            db = next(get_db())
            from models.document import Document
            
            document = db.query(Document).filter(Document.id == document_id).first()
            
            if not document:
                return False
            
            # 检查用户是否有该文档所属仓库的权限
            has_permission = self.permission_service.check_warehouse_permission(
                user_id=user["id"],
                warehouse_id=document.warehouse_id,
                permission_type="read"
            )
            
            return has_permission
            
        except Exception as e:
            logger.error(f"检查文档权限异常: {str(e)}")
            return False 