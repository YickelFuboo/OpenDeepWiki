import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from src.models.repository import Repository, WarehouseStatus
from src.dto.repository_dto import CreateRepositoryDto, UpdateRepositoryDto, RepositoryInfoDto


class RepositoryService:
    """仓库管理服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_repository_by_id(self, repository_id: str) -> Optional[Repository]:
        """根据ID获取仓库"""
        result = await self.db.execute(
            select(Repository).where(Repository.id == repository_id)
        )
        return result.scalar_one_or_none()
    
    async def get_repository_list(
        self, 
        user_id: str, 
        page: int = 1, 
        page_size: int = 10, 
        keyword: Optional[str] = None
    ) -> tuple[List[Repository], int]:
        """获取用户仓库列表"""
        query = select(Repository).where(Repository.user_id == user_id)
        
        # 如果有关键词，则按名称或描述搜索
        if keyword:
            query = query.where(
                Repository.name.contains(keyword) | 
                Repository.description.contains(keyword) |
                Repository.organization_name.contains(keyword)
            )
        
        # 按创建时间降序排序
        query = query.order_by(Repository.created_at.desc())
        
        # 计算总数
        count_result = await self.db.execute(
            select(Repository).where(query.whereclause)
        )
        total = len(count_result.scalars().all())
        
        # 获取分页数据
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        repositories = result.scalars().all()
        
        return repositories, total
    
    async def create_repository(self, user_id: str, create_repository_dto: CreateRepositoryDto) -> Repository:
        """创建仓库"""
        # 检查仓库地址是否已存在
        existing_repo = await self.db.execute(
            select(Repository).where(Repository.address == create_repository_dto.address)
        )
        if existing_repo.scalar_one_or_none():
            raise ValueError("仓库地址已存在")
        
        # 创建仓库
        repository = Repository(
            id=str(uuid.uuid4()),
            user_id=user_id,
            organization_name=create_repository_dto.organization_name,
            name=create_repository_dto.name,
            description=create_repository_dto.description,
            address=create_repository_dto.address,
            git_username=create_repository_dto.git_username,
            git_password=create_repository_dto.git_password,
            email=create_repository_dto.email,
            type=create_repository_dto.type,
            branch=create_repository_dto.branch,
            status=WarehouseStatus.PENDING.value,
            prompt=create_repository_dto.prompt,
            created_at=datetime.utcnow()
        )
        
        self.db.add(repository)
        await self.db.commit()
        await self.db.refresh(repository)
        
        logger.info(f"Created repository: {repository.name} by user {user_id}")
        return repository
    
    async def update_repository(
        self, 
        repository_id: str, 
        user_id: str, 
        update_repository_dto: UpdateRepositoryDto
    ) -> Optional[Repository]:
        """更新仓库"""
        repository = await self.get_repository_by_id(repository_id)
        if not repository or repository.user_id != user_id:
            return None
        
        # 更新仓库信息
        if update_repository_dto.description is not None:
            repository.description = update_repository_dto.description
        if update_repository_dto.is_recommended is not None:
            repository.is_recommended = update_repository_dto.is_recommended
        if update_repository_dto.prompt is not None:
            repository.prompt = update_repository_dto.prompt
        
        repository.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(repository)
        
        logger.info(f"Updated repository: {repository.name}")
        return repository
    
    async def delete_repository(self, repository_id: str, user_id: str) -> bool:
        """删除仓库"""
        repository = await self.get_repository_by_id(repository_id)
        if not repository or repository.user_id != user_id:
            return False
        
        await self.db.execute(delete(Repository).where(Repository.id == repository_id))
        await self.db.commit()
        
        logger.info(f"Deleted repository: {repository.name}")
        return True
    
    def repository_to_dto(self, repository: Repository) -> RepositoryInfoDto:
        """将仓库实体转换为DTO"""
        return RepositoryInfoDto(
            id=repository.id,
            organization_name=repository.organization_name,
            name=repository.name,
            description=repository.description,
            address=repository.address,
            type=repository.type,
            branch=repository.branch,
            status=repository.status,
            error=repository.error,
            prompt=repository.prompt,
            version=repository.version,
            is_embedded=repository.is_embedded,
            is_recommended=repository.is_recommended,
            created_at=repository.created_at
        ) 