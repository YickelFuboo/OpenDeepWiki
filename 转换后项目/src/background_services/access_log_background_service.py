import asyncio
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.services.statistics_service import StatisticsService


@dataclass
class AccessLogEntry:
    """访问日志条目"""
    resource_type: str
    resource_id: str
    user_id: str
    ip_address: str
    user_agent: str
    path: str
    method: str
    status_code: int
    response_time: float


class AccessLogQueue:
    """访问日志队列"""
    
    def __init__(self):
        self._queue = asyncio.Queue()
    
    async def enqueue_async(self, log_entry: AccessLogEntry):
        """入队"""
        await self._queue.put(log_entry)
    
    async def dequeue_async(self, cancellation_token: Optional[asyncio.CancelledError] = None):
        """出队"""
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    @property
    def count(self) -> int:
        """队列长度"""
        return self._queue.qsize()


class AccessLogBackgroundService:
    """访问日志后台处理服务"""
    
    def __init__(self, db: AsyncSession, log_queue: AccessLogQueue, statistics_service: StatisticsService):
        self.db = db
        self.log_queue = log_queue
        self.statistics_service = statistics_service
    
    async def execute_async(self, stopping_token: Optional[asyncio.CancelledError] = None):
        """执行访问日志处理任务"""
        logger.info("访问日志后台处理服务已启动")
        
        while not stopping_token:
            try:
                log_entry = await self.log_queue.dequeue_async(stopping_token)
                if log_entry:
                    await self._process_log_entry_async(log_entry)
            except asyncio.CancelledError:
                # 正常的取消操作，退出循环
                break
            except Exception as e:
                logger.error(f"处理访问日志时发生错误: {e}")
                
                # 发生错误时等待一段时间再继续
                try:
                    await asyncio.sleep(5)
                except asyncio.CancelledError:
                    break
        
        logger.info("访问日志后台处理服务已停止")
    
    async def _process_log_entry_async(self, log_entry: AccessLogEntry):
        """处理访问日志条目"""
        try:
            await self.statistics_service.record_access_async(
                resource_type=log_entry.resource_type,
                resource_id=log_entry.resource_id,
                user_id=log_entry.user_id,
                ip_address=log_entry.ip_address,
                user_agent=log_entry.user_agent,
                path=log_entry.path,
                method=log_entry.method,
                status_code=log_entry.status_code,
                response_time=log_entry.response_time
            )
        except Exception as e:
            logger.error(f"处理访问日志条目失败: {log_entry.resource_type}/{log_entry.resource_id}, Path: {log_entry.path}, Error: {e}")
    
    async def stop_async(self, cancellation_token: Optional[asyncio.CancelledError] = None):
        """停止访问日志后台服务"""
        logger.info("正在停止访问日志后台处理服务...")
        
        # 处理队列中剩余的日志条目
        remaining_count = self.log_queue.count
        if remaining_count > 0:
            logger.info(f"处理队列中剩余的 {remaining_count} 条访问日志")
            
            timeout = 30  # 最多等待30秒
            end_time = datetime.utcnow().timestamp() + timeout
            
            while self.log_queue.count > 0 and datetime.utcnow().timestamp() < end_time:
                try:
                    log_entry = await self.log_queue.dequeue_async(cancellation_token)
                    if log_entry:
                        await self._process_log_entry_async(log_entry)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"停止时处理访问日志失败: {e}")
    
    async def start(self):
        """启动访问日志后台服务"""
        try:
            await self.execute_async()
        except Exception as e:
            logger.error(f"访问日志后台服务启动失败: {e}")
            raise 