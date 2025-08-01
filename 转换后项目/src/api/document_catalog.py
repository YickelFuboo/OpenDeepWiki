from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.auth import get_current_active_user, require_user
from src.dto.document_catalog_dto import (
    DocumentCatalogResponse, UpdateCatalogRequest, UpdateDocumentContentRequest,
    DocumentFileItemResponse
)
from src.services.document_catalog_service import DocumentCatalogService
from src.models.user import User

document_catalog_router = APIRouter()


@document_catalog_router.get("/", response_model=DocumentCatalogResponse)
@require_user()
async def get_document_catalogs(
    organization_name: str = Query(..., description="组织名称"),
    name: str = Query(..., description="仓库名称"),
    branch: Optional[str] = Query(None, description="分支名称"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取目录列表"""
    document_catalog_service = DocumentCatalogService(db)
    
    try:
        return await document_catalog_service.get_document_catalogs(organization_name, name, branch)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录列表失败: {str(e)}"
        )


@document_catalog_router.get("/document")
@require_user()
async def get_document_by_id(
    owner: str = Query(..., description="所有者"),
    name: str = Query(..., description="仓库名称"),
    path: str = Query(..., description="路径"),
    branch: Optional[str] = Query(None, description="分支名称"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据目录id获取文件"""
    document_catalog_service = DocumentCatalogService(db)
    
    try:
        result = await document_catalog_service.get_document_by_id(owner, name, path, branch)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档失败: {str(e)}"
        )


@document_catalog_router.put("/catalog")
@require_user()
async def update_catalog(
    request: UpdateCatalogRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新目录"""
    document_catalog_service = DocumentCatalogService(db)
    
    try:
        success = await document_catalog_service.update_catalog(request)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
        return {"message": "更新成功", "code": 200}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新目录失败: {str(e)}"
        )


@document_catalog_router.put("/content")
@require_user()
async def update_document_content(
    request: UpdateDocumentContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新文档内容"""
    document_catalog_service = DocumentCatalogService(db)
    
    try:
        success = await document_catalog_service.update_document_content(request)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        return {"message": "更新成功", "code": 200}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档内容失败: {str(e)}"
        ) 