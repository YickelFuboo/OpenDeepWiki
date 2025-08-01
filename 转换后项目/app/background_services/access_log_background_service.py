import asyncio
import json
from datetime import datetime
from typing import Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access_record import AccessRecord

class AccessLogQueue:
    """访问日志队列"""
    
    def __init__(self):
        self.queue = asyncio.Queue()
    
    async def put(self, log_data: dict):
        """添加日志到队列"""
        await self.queue.put(log_data)
    
    async def get(self):
        """从队列获取日志"""
        return await self.queue.get()
    
    def qsize(self):
        """获取队列大小"""
        return self.queue.qsize()


class AccessLogBackgroundService:
    """访问日志后台服务"""
    
    def __init__(self, db: AsyncSession, log_queue: AccessLogQueue):
        self.db = db
        self.log_queue = log_queue
        self.running = False
    
    async def start(self):
        """启动后台服务"""
        self.running = True
        logger.info("访问日志后台服务启动")
        
        while self.running:
            try:
                # 处理访问日志
                await self.process_access_logs()
                
                # 等待一段时间再处理下一批
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"访问日志后台服务发生错误: {e}")
                await asyncio.sleep(60)  # 1分钟后重试
        
        logger.info("访问日志后台服务停止")
    
    async def stop(self):
        """停止后台服务"""
        self.running = False
    
    async def process_access_logs(self):
        """处理访问日志"""
        try:
            # 处理队列中的所有日志
            while not self.log_queue.queue.empty():
                log_data = await self.log_queue.get()
                
                # 创建访问记录
                access_record = AccessRecord(
                    user_id=log_data.get("user_id", "anonymous"),
                    ip_address=log_data.get("ip_address", ""),
                    user_agent=log_data.get("user_agent", ""),
                    request_path=log_data.get("request_path", ""),
                    request_method=log_data.get("request_method", ""),
                    response_status=log_data.get("response_status", 0),
                    response_time=log_data.get("response_time", 0),
                    timestamp=datetime.utcnow()
                )
                
                self.db.add(access_record)
                
                # 每处理100条记录提交一次
                if self.db.dirty:
                    await self.db.commit()
                
                logger.debug(f"处理访问日志: {log_data.get('request_path', '')}")
                
        except Exception as e:
            logger.error(f"处理访问日志时发生错误: {e}")
            await self.db.rollback() 