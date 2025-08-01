from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.core.database import get_db
from src.services.user_service import UserService
from src.services.auth_service import AuthService
from src.services.repository_service import RepositoryService
from src.services.warehouse_service import WarehouseService
from src.services.statistics_service import StatisticsService
from src.services.document_service import DocumentService
from src.services.ai_service import AIService
from src.services.menu_service import MenuService
from src.services.background_services import BackgroundServices
from src.services.kernel_factory import KernelFactory
from src.services.prompt_service import PromptService


# 数据库会话依赖
async def get_db_session() -> Generator[AsyncSession, None, None]:
    async with get_db() as session:
        yield session


# 服务依赖
def get_user_service(db: AsyncSession = Depends(get_db_session)) -> UserService:
    return UserService(db)


def get_auth_service(db: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(db)


def get_repository_service(db: AsyncSession = Depends(get_db_session)) -> RepositoryService:
    return RepositoryService(db)


def get_warehouse_service(db: AsyncSession = Depends(get_db_session)) -> WarehouseService:
    return WarehouseService(db)


def get_statistics_service(db: AsyncSession = Depends(get_db_session)) -> StatisticsService:
    return StatisticsService(db)


def get_document_service(db: AsyncSession = Depends(get_db_session)) -> DocumentService:
    return DocumentService(db)


def get_ai_service(db: AsyncSession = Depends(get_db_session)) -> AIService:
    return AIService(db)


def get_menu_service(user_service: UserService = Depends(get_user_service)) -> MenuService:
    return MenuService(user_service)


def get_background_services(db: AsyncSession = Depends(get_db_session)) -> BackgroundServices:
    return BackgroundServices(db)


def get_kernel_factory() -> KernelFactory:
    return KernelFactory()


def get_prompt_service() -> PromptService:
    return PromptService() 