from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db
from app.services.repository_service import RepositoryService
from app.services.warehouse_service import WarehouseService
from app.services.document_service import DocumentService
from app.services.ai_service import AIService
from app.services.background_services import BackgroundServices
from app.services.kernel_factory import KernelFactory
from app.services.prompt_service import PromptService


# 数据库会话依赖
async def get_db_session() -> Generator[AsyncSession, None, None]:
    async with get_db() as session:
        yield session


# 服务依赖
def get_repository_service(db: AsyncSession = Depends(get_db_session)) -> RepositoryService:
    return RepositoryService(db)


def get_warehouse_service(db: AsyncSession = Depends(get_db_session)) -> WarehouseService:
    return WarehouseService(db)


def get_document_service(db: AsyncSession = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db)


def get_ai_service(db: AsyncSession = Depends(get_db_session)) -> AIService:
    return AIService(db)


def get_background_services(db: AsyncSession = Depends(get_db_session)) -> BackgroundServices:
    return BackgroundServices(db)


def get_kernel_factory() -> KernelFactory:
    return KernelFactory()


def get_prompt_service() -> PromptService:
    return PromptService() 