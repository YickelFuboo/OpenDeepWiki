import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from loguru import logger

from src.models.warehouse import Warehouse
from src.dto.warehouse_dto import CreateWarehouseDto, UpdateWarehouseDto, WarehouseInfoDto


class WarehouseService:
    """知识仓库基础服务 - 只包含基础CRUD操作"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_warehouse_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """根据ID获取知识仓库"""
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        return result.scalar_one_or_none()
    
    async def get_warehouse_list(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 10, 
        keyword: Optional[str] = None
    ) -> tuple[List[Warehouse], int]:
        """获取用户知识仓库列表"""
        query = select(Warehouse).where(Warehouse.user_id == user_id)
        
        # 如果有关键词，则按名称或描述搜索
        if keyword:
            query = query.where(
                Warehouse.name.contains(keyword) | 
                Warehouse.description.contains(keyword)
            )
        
        # 按创建时间降序排序
        query = query.order_by(Warehouse.created_at.desc())
        
        # 计算总数
        count_result = await self.db.execute(
            select(Warehouse).where(query.whereclause)
        )
        total = len(count_result.scalars().all())
        
        # 获取分页数据
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        warehouses = result.scalars().all()
        
        return warehouses, total
    
    async def create_warehouse(self, user_id: str, create_warehouse_dto: CreateWarehouseDto) -> Warehouse:
        """创建知识仓库"""
        # 检查仓库名称是否已存在
        existing_warehouse = await self.db.execute(
            select(Warehouse).where(
                Warehouse.name == create_warehouse_dto.name,
                Warehouse.user_id == user_id
            )
        )
        if existing_warehouse.scalar_one_or_none():
            raise ValueError("知识仓库名称已存在")
        
        # 创建知识仓库
        warehouse = Warehouse(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=create_warehouse_dto.name,
            description=create_warehouse_dto.description,
            type=create_warehouse_dto.type,
            config=create_warehouse_dto.config or "",
            settings=create_warehouse_dto.settings or "",
            is_public=create_warehouse_dto.is_public,
            created_at=datetime.utcnow()
        )
        
        self.db.add(warehouse)
        await self.db.commit()
        await self.db.refresh(warehouse)
        
        logger.info(f"Created warehouse: {warehouse.name} by user {user_id}")
        return warehouse
    
    async def update_warehouse(
        self, 
        warehouse_id: str, 
        user_id: str, 
        update_warehouse_dto: UpdateWarehouseDto
    ) -> Optional[Warehouse]:
        """更新知识仓库"""
        warehouse = await self.get_warehouse_by_id(warehouse_id)
        if not warehouse or warehouse.user_id != user_id:
            return None
        
        # 更新仓库信息
        if update_warehouse_dto.name is not None:
            warehouse.name = update_warehouse_dto.name
        if update_warehouse_dto.description is not None:
            warehouse.description = update_warehouse_dto.description
        if update_warehouse_dto.type is not None:
            warehouse.type = update_warehouse_dto.type
        if update_warehouse_dto.config is not None:
            warehouse.config = update_warehouse_dto.config
        if update_warehouse_dto.settings is not None:
            warehouse.settings = update_warehouse_dto.settings
        if update_warehouse_dto.is_public is not None:
            warehouse.is_public = update_warehouse_dto.is_public
        
        warehouse.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(warehouse)
        
        logger.info(f"Updated warehouse: {warehouse.name}")
        return warehouse
    
    async def delete_warehouse(self, warehouse_id: str, user_id: str) -> bool:
        """删除知识仓库"""
        warehouse = await self.get_warehouse_by_id(warehouse_id)
        if not warehouse or warehouse.user_id != user_id:
            return False
        
        await self.db.execute(delete(Warehouse).where(Warehouse.id == warehouse_id))
        await self.db.commit()
        
        logger.info(f"Deleted warehouse: {warehouse.name}")
        return True
    
    async def increment_view_count(self, warehouse_id: str) -> None:
        """增加仓库查看次数"""
        warehouse = await self.get_warehouse_by_id(warehouse_id)
        if warehouse:
            current_count = int(warehouse.view_count or "0")
            warehouse.view_count = str(current_count + 1)
            await self.db.commit()
    
    def warehouse_to_dto(self, warehouse: Warehouse) -> WarehouseInfoDto:
        """将知识仓库实体转换为DTO"""
        return WarehouseInfoDto(
            id=warehouse.id,
            name=warehouse.name,
            description=warehouse.description,
            type=warehouse.type,
            config=warehouse.config,
            settings=warehouse.settings,
            is_active=warehouse.is_active,
            is_public=warehouse.is_public,
            document_count=warehouse.document_count,
            view_count=warehouse.view_count,
            created_at=warehouse.created_at,
            updated_at=warehouse.updated_at
        ) 