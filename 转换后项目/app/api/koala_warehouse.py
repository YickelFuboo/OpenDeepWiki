from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.koala_warehouse.warehouse_classify import WarehouseClassify, ClassifyType
from src.koala_warehouse.mini_map_service import MiniMapService
from src.koala_warehouse.overview.overview_service import OverviewService
from src.koala_warehouse.generate_think_catalogue.generate_think_catalogue_service import GenerateThinkCatalogueService
from src.services.kernel_factory import KernelFactory
from src.models.user import User
from src.models.warehouse import Warehouse
from src.conf.settings import settings

koala_warehouse_router = APIRouter()


@koala_warehouse_router.post("/classify")
@require_user()
async def classify_warehouse(
    catalog: str,
    readme: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """仓库分类"""
    try:
        classify_service = WarehouseClassify()
        
        # 创建内核
        kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key,
            "",
            settings.openai.chat_model
        )
        
        # 执行分类
        classify_type = await classify_service.classify_async(kernel, catalog, readme)
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "classify_type": classify_type.value if classify_type else None,
                "classify_name": classify_type.name if classify_type else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"仓库分类失败: {str(e)}"
        )


@koala_warehouse_router.post("/generate-mini-map")
@require_user()
async def generate_mini_map(
    catalogue: str,
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成知识图谱"""
    try:
        # 获取仓库信息
        from sqlalchemy import select
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
        )
        warehouse = warehouse_result.scalar_one_or_none()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        mini_map_service = MiniMapService()
        result = await mini_map_service.generate_mini_map(catalogue, warehouse, "")
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "title": result.title,
                "url": result.url,
                "nodes": [
                    {
                        "title": node.title,
                        "url": node.url,
                        "nodes": node.nodes
                    }
                    for node in result.nodes
                ]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成知识图谱失败: {str(e)}"
        )


@koala_warehouse_router.post("/generate-overview")
@require_user()
async def generate_project_overview(
    catalog: str,
    git_repository: str,
    branch: str,
    readme: str,
    classify_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成项目概述"""
    try:
        # 创建内核
        kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key,
            "",
            settings.openai.chat_model
        )
        
        # 解析分类类型
        classify = None
        if classify_type:
            try:
                classify = ClassifyType(classify_type)
            except ValueError:
                pass
        
        overview_service = OverviewService()
        overview = await overview_service.generate_project_overview(
            kernel, catalog, git_repository, branch, readme, classify
        )
        
        return {
            "message": "success",
            "code": 200,
            "data": {
                "overview": overview
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成项目概述失败: {str(e)}"
        )


@koala_warehouse_router.post("/generate-catalogue")
@require_user()
async def generate_catalogue(
    path: str,
    git_repository: str,
    catalogue: str,
    warehouse_id: str,
    classify_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """生成文档目录"""
    try:
        # 获取仓库信息
        from sqlalchemy import select
        warehouse_result = await db.execute(
            select(Warehouse).where(Warehouse.id == warehouse_id)
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
        
        generate_service = GenerateThinkCatalogueService()
        result = await generate_service.generate_catalogue(
            path, git_repository, catalogue, warehouse, classify
        )
        
        if result:
            return {
                "message": "success",
                "code": 200,
                "data": {
                    "items": result.items,
                    "delete_id": result.delete_id
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="生成目录失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成文档目录失败: {str(e)}"
        ) 