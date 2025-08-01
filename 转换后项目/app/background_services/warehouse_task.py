import asyncio
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from src.models.warehouse import Warehouse, WarehouseStatus
from src.models.document import Document
from src.services.document_service import DocumentService
from src.services.git_service import GitService
from src.core.database import get_db


class WarehouseTask:
    """仓库任务后台服务"""
    
    def __init__(self, db: AsyncSession, document_service: DocumentService):
        self.db = db
        self.document_service = document_service
    
    async def execute_async(self, stopping_token: Optional[asyncio.CancelledError] = None):
        """执行仓库任务"""
        # 初始化延迟，避免服务启动时立即执行
        await asyncio.sleep(1)
        
        # 主循环：持续监控待处理的仓库
        while not stopping_token:
            try:
                # 查询待处理或处理中的仓库，优先处理正在处理中的仓库
                warehouse_result = await self.db.execute(
                    select(Warehouse).where(
                        Warehouse.status.in_([WarehouseStatus.Pending, WarehouseStatus.Processing])
                    ).order_by(Warehouse.status == WarehouseStatus.Processing.desc())
                )
                warehouse = warehouse_result.scalar_one_or_none()
                
                # 如果没有找到待处理的仓库，等待5秒后继续
                if not warehouse:
                    await asyncio.sleep(5)
                    continue
                
                # 创建追踪活动
                logger.info(f"开始处理仓库: {warehouse.id}, 名称: {warehouse.name}, 类型: {warehouse.type}, 地址: {warehouse.address}, 状态: {warehouse.status}")
                
                try:
                    document = None
                    
                    # 处理Git类型的仓库
                    if warehouse.type and warehouse.type.lower() == "git":
                        await self._process_git_warehouse(warehouse)
                        
                        # 检查是否已存在文档记录
                        document_result = await self.db.execute(
                            select(Document).where(Document.warehouse_id == warehouse.id)
                        )
                        document = document_result.scalar_one_or_none()
                        
                        if document:
                            logger.info(f"获取现有文档记录，文档ID: {document.id}")
                        else:
                            # 创建新的文档记录
                            document = Document(
                                id=str(uuid.uuid4()),
                                warehouse_id=warehouse.id,
                                created_at=datetime.utcnow(),
                                last_update=datetime.utcnow(),
                                git_path=warehouse.git_path,
                                status=WarehouseStatus.Pending
                            )
                            logger.info(f"创建文档记录，文档ID: {document.id}")
                            self.db.add(document)
                            await self.db.commit()
                    
                    # 处理文件类型的仓库
                    elif warehouse.type and warehouse.type.lower() == "file":
                        await self._process_file_warehouse(warehouse)
                        
                        # 检查是否已存在文档记录
                        document_result = await self.db.execute(
                            select(Document).where(Document.warehouse_id == warehouse.id)
                        )
                        document = document_result.scalar_one_or_none()
                        
                        if document:
                            logger.info(f"获取现有文档记录，文档ID: {document.id}")
                        else:
                            # 创建新的文档记录
                            document = Document(
                                id=str(uuid.uuid4()),
                                warehouse_id=warehouse.id,
                                created_at=datetime.utcnow(),
                                last_update=datetime.utcnow(),
                                git_path=warehouse.address,
                                status=WarehouseStatus.Pending
                            )
                            logger.info(f"创建文档记录，文档ID: {document.id}")
                            self.db.add(document)
                            await self.db.commit()
                    
                    # 处理不支持的仓库类型
                    else:
                        logger.error(f"不支持的仓库类型: {warehouse.type}")
                        
                        # 更新仓库状态为失败，并记录错误信息
                        await self.db.execute(
                            update(Warehouse)
                            .where(Warehouse.id == warehouse.id)
                            .values(
                                status=WarehouseStatus.Failed,
                                error="不支持的仓库类型"
                            )
                        )
                        await self.db.commit()
                        continue
                    
                    logger.info(f"数据库更改保存完成，开始处理文档")
                    
                    # 调用文档处理服务，进行AI分析、文档生成等处理
                    await self.document_service.handle_async(
                        document, warehouse, self.db, warehouse.address.replace(".git", "")
                    )
                    
                    logger.info(f"文档处理完成，仓库地址: {warehouse.address}")
                    
                    # 更新仓库状态为完成
                    await self.db.execute(
                        update(Warehouse)
                        .where(Warehouse.id == warehouse.id)
                        .values(
                            status=WarehouseStatus.Completed,
                            error=""
                        )
                    )
                    
                    # 更新文档的最后更新时间和状态
                    await self.db.execute(
                        update(Document)
                        .where(Document.id == document.id)
                        .values(
                            last_update=datetime.utcnow(),
                            status=WarehouseStatus.Completed
                        )
                    )
                    
                    await self.db.commit()
                    
                    logger.info(f"仓库状态更新为完成，仓库地址: {warehouse.address}")
                    
                except Exception as e:
                    logger.error(f"处理仓库时发生错误: {e}")
                    
                    # 更新仓库状态为失败，并记录详细的错误信息
                    await self.db.execute(
                        update(Warehouse)
                        .where(Warehouse.id == warehouse.id)
                        .values(
                            status=WarehouseStatus.Failed,
                            error=str(e)
                        )
                    )
                    await self.db.commit()
                    
                    # 等待5秒后继续，避免频繁重试
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"仓库任务主循环发生错误: {e}")
                await asyncio.sleep(5)
    
    async def _process_git_warehouse(self, warehouse: Warehouse):
        """处理Git类型的仓库"""
        logger.info(f"开始拉取仓库: {warehouse.address}")
        
        # 克隆Git仓库
        git_info = await GitService.clone_repository(
            warehouse.address,
            warehouse.git_user_name or "",
            warehouse.git_password or "",
            warehouse.branch
        )
        
        logger.info(f"仓库拉取完成: {git_info.repository_name}, 分支: {git_info.branch_name}")
        
        # 更新仓库信息到数据库
        await self.db.execute(
            update(Warehouse)
            .where(Warehouse.id == warehouse.id)
            .values(
                name=git_info.repository_name,
                branch=git_info.branch_name,
                version=git_info.version,
                status=WarehouseStatus.Processing,
                organization_name=git_info.organization,
                git_path=git_info.local_path
            )
        )
        await self.db.commit()
        
        logger.info(f"更新仓库信息到数据库完成，仓库ID: {warehouse.id}")
    
    async def _process_file_warehouse(self, warehouse: Warehouse):
        """处理文件类型的仓库"""
        logger.info(f"开始处理文件仓库: {warehouse.address}")
        
        # 更新仓库状态为处理中
        await self.db.execute(
            update(Warehouse)
            .where(Warehouse.id == warehouse.id)
            .values(status=WarehouseStatus.Processing)
        )
        await self.db.commit()
        
        logger.info(f"更新仓库信息到数据库完成，仓库ID: {warehouse.id}")
    
    async def start(self):
        """启动仓库任务"""
        try:
            await self.execute_async()
        except Exception as e:
            logger.error(f"仓库任务启动失败: {e}")
            raise 