from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.services.fine_tuning_service import FineTuningService
from src.infrastructure.user_context import UserContext
from src.dto.fine_tuning_dto import (
    CreateDatasetInput, UpdateDatasetInput, CreateTaskInput, StartTaskInput,
    TrainingDatasetResponse, FineTuningTaskResponse
)
from src.models.user import User

fine_tuning_router = APIRouter()


@fine_tuning_router.post("/datasets", response_model=TrainingDatasetResponse)
@require_user()
async def create_dataset(
    input: CreateDatasetInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建训练数据集"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        dataset = await service.create_dataset(
            input.warehouse_id,
            input.name,
            input.endpoint,
            input.api_key,
            input.prompt,
            input.model
        )
        
        return TrainingDatasetResponse(
            id=dataset.id,
            warehouse_id=dataset.warehouse_id,
            user_id=dataset.user_id,
            name=dataset.name,
            endpoint=dataset.endpoint,
            model=dataset.model,
            api_key=dataset.api_key,
            prompt=dataset.prompt,
            status=dataset.status,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建训练数据集失败: {str(e)}"
        )


@fine_tuning_router.get("/datasets", response_model=List[TrainingDatasetResponse])
@require_user()
async def get_datasets(
    warehouse_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取训练数据集列表"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        datasets = await service.get_datasets(warehouse_id)
        
        return [
            TrainingDatasetResponse(
                id=dataset.id,
                warehouse_id=dataset.warehouse_id,
                user_id=dataset.user_id,
                name=dataset.name,
                endpoint=dataset.endpoint,
                model=dataset.model,
                api_key=dataset.api_key,
                prompt=dataset.prompt,
                status=dataset.status,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at
            )
            for dataset in datasets
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练数据集列表失败: {str(e)}"
        )


@fine_tuning_router.get("/datasets/{dataset_id}", response_model=TrainingDatasetResponse)
@require_user()
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取训练数据集详情"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        dataset = await service.get_dataset(dataset_id)
        
        return TrainingDatasetResponse(
            id=dataset.id,
            warehouse_id=dataset.warehouse_id,
            user_id=dataset.user_id,
            name=dataset.name,
            endpoint=dataset.endpoint,
            model=dataset.model,
            api_key=dataset.api_key,
            prompt=dataset.prompt,
            status=dataset.status,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取训练数据集详情失败: {str(e)}"
        )


@fine_tuning_router.put("/datasets/{dataset_id}", response_model=TrainingDatasetResponse)
@require_user()
async def update_dataset(
    dataset_id: str,
    input: UpdateDatasetInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新训练数据集"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        dataset = await service.update_dataset(
            dataset_id,
            input.name,
            input.endpoint,
            input.api_key,
            input.prompt
        )
        
        return TrainingDatasetResponse(
            id=dataset.id,
            warehouse_id=dataset.warehouse_id,
            user_id=dataset.user_id,
            name=dataset.name,
            endpoint=dataset.endpoint,
            model=dataset.model,
            api_key=dataset.api_key,
            prompt=dataset.prompt,
            status=dataset.status,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新训练数据集失败: {str(e)}"
        )


@fine_tuning_router.delete("/datasets/{dataset_id}")
@require_user()
async def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除训练数据集"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        await service.delete_dataset(dataset_id)
        
        return {
            "message": "删除训练数据集成功",
            "code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除训练数据集失败: {str(e)}"
        )


@fine_tuning_router.post("/tasks", response_model=FineTuningTaskResponse)
@require_user()
async def create_task(
    input: CreateTaskInput,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建微调任务"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        task = await service.create_task(
            input.training_dataset_id,
            input.document_catalog_id,
            input.name,
            input.description
        )
        
        return FineTuningTaskResponse(
            id=task.id,
            warehouse_id=task.warehouse_id,
            training_dataset_id=task.training_dataset_id,
            document_catalog_id=task.document_catalog_id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            status=task.status,
            started_at=task.started_at,
            completed_at=task.completed_at,
            dataset=task.dataset,
            original_dataset=task.original_dataset,
            error=task.error,
            created_at=task.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建微调任务失败: {str(e)}"
        )


@fine_tuning_router.get("/tasks", response_model=List[FineTuningTaskResponse])
@require_user()
async def get_tasks(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务列表"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        tasks = await service.get_tasks(warehouse_id)
        
        return [
            FineTuningTaskResponse(
                id=task.id,
                warehouse_id=task.warehouse_id,
                training_dataset_id=task.training_dataset_id,
                document_catalog_id=task.document_catalog_id,
                user_id=task.user_id,
                name=task.name,
                description=task.description,
                status=task.status,
                started_at=task.started_at,
                completed_at=task.completed_at,
                dataset=task.dataset,
                original_dataset=task.original_dataset,
                error=task.error,
                created_at=task.created_at
            )
            for task in tasks
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取微调任务列表失败: {str(e)}"
        )


@fine_tuning_router.get("/tasks/{task_id}", response_model=FineTuningTaskResponse)
@require_user()
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务详情"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        task = await service.get_task(task_id)
        
        return FineTuningTaskResponse(
            id=task.id,
            warehouse_id=task.warehouse_id,
            training_dataset_id=task.training_dataset_id,
            document_catalog_id=task.document_catalog_id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            status=task.status,
            started_at=task.started_at,
            completed_at=task.completed_at,
            dataset=task.dataset,
            original_dataset=task.original_dataset,
            error=task.error,
            created_at=task.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取微调任务详情失败: {str(e)}"
        )


@fine_tuning_router.post("/tasks/{task_id}/start")
@require_user()
async def start_task(
    task_id: str,
    input: StartTaskInput,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """启动微调任务"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        return await service.start_task(task_id, input.prompt)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动微调任务失败: {str(e)}"
        )


@fine_tuning_router.post("/tasks/{task_id}/cancel", response_model=FineTuningTaskResponse)
@require_user()
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """取消微调任务"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        task = await service.cancel_task(task_id)
        
        return FineTuningTaskResponse(
            id=task.id,
            warehouse_id=task.warehouse_id,
            training_dataset_id=task.training_dataset_id,
            document_catalog_id=task.document_catalog_id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            status=task.status,
            started_at=task.started_at,
            completed_at=task.completed_at,
            dataset=task.dataset,
            original_dataset=task.original_dataset,
            error=task.error,
            created_at=task.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消微调任务失败: {str(e)}"
        )


@fine_tuning_router.delete("/tasks/{task_id}")
@require_user()
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除微调任务"""
    try:
        user_context = UserContext(current_user.id, current_user.username, current_user.email, current_user.role)
        service = FineTuningService(db, user_context)
        
        await service.delete_task(task_id)
        
        return {
            "message": "删除微调任务成功",
            "code": 200
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除微调任务失败: {str(e)}"
        ) 