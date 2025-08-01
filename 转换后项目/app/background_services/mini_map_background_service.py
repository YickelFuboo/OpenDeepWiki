import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from src.models.warehouse import Warehouse, WarehouseStatus
from src.models.document import Document
from src.koala_warehouse.mini_map_service import MiniMapService


class MiniMapBackgroundService:
    """思维导图服务生成"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def execute_async(self, stopping_token: Optional[asyncio.CancelledError] = None):
        """执行迷你地图生成任务"""
        await asyncio.sleep(1)  # 等待服务启动完成
        
        while not stopping_token:
            try:
                # 获取已存在的迷你地图仓库ID列表
                # 注意：这里需要根据实际的MiniMap模型调整
                existing_mini_map_ids = []  # 这里需要从数据库查询
                
                # 查询需要生成知识图谱的仓库
                warehouse_result = await self.db.execute(
                    select(Warehouse).where(
                        Warehouse.status == WarehouseStatus.Completed
                        # 这里需要添加排除已存在迷你地图的条件
                    ).order_by(Warehouse.created_at)
                )
                warehouse = warehouse_result.scalar_one_or_none()
                
                if not warehouse:
                    await asyncio.sleep(10)  # 等待10秒后重试
                    continue
                
                logger.info(f"开始生成知识图谱，仓库: {warehouse.name}")
                
                try:
                    logger.info(f"开始处理仓库 {warehouse.name}")
                    
                    # 获取仓库对应的文档
                    document_result = await self.db.execute(
                        select(Document).where(Document.warehouse_id == warehouse.id)
                    )
                    document = document_result.scalar_one_or_none()
                    
                    if not document:
                        logger.warning(f"仓库 {warehouse.name} 没有对应的文档记录")
                        continue
                    
                    # 生成迷你地图
                    mini_map = await MiniMapService().generate_mini_map(
                        warehouse.optimized_directory_structure or "",
                        warehouse,
                        document.git_path
                    )
                    
                    if mini_map:
                        # 保存迷你地图到数据库
                        # 注意：这里需要根据实际的MiniMap模型调整
                        mini_map_data = {
                            "id": str(uuid.uuid4()),
                            "warehouse_id": warehouse.id,
                            "value": json.dumps(mini_map, ensure_ascii=False),
                            "created_at": datetime.utcnow()
                        }
                        
                        # 这里需要实际的MiniMap模型来保存数据
                        # await self.db.add(MiniMap(**mini_map_data))
                        # await self.db.commit()
                        
                        logger.info(f"仓库 {warehouse.name} 的知识图谱生成成功")
                    else:
                        logger.warning(f"仓库 {warehouse.name} 的知识图谱生成失败")
                        
                except Exception as e:
                    logger.error(f"处理仓库 {warehouse.name} 时发生异常: {e}")
                    
            except Exception as e:
                await asyncio.sleep(10)  # 等待10秒后重试
                logger.error(f"MiniMapBackgroundService 执行异常: {e}")
    
    async def start(self):
        """启动迷你地图后台服务"""
        try:
            await self.execute_async()
        except Exception as e:
            logger.error(f"迷你地图后台服务启动失败: {e}")
            raise 