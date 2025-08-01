import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from .database import get_db
from .auth import get_current_user_from_cookie_or_header
from src.models.user import User


class AccessRecordMiddleware(BaseHTTPMiddleware):
    """访问记录中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 获取请求信息
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # 尝试获取用户信息
        user = None
        try:
            async for db in get_db():
                user = await get_current_user_from_cookie_or_header(request, db)
                break
        except Exception as e:
            logger.warning(f"Failed to get user in access record: {e}")
        
        # 记录访问日志
        access_log = {
            "timestamp": time.time(),
            "path": path,
            "method": method,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "user_id": user.id if user else None,
            "username": user.username if user else None,
        }
        
        logger.info(f"Access: {method} {path} - IP: {client_ip} - User: {user.username if user else 'anonymous'}")
        
        # 处理请求
        response = await call_next(request)
        
        # 记录响应时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过不需要权限检查的路径
        skip_paths = ["/health", "/docs", "/openapi.json", "/static", "/api/auth"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # 获取用户信息
        user = None
        try:
            async for db in get_db():
                user = await get_current_user_from_cookie_or_header(request, db)
                break
        except Exception as e:
            logger.warning(f"Failed to get user in permission middleware: {e}")
        
        # 检查权限
        if not user:
            # 对于API请求，返回401
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Authentication required"}
                )
            # 对于其他请求，继续处理（可能是静态文件等）
            return await call_next(request)
        
        # 检查用户是否被禁用
        if not user.is_active:
            return JSONResponse(
                status_code=403,
                content={"detail": "User account is disabled"}
            )
        
        # 将用户信息添加到请求状态中
        request.state.user = user
        
        return await call_next(request)


class GlobalMiddleware(BaseHTTPMiddleware):
    """全局中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 添加请求ID
        request_id = f"{int(time.time() * 1000)}"
        request.state.request_id = request_id
        
        # 添加请求开始时间
        request.state.start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.error(f"Global middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )


class UserContext:
    """用户上下文"""
    
    def __init__(self, user: User):
        self.user = user
        self.user_id = user.id
        self.username = user.username
        self.roles = user.roles
        self.is_admin = "admin" in user.roles


async def get_user_context(request: Request) -> UserContext:
    """获取用户上下文"""
    user = getattr(request.state, 'user', None)
    if user:
        return UserContext(user)
    return None 