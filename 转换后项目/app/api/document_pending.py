from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.koala_warehouse.document_pending.document_pending_service import DocumentPendingService
from src.services.kernel_factory import KernelFactory
from src.koala_warehouse.warehouse_classify import ClassifyType
from src.models.user import User
from src.models.warehouse import Warehouse
from src.models.document_catalog import DocumentCatalog
from src.conf.settings import settings

document_pending_router = APIRouter()


@document_pending_router.post("/process/{warehouse_id}")
@require_user()
async def process_pending_documents(
    warehouse_id: str,
    background_tasks: BackgroundTasks,
    classify_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """处理待处理文档"""
    try:
        # 获取仓库信息
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        # 获取待处理的文档目录
        documents_result = await db.execute(
            select(DocumentCatalog).where(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_completed == False,
                DocumentCatalog.is_deleted == False
            )
        )
        documents = documents_result.scalars().all()
        
        if not documents:
            return {
                "message": "没有待处理的文档",
                "code": 200,
                "data": {
                    "warehouse_id": warehouse_id,
                    "pending_count": 0
                }
            }
        
        # 解析分类类型
        classify = None
        if classify_type:
            try:
                classify = ClassifyType(classify_type)
            except ValueError:
                pass
        
        # 创建内核
        kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key,
            "",
            settings.openai.chat_model
        )
        
        # 创建文档待处理服务
        pending_service = DocumentPendingService()
        
        # 在后台任务中处理
        background_tasks.add_task(
            pending_service.handle_pending_documents_async,
            documents,
            kernel,
            "",  # catalogue - 需要从仓库获取
            warehouse.address,
            warehouse,
            "",  # path - 需要从仓库获取
            db,
            classify
        )
        
        return {
            "message": "文档处理任务已启动",
            "code": 200,
            "data": {
                "warehouse_id": warehouse_id,
                "pending_count": len(documents),
                "status": "processing"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动文档处理失败: {str(e)}"
        )


@document_pending_router.get("/status/{warehouse_id}")
@require_user()
async def get_pending_status(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取待处理文档状态"""
    try:
        # 获取待处理的文档数量
        pending_result = await db.execute(
            select(DocumentCatalog).where(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_completed == False,
                DocumentCatalog.is_deleted == False
            )
        )
        pending_documents = pending_result.scalars().all()
        
        # 获取已完成的文档数量
        completed_result = await db.execute(
            select(DocumentCatalog).where(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_completed == True,
                DocumentCatalog.is_deleted == False
            )
        )
        completed_documents = completed_result.scalars().all()
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "warehouse_id": warehouse_id,
                "pending_count": len(pending_documents),
                "completed_count": len(completed_documents),
                "total_count": len(pending_documents) + len(completed_documents)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取待处理状态失败: {str(e)}"
        )


@document_pending_router.post("/retry/{document_id}")
@require_user()
async def retry_document_processing(
    document_id: str,
    classify_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重试文档处理"""
    try:
        # 获取文档目录
        document_result = await db.execute(
            select(DocumentCatalog).where(DocumentCatalog.id == document_id)
        )
        document = document_result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 获取仓库信息
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.id == document.warehouse_id)
        )
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        # 解析分类类型
        classify = None
        if classify_type:
            try:
                classify = ClassifyType(classify_type)
            except ValueError:
                pass
        
        # 创建内核
        kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key,
            "",
            settings.openai.chat_model
        )
        
        # 创建文档待处理服务
        pending_service = DocumentPendingService()
        
        # 处理单个文档
        catalog, file_item, files = await pending_service._process_document_async(
            document,
            kernel,
            "",  # catalogue - 需要从仓库获取
            warehouse.address,
            warehouse.branch,
            "",  # path - 需要从仓库获取
            None,  # semaphore
            classify
        )
        
        if file_item:
            # 更新文档状态
            await db.execute(
                update(DocumentCatalog)
                .where(DocumentCatalog.id == document.id)
                .values(is_completed=True)
            )
            
            # 保存文件项
            db.add(file_item)
            await db.commit()
            
            return {
                "message": "文档处理成功",
                "code": 200,
                "data": {
                    "document_id": document_id,
                    "status": "completed"
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文档处理失败"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重试文档处理失败: {str(e)}"
        ) 