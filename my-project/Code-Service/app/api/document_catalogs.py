from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from sqlalchemy import and_, or_

from app.db.connection import get_db
from services.document_catalog_service import DocumentCatalogService
from schemas.document import (
    UpdateCatalogRequest, UpdateDocumentContentRequest,
    DocumentCatalogTreeResponse
)
from schemas.common import BaseResponse
from utils.auth import get_current_active_user, check_user_permission
from models.user import User

router = APIRouter()

@router.get("/catalogs")
async def get_document_catalogs(
    organization_name: str = Query(..., description="组织名称"),
    name: str = Query(..., description="仓库名称"),
    branch: Optional[str] = Query(None, description="分支名称"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档目录列表"""
    try:
        catalog_service = DocumentCatalogService(db)
        result = catalog_service.get_document_catalogs_by_warehouse(organization_name, name, branch)
        return BaseResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档目录失败: {str(e)}"
        )

@router.get("/document")
async def get_document_by_path(
    owner: str = Query(..., description="组织名称"),
    name: str = Query(..., description="仓库名称"),
    path: str = Query(..., description="文档路径"),
    branch: Optional[str] = Query(None, description="分支名称"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据路径获取文档内容"""
    try:
        catalog_service = DocumentCatalogService(db)
        result = catalog_service.get_document_by_path(owner, name, path, branch)
        return BaseResponse(data=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档内容失败: {str(e)}"
        )

@router.put("/catalog/update")
async def update_catalog(
    request: UpdateCatalogRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新目录信息"""
    try:
        catalog_service = DocumentCatalogService(db)
        success = catalog_service.update_catalog(request)
        
        if success:
            return BaseResponse(message="目录更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新目录失败: {str(e)}"
        )

@router.put("/content/update")
async def update_document_content(
    request: UpdateDocumentContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新文档内容"""
    try:
        catalog_service = DocumentCatalogService(db)
        success = catalog_service.update_document_content(request)
        
        if success:
            return BaseResponse(message="文档内容更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档内容失败: {str(e)}"
        )

@router.get("/catalog/{catalog_id}")
async def get_catalog_by_id(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据ID获取目录信息"""
    try:
        catalog_service = DocumentCatalogService(db)
        catalog = catalog_service.get_catalog_by_id(catalog_id)
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
        
        return BaseResponse(data={
            "id": catalog.id,
            "warehouse_id": catalog.warehouse_id,
            "parent_id": catalog.parent_id,
            "title": catalog.title,
            "name": catalog.name,
            "url": catalog.url,
            "description": catalog.description,
            "prompt": catalog.prompt,
            "order_index": catalog.order_index,
            "is_completed": catalog.is_completed,
            "is_deleted": catalog.is_deleted,
            "created_at": catalog.created_at,
            "updated_at": catalog.updated_at
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录信息失败: {str(e)}"
        )

@router.get("/catalog/url/{warehouse_id}")
async def get_catalog_by_url(
    warehouse_id: str,
    url: str = Query(..., description="目录URL"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据URL获取目录信息"""
    try:
        catalog_service = DocumentCatalogService(db)
        catalog = catalog_service.get_catalog_by_url(warehouse_id, url)
        
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
        
        return BaseResponse(data={
            "id": catalog.id,
            "warehouse_id": catalog.warehouse_id,
            "parent_id": catalog.parent_id,
            "title": catalog.title,
            "name": catalog.name,
            "url": catalog.url,
            "description": catalog.description,
            "prompt": catalog.prompt,
            "order_index": catalog.order_index,
            "is_completed": catalog.is_completed,
            "is_deleted": catalog.is_deleted,
            "created_at": catalog.created_at,
            "updated_at": catalog.updated_at
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录信息失败: {str(e)}"
        )

@router.post("/catalog/create")
async def create_catalog(
    catalog_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建目录"""
    try:
        catalog_service = DocumentCatalogService(db)
        catalog = catalog_service.create_catalog(catalog_data)
        
        return BaseResponse(
            message="目录创建成功",
            data={
                "id": catalog.id,
                "warehouse_id": catalog.warehouse_id,
                "parent_id": catalog.parent_id,
                "title": catalog.title,
                "name": catalog.name,
                "url": catalog.url,
                "description": catalog.description,
                "prompt": catalog.prompt,
                "order_index": catalog.order_index,
                "is_completed": catalog.is_completed,
                "created_at": catalog.created_at,
                "updated_at": catalog.updated_at
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建目录失败: {str(e)}"
        )

@router.put("/catalog/{catalog_id}/status")
async def update_catalog_status(
    catalog_id: str,
    is_completed: bool = Query(..., description="是否完成"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新目录状态"""
    try:
        catalog_service = DocumentCatalogService(db)
        success = catalog_service.update_catalog_status(catalog_id, is_completed)
        
        if success:
            return BaseResponse(message="目录状态更新成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新目录状态失败: {str(e)}"
        )

@router.delete("/catalog/{catalog_id}")
async def delete_catalog(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除目录"""
    try:
        catalog_service = DocumentCatalogService(db)
        success = catalog_service.delete_catalog(catalog_id)
        
        if success:
            return BaseResponse(message="目录删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目录不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除目录失败: {str(e)}"
        )

@router.get("/progress/{warehouse_id}")
async def get_catalog_progress(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取目录处理进度"""
    try:
        catalog_service = DocumentCatalogService(db)
        progress = catalog_service.get_catalog_progress(warehouse_id)
        return BaseResponse(data=progress)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录进度失败: {str(e)}"
        )

@router.get("/statistics/{warehouse_id}")
async def get_catalog_statistics(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取目录统计信息"""
    try:
        catalog_service = DocumentCatalogService(db)
        statistics = catalog_service.get_catalog_statistics(warehouse_id)
        return BaseResponse(data=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取目录统计失败: {str(e)}"
        )

@router.get("/tree/{warehouse_id}")
async def get_document_catalog_tree(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档目录树"""
    try:
        catalog_service = DocumentCatalogService(db)
        
        # 获取仓库信息
        from models.warehouse import Warehouse
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        # 获取文档目录
        result = catalog_service.get_document_catalogs_by_warehouse(
            warehouse.organization_name, 
            warehouse.name, 
            warehouse.branch
        )
        
        # 构建树形响应
        tree_response = DocumentCatalogTreeResponse(
            items=result["items"],
            last_update=result["last_update"],
            description=result["description"],
            progress=result["progress"],
            git=result["git"],
            branches=result["branches"],
            warehouse_id=warehouse_id,
            like_count=result["like_count"],
            status=result["status"],
            comment_count=result["comment_count"]
        )
        
        return BaseResponse(data=tree_response)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档目录树失败: {str(e)}"
        )

@router.get("/search")
async def search_catalogs(
    warehouse_id: str = Query(..., description="仓库ID"),
    keyword: str = Query(..., description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """搜索目录"""
    try:
        from models.document import DocumentCatalog
        
        # 搜索目录
        catalogs = db.query(DocumentCatalog).filter(
            and_(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_deleted == False,
                or_(
                    DocumentCatalog.name.contains(keyword),
                    DocumentCatalog.title.contains(keyword),
                    DocumentCatalog.description.contains(keyword)
                )
            )
        ).all()
        
        results = []
        for catalog in catalogs:
            results.append({
                "id": catalog.id,
                "name": catalog.name,
                "title": catalog.title,
                "description": catalog.description,
                "url": catalog.url,
                "is_completed": catalog.is_completed,
                "created_at": catalog.created_at
            })
        
        return BaseResponse(data={
            "keyword": keyword,
            "total": len(results),
            "results": results
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索目录失败: {str(e)}"
        )

@router.get("/export/{warehouse_id}")
async def export_catalogs(
    warehouse_id: str,
    format: str = Query("json", description="导出格式 (json, csv)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """导出目录数据"""
    try:
        from models.document import DocumentCatalog
        
        # 获取所有目录
        catalogs = db.query(DocumentCatalog).filter(
            and_(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_deleted == False
            )
        ).order_by(DocumentCatalog.order_index).all()
        
        # 构建导出数据
        export_data = []
        for catalog in catalogs:
            export_data.append({
                "id": catalog.id,
                "name": catalog.name,
                "title": catalog.title,
                "description": catalog.description,
                "url": catalog.url,
                "parent_id": catalog.parent_id,
                "order_index": catalog.order_index,
                "is_completed": catalog.is_completed,
                "prompt": catalog.prompt,
                "created_at": catalog.created_at.isoformat() if catalog.created_at else None,
                "updated_at": catalog.updated_at.isoformat() if catalog.updated_at else None
            })
        
        if format.lower() == "csv":
            import csv
            import io
            
            # 生成CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=export_data[0].keys() if export_data else [])
            writer.writeheader()
            writer.writerows(export_data)
            
            return BaseResponse(
                message="目录导出成功",
                data={
                    "format": "csv",
                    "content": output.getvalue(),
                    "filename": f"catalogs_{warehouse_id}.csv"
                }
            )
        else:
            # JSON格式
            return BaseResponse(
                message="目录导出成功",
                data={
                    "format": "json",
                    "content": export_data,
                    "filename": f"catalogs_{warehouse_id}.json"
                }
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出目录失败: {str(e)}"
        ) 