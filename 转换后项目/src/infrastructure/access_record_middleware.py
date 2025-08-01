import time
from typing import Optional
from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from loguru import logger

from src.models.access_record import AccessRecord
from src.infrastructure.user_context import UserContext


class AccessRecordMiddleware:
    """访问记录中间件"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_access(
        self,
        request: Request,
        response: Response,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """记录访问信息"""
        try:
            # 获取请求信息
            path = request.url.path
            method = request.method
            status_code = response.status_code
            
            # 获取IP地址
            if not ip_address:
                ip_address = self._get_client_ip(request)
            
            # 获取用户代理
            if not user_agent:
                user_agent = request.headers.get("user-agent", "")
            
            # 获取用户ID
            if not user_id:
                user_context = UserContext()
                user_id = user_context.get_current_user_id()
            
            # 创建访问记录
            access_record = AccessRecord(
                user_id=user_id,
                path=path,
                method=method,
                status_code=status_code,
                ip_address=ip_address,
                user_agent=user_agent,
                request_time=time.time(),
                response_time=time.time()
            )
            
            # 保存到数据库
            await self.db.execute(insert(AccessRecord).values(
                user_id=access_record.user_id,
                path=access_record.path,
                method=access_record.method,
                status_code=access_record.status_code,
                ip_address=access_record.ip_address,
                user_agent=access_record.user_agent,
                request_time=access_record.request_time,
                response_time=access_record.response_time
            ))
            await self.db.commit()
            
            logger.info(f"记录访问: {method} {path} - {status_code}")
            
        except Exception as e:
            logger.error(f"记录访问信息失败: {str(e)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 尝试从各种头部获取真实IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 获取直接连接的IP
        client_host = request.client.host if request.client else "unknown"
        return client_host
    
    async def get_access_statistics(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> dict:
        """获取访问统计信息"""
        try:
            from sqlalchemy import select, func
            
            query = select(AccessRecord)
            
            # 按用户ID过滤
            if user_id:
                query = query.where(AccessRecord.user_id == user_id)
            
            # 按时间范围过滤
            if start_time:
                query = query.where(AccessRecord.request_time >= start_time)
            if end_time:
                query = query.where(AccessRecord.request_time <= end_time)
            
            # 执行查询
            result = await self.db.execute(query)
            records = result.scalars().all()
            
            # 统计信息
            total_requests = len(records)
            successful_requests = len([r for r in records if 200 <= r.status_code < 300])
            failed_requests = len([r for r in records if r.status_code >= 400])
            
            # 按路径统计
            path_stats = {}
            for record in records:
                if record.path not in path_stats:
                    path_stats[record.path] = 0
                path_stats[record.path] += 1
            
            # 按状态码统计
            status_stats = {}
            for record in records:
                if record.status_code not in status_stats:
                    status_stats[record.status_code] = 0
                status_stats[record.status_code] += 1
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "path_statistics": path_stats,
                "status_statistics": status_stats
            }
            
        except Exception as e:
            logger.error(f"获取访问统计信息失败: {str(e)}")
            return {}


async def access_record_middleware(request: Request, call_next):
    """访问记录中间件处理函数"""
    start_time = time.time()
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 记录访问信息
        # 这里需要从依赖注入中获取数据库会话
        # 暂时跳过记录，实际应该实现完整的记录逻辑
        
        return response
        
    except Exception as e:
        logger.error(f"访问记录中间件处理失败: {str(e)}")
        raise 