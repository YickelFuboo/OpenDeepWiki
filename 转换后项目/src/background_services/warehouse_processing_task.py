import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from src.models.warehouse import Warehouse, WarehouseStatus
from src.models.document import Document
from src.services.statistics_service import StatisticsService
from src.core.config import settings


class WarehouseProcessingTask:
    """仓库处理任务"""
    
    def __init__(self, db: AsyncSession, statistics_service: StatisticsService):
        self.db = db
        self.statistics_service = statistics_service
    
    async def execute_async(self, stopping_token: Optional[asyncio.CancelledError] = None):
        """执行仓库处理任务"""
        await asyncio.sleep(1)
        
        # 检查是否启用增量更新
        if not settings.document.enable_incremental_update:
            logger.warning("增量更新未启用，跳过增量更新任务")
            return
        
        # 读取环境变量，获取更新间隔
        update_interval = int(os.getenv("UPDATE_INTERVAL", "5"))
        
        while not stopping_token:
            try:
                # 1. 读取现有的仓库状态=2
                warehouse_result = await self.db.execute(
                    select(Warehouse).where(Warehouse.status == WarehouseStatus.Completed)
                )
                warehouse = warehouse_result.scalar_one_or_none()
                
                if not warehouse:
                    # 如果没有仓库，等待一段时间后重试
                    await asyncio.sleep(60)
                    continue
                
                # 查找超过指定天数没更新的文档
                cutoff_date = datetime.utcnow() - timedelta(days=update_interval)
                documents_result = await self.db.execute(
                    select(Document).where(
                        Document.warehouse_id == warehouse.id,
                        Document.last_update < cutoff_date
                    )
                )
                documents = documents_result.scalars().all()
                
                warehouse_ids = [doc.warehouse_id for doc in documents]
                
                # 获取需要更新的仓库
                warehouse_result = await self.db.execute(
                    select(Warehouse).where(Warehouse.id.in_(warehouse_ids))
                )
                warehouse = warehouse_result.scalar_one_or_none()
                
                if not warehouse:
                    await asyncio.sleep(60)
                    continue
                
                document = next((doc for doc in documents if doc.warehouse_id == warehouse.id), None)
                
                if document:
                    commit_id = await self._handle_analyse_async(warehouse, document)
                    
                    if not commit_id:
                        # 更新文档记录
                        await self.db.execute(
                            update(Document)
                            .where(Document.warehouse_id == warehouse.id)
                            .values(last_update=datetime.utcnow())
                        )
                        await self.db.commit()
                        continue
                    
                    # 更新文档记录
                    await self.db.execute(
                        update(Document)
                        .where(Document.warehouse_id == warehouse.id)
                        .values(last_update=datetime.utcnow())
                    )
                    
                    # 更新仓库版本
                    await self.db.execute(
                        update(Warehouse)
                        .where(Warehouse.id == warehouse.id)
                        .values(version=commit_id)
                    )
                    
                    await self.db.commit()
                    
            except Exception as e:
                logger.error(f"处理仓库失败: {e}")
                await asyncio.sleep(60)
    
    async def _handle_analyse_async(self, warehouse: Warehouse, document: Document) -> Optional[str]:
        """处理仓库分析"""
        try:
            logger.info(f"开始分析仓库: {warehouse.name}")
            
            # 这里实现仓库分析逻辑
            # 可以调用Git服务获取最新的commit ID
            # 或者调用其他分析服务
            
            # 示例：返回一个模拟的commit ID
            return f"commit_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
        except Exception as e:
            logger.error(f"分析仓库失败: {e}")
            return None
    
    async def start(self):
        """启动仓库处理任务"""
        try:
            await self.execute_async()
        except Exception as e:
            logger.error(f"仓库处理任务启动失败: {e}")
            raise 