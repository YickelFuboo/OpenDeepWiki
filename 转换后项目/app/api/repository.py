from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.simple_auth import get_current_active_user, require_user, SimpleUserContext
from app.dto.repository_dto import CreateRepositoryDto, UpdateRepositoryDto, RepositoryInfoDto
from app.services.repository_service import RepositoryService

repository_router = APIRouter()


@repository_router.get("/list", response_model=List[RepositoryInfoDto])
@require_user()
async def get_repository_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str = Query(None, description="搜索关键词"),
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库列表"""
    repository_service = RepositoryService(db)
    repositories, total = await repository_service.get_repository_list(
        current_user.id, page, page_size, keyword
    )
    
    return [repository_service.repository_to_dto(repo) for repo in repositories]


@repository_router.post("/create", response_model=RepositoryInfoDto)
@require_user()
async def create_repository(
    create_repository_dto: CreateRepositoryDto,
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建仓库"""
    repository_service = RepositoryService(db)
    
    try:
        repository = await repository_service.create_repository(
            current_user.id, create_repository_dto
        )
        return repository_service.repository_to_dto(repository)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@repository_router.get("/{repository_id}", response_model=RepositoryInfoDto)
@require_user()
async def get_repository(
    repository_id: str,
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库详情"""
    repository_service = RepositoryService(db)
    
    repository = await repository_service.get_repository_by_id(repository_id)
    if not repository or repository.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="仓库不存在"
        )
    
    return repository_service.repository_to_dto(repository)


@repository_router.put("/{repository_id}", response_model=RepositoryInfoDto)
@require_user()
async def update_repository(
    repository_id: str,
    update_repository_dto: UpdateRepositoryDto,
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新仓库"""
    repository_service = RepositoryService(db)
    
    try:
        repository = await repository_service.update_repository(
            repository_id, current_user.id, update_repository_dto
        )
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        return repository_service.repository_to_dto(repository)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@repository_router.delete("/{repository_id}")
@require_user()
async def delete_repository(
    repository_id: str,
    current_user: SimpleUserContext = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除仓库"""
    repository_service = RepositoryService(db)
    
    success = await repository_service.delete_repository(repository_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="仓库不存在"
        )
    
    return {"message": "仓库删除成功"} 