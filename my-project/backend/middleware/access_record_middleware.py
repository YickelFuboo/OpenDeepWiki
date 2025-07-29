"""
访问记录中间件

记录用户访问日志和统计信息
"""

import logging
import time
from typing import Optional, Dict, Any
from fastapi import Request, Response
from sqlalchemy.orm import Session

from database import get_db
from models.access_log import AccessLog
from services.statistics_service import StatisticsService

logger = logging.getLogger(__name__)

class AccessRecordMiddleware:
    """访问记录中间件"""
    
    def __init__(self):
        self.statistics_service = StatisticsService()
    
    async def __call__(self, request: Request, call_next):
        """中间件处理逻辑"""
        start_time = time.time()
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 记录访问日志
            await self._record_access(request, response, start_time)
            
            return response
            
        except Exception as e:
            # 记录错误访问
            await self._record_error_access(request, str(e), start_time)
            raise
    
    async def _record_access(self, request: Request, response: Response, start_time: float):
        """记录访问日志"""
        try:
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 获取请求信息
            path = request.url.path
            method = request.method
            status_code = response.status_code
            user_agent = request.headers.get("User-Agent", "")
            ip_address = self._get_client_ip(request)
            
            # 获取用户信息
            current_user = await self._get_current_user(request)
            user_id = current_user.get("id") if current_user else None
            
            # 确定资源类型和ID
            resource_type, resource_id = self._extract_resource_info(path)
            
            # 创建访问记录
            access_log = AccessLog(
                id=f"log_{int(time.time() * 1000)}",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                path=path,
                method=method,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                response_time=response_time,
                created_at=time.time()
            )
            
            # 保存到数据库
            db = next(get_db())
            db.add(access_log)
            db.commit()
            
            # 异步更新统计信息
            await self._update_statistics(access_log)
            
        except Exception as e:
            logger.error(f"记录访问日志异常: {str(e)}")
    
    async def _record_error_access(self, request: Request, error_message: str, start_time: float):
        """记录错误访问"""
        try:
            response_time = (time.time() - start_time) * 1000
            
            path = request.url.path
            method = request.method
            user_agent = request.headers.get("User-Agent", "")
            ip_address = self._get_client_ip(request)
            
            current_user = await self._get_current_user(request)
            user_id = current_user.get("id") if current_user else None
            
            resource_type, resource_id = self._extract_resource_info(path)
            
            # 创建错误访问记录
            access_log = AccessLog(
                id=f"error_log_{int(time.time() * 1000)}",
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                path=path,
                method=method,
                status_code=500,
                ip_address=ip_address,
                user_agent=user_agent,
                response_time=response_time,
                error_message=error_message,
                created_at=time.time()
            )
            
            # 保存到数据库
            db = next(get_db())
            db.add(access_log)
            db.commit()
            
        except Exception as e:
            logger.error(f"记录错误访问日志异常: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 获取直接IP
        client = request.client
        if client:
            return client.host
        
        return "unknown"
    
    async def _get_current_user(self, request: Request) -> Optional[Dict[str, Any]]:
        """获取当前用户"""
        try:
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None
            
            token = authorization.replace("Bearer ", "")
            
            from utils.auth import verify_token
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # 获取数据库会话
            db = next(get_db())
            from models.user import User
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            
        except Exception as e:
            logger.error(f"获取当前用户异常: {str(e)}")
            return None
    
    def _extract_resource_info(self, path: str) -> tuple:
        """提取资源类型和ID"""
        try:
            path_parts = path.split("/")
            
            # 检查是否是仓库相关
            if "warehouses" in path_parts:
                warehouse_index = path_parts.index("warehouses")
                if warehouse_index + 1 < len(path_parts):
                    warehouse_id = path_parts[warehouse_index + 1]
                    return "warehouse", warehouse_id
            
            # 检查是否是文档相关
            elif "documents" in path_parts:
                document_index = path_parts.index("documents")
                if document_index + 1 < len(path_parts):
                    document_id = path_parts[document_index + 1]
                    return "document", document_id
            
            # 检查是否是用户相关
            elif "users" in path_parts:
                user_index = path_parts.index("users")
                if user_index + 1 < len(path_parts):
                    user_id = path_parts[user_index + 1]
                    return "user", user_id
            
            # 检查是否是角色相关
            elif "roles" in path_parts:
                role_index = path_parts.index("roles")
                if role_index + 1 < len(path_parts):
                    role_id = path_parts[role_index + 1]
                    return "role", role_id
            
            # 默认返回路径作为资源类型
            return "api", path
            
        except Exception as e:
            logger.error(f"提取资源信息异常: {str(e)}")
            return "unknown", "unknown"
    
    async def _update_statistics(self, access_log: AccessLog):
        """更新统计信息"""
        try:
            # 异步更新访问统计
            await self.statistics_service.record_access(
                resource_type=access_log.resource_type,
                resource_id=access_log.resource_id,
                user_id=access_log.user_id,
                ip_address=access_log.ip_address,
                user_agent=access_log.user_agent,
                path=access_log.path,
                method=access_log.method,
                status_code=access_log.status_code,
                response_time=access_log.response_time
            )
            
        except Exception as e:
            logger.error(f"更新统计信息异常: {str(e)}")
    
    def get_access_statistics(self, resource_type: str = None, resource_id: str = None) -> Dict[str, Any]:
        """获取访问统计信息"""
        try:
            db = next(get_db())
            
            query = db.query(AccessLog)
            
            if resource_type:
                query = query.filter(AccessLog.resource_type == resource_type)
            
            if resource_id:
                query = query.filter(AccessLog.resource_id == resource_id)
            
            # 统计总访问量
            total_access = query.count()
            
            # 统计成功访问量
            success_access = query.filter(AccessLog.status_code < 400).count()
            
            # 统计错误访问量
            error_access = query.filter(AccessLog.status_code >= 400).count()
            
            # 统计平均响应时间
            avg_response_time = db.query(
                db.func.avg(AccessLog.response_time)
            ).filter(
                AccessLog.resource_type == resource_type if resource_type else True,
                AccessLog.resource_id == resource_id if resource_id else True
            ).scalar() or 0
            
            return {
                "total_access": total_access,
                "success_access": success_access,
                "error_access": error_access,
                "avg_response_time": round(avg_response_time, 2),
                "success_rate": round(success_access / total_access * 100, 2) if total_access > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"获取访问统计异常: {str(e)}")
            return {
                "total_access": 0,
                "success_access": 0,
                "error_access": 0,
                "avg_response_time": 0,
                "success_rate": 0
            } 