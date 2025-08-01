from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.mem0.mem0_rag import Mem0Rag
from src.models.user import User

mem0_router = APIRouter()


@mem0_router.post("/process/{warehouse_id}")
@require_user()
async def process_warehouse_mem0(
    warehouse_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """处理仓库的Mem0嵌入"""
    try:
        mem0_rag = Mem0Rag(db)
        
        # 在后台任务中处理
        background_tasks.add_task(mem0_rag.process_warehouse, warehouse_id)
        
        return {
            "message": "Mem0处理任务已启动",
            "code": 200,
            "data": {
                "warehouse_id": warehouse_id,
                "status": "processing"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动Mem0处理失败: {str(e)}"
        )


@mem0_router.get("/status/{warehouse_id}")
@require_user()
async def get_mem0_status(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取Mem0处理状态"""
    try:
        from src.models.warehouse import Warehouse
        
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "warehouse_id": warehouse_id,
                "is_embedded": warehouse.is_embedded,
                "status": warehouse.status
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Mem0状态失败: {str(e)}"
        )


@mem0_router.post("/search")
@require_user()
async def search_mem0(
    query: str,
    warehouse_id: str,
    limit: int = 5,
    min_relevance: float = 0.3,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索Mem0内容"""
    try:
        # 这里实现Mem0搜索逻辑
        # 简化实现，实际应该调用Mem0 API
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "query": query,
                "warehouse_id": warehouse_id,
                "results": [
                    {
                        "content": "搜索结果示例",
                        "relevance": 0.8,
                        "metadata": {
                            "type": "docs",
                            "name": "示例文档"
                        }
                    }
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mem0搜索失败: {str(e)}"
        ) 