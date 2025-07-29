from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from database import get_db
from services.document_service import DocumentService
from schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentCatalogCreate, DocumentCatalogUpdate, DocumentCatalogResponse,
    DocumentFileItemCreate, DocumentFileItemResponse, DocumentContentResponse,
    DocumentCatalogTreeResponse, UpdateCatalogRequest, UpdateDocumentContentRequest
)
from schemas.common import BaseResponse, PaginationParams, PaginatedResponse
from utils.auth import get_current_active_user, check_user_permission
from models.user import User

router = APIRouter()

@router.get("/", response_model=PaginatedResponse)
async def get_documents(
    pagination: PaginationParams = Depends(),
    warehouse_id: Optional[str] = Query(None, description="仓库ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档列表"""
    try:
        document_service = DocumentService(db)
        result = document_service.get_documents(pagination, warehouse_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    try:
        document_service = DocumentService(db)
        document = document_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        return DocumentResponse.from_orm(document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )

@router.post("/", response_model=DocumentResponse)
async def create_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建文档"""
    try:
        document_service = DocumentService(db)
        document_response = document_service.create_document(document_data)
        return document_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文档失败: {str(e)}"
        )

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_data: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新文档"""
    try:
        document_service = DocumentService(db)
        document_response = document_service.update_document(document_id, document_data)
        return document_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档失败: {str(e)}"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除文档"""
    try:
        document_service = DocumentService(db)
        success = document_service.delete_document(document_id)
        
        if success:
            return BaseResponse(message="文档删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文档删除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )

# 文档目录相关接口
@router.get("/catalogs/{warehouse_id}", response_model=List[DocumentCatalogResponse])
async def get_document_catalogs(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档目录列表"""
    try:
        document_service = DocumentService(db)
        catalogs = document_service.get_document_catalogs(warehouse_id)
        return catalogs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档目录失败: {str(e)}"
        )

@router.get("/catalogs/tree/{warehouse_id}", response_model=DocumentCatalogTreeResponse)
async def get_document_catalog_tree(
    warehouse_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档目录树"""
    try:
        document_service = DocumentService(db)
        catalogs = document_service.get_document_catalogs(warehouse_id)
        
        # 获取仓库信息
        from models.warehouse import Warehouse
        warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
        
        # 获取文档信息
        document = document_service.get_document_by_warehouse(warehouse_id)
        
        # 构建响应
        tree_response = DocumentCatalogTreeResponse(
            items=catalogs,
            last_update=document.last_update if document else None,
            description=document.description if document else None,
            progress=0,  # 这里需要计算实际进度
            git=warehouse.address if warehouse else "",
            branches=[warehouse.branch] if warehouse and warehouse.branch else [],
            warehouse_id=warehouse_id,
            like_count=document.like_count if document else 0,
            status=document.status.value if document else "pending",
            comment_count=document.comment_count if document else 0
        )
        
        return tree_response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档目录树失败: {str(e)}"
        )

@router.post("/catalogs/", response_model=DocumentCatalogResponse)
async def create_document_catalog(
    catalog_data: DocumentCatalogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建文档目录"""
    try:
        document_service = DocumentService(db)
        catalog_response = document_service.create_document_catalog(catalog_data)
        return catalog_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建文档目录失败: {str(e)}"
        )

@router.put("/catalogs/{catalog_id}", response_model=DocumentCatalogResponse)
async def update_document_catalog(
    catalog_id: str,
    catalog_data: DocumentCatalogUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新文档目录"""
    try:
        document_service = DocumentService(db)
        catalog_response = document_service.update_document_catalog(catalog_id, catalog_data)
        return catalog_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档目录失败: {str(e)}"
        )

@router.delete("/catalogs/{catalog_id}")
async def delete_document_catalog(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除文档目录"""
    try:
        document_service = DocumentService(db)
        success = document_service.delete_document_catalog(catalog_id)
        
        if success:
            return BaseResponse(message="文档目录删除成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="文档目录删除失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档目录失败: {str(e)}"
        )

# 文档内容相关接口
@router.get("/content/{catalog_id}", response_model=DocumentContentResponse)
async def get_document_content(
    catalog_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取文档内容"""
    try:
        document_service = DocumentService(db)
        
        # 获取目录信息
        catalog = document_service.get_document_catalog_by_id(catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档目录不存在"
            )
        
        # 获取文件项
        file_item = document_service.get_document_file_item(catalog_id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档内容不存在"
            )
        
        # 获取文件源
        file_sources = document_service.get_document_file_sources(file_item.id)
        
        # 获取仓库信息
        from models.warehouse import Warehouse
        warehouse = db.query(Warehouse).filter(Warehouse.id == catalog.warehouse_id).first()
        
        # 构建响应
        content_response = DocumentContentResponse(
            content=file_item.content,
            title=file_item.title,
            file_sources=[DocumentFileItemSourceResponse.from_orm(source) for source in file_sources],
            address=warehouse.address if warehouse else "",
            branch=warehouse.branch if warehouse else None,
            last_update=file_item.updated_at,
            document_catalog_id=catalog_id
        )
        
        return content_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档内容失败: {str(e)}"
        )

@router.put("/content/{catalog_id}", response_model=DocumentFileItemResponse)
async def update_document_content(
    catalog_id: str,
    content_request: UpdateDocumentContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新文档内容"""
    try:
        document_service = DocumentService(db)
        
        # 获取文件项
        file_item = document_service.get_document_file_item(catalog_id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档内容不存在"
            )
        
        # 更新内容
        file_item_response = document_service.update_document_file_item(file_item.id, content_request.content)
        return file_item_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档内容失败: {str(e)}"
        )

# 兼容性接口（保持与原API一致）
@router.put("/catalogs/update", response_model=BaseResponse)
async def update_catalog(
    request: UpdateCatalogRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新目录信息（兼容性接口）"""
    try:
        document_service = DocumentService(db)
        
        catalog_data = DocumentCatalogUpdate(
            name=request.name,
            prompt=request.prompt
        )
        
        document_service.update_document_catalog(request.id, catalog_data)
        return BaseResponse(message="目录更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新目录失败: {str(e)}"
        )

@router.put("/content/update", response_model=BaseResponse)
async def update_document_content_legacy(
    request: UpdateDocumentContentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新文档内容（兼容性接口）"""
    try:
        document_service = DocumentService(db)
        
        # 获取文件项
        file_item = document_service.get_document_file_item(request.id)
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档内容不存在"
            )
        
        # 更新内容
        document_service.update_document_file_item(file_item.id, request.content)
        return BaseResponse(message="文档内容更新成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档内容失败: {str(e)}"
        ) 