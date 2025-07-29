import logging
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime

from models.document import Document, DocumentCatalog, DocumentFileItem, DocumentFileItemSource
from models.warehouse import Warehouse, WarehouseStatus
from schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentCatalogCreate, DocumentCatalogUpdate, DocumentCatalogResponse,
    DocumentFileItemCreate, DocumentFileItemResponse
)
from schemas.common import PaginationParams, PaginatedResponse
from utils.auth import check_user_permission
from config import get_settings

logger = logging.getLogger(__name__)

class DocumentService:
    """文档服务类，负责文档管理的核心业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def get_documents(self, pagination: PaginationParams, warehouse_id: Optional[str] = None) -> PaginatedResponse:
        """获取文档列表"""
        query = self.db.query(Document)
        
        # 按仓库过滤
        if warehouse_id:
            query = query.filter(Document.warehouse_id == warehouse_id)
        
        # 关键词搜索
        if pagination.keyword:
            query = query.filter(
                or_(
                    Document.title.contains(pagination.keyword),
                    Document.description.contains(pagination.keyword)
                )
            )
        
        # 计算总数
        total = query.count()
        
        # 分页
        documents = query.order_by(Document.created_at.desc()).offset(
            (pagination.page - 1) * pagination.page_size
        ).limit(pagination.page_size).all()
        
        # 转换为响应模型
        document_responses = []
        for doc in documents:
            doc_response = DocumentResponse(
                id=doc.id,
                warehouse_id=doc.warehouse_id,
                title=doc.title,
                description=doc.description,
                status=doc.status.value,
                git_path=doc.git_path,
                last_update=doc.last_update,
                like_count=doc.like_count,
                comment_count=doc.comment_count,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            document_responses.append(doc_response)
        
        return PaginatedResponse(
            items=document_responses,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=(total + pagination.page_size - 1) // pagination.page_size
        )
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """根据ID获取文档"""
        return self.db.query(Document).filter(Document.id == document_id).first()
    
    def get_document_by_warehouse(self, warehouse_id: str) -> Optional[Document]:
        """根据仓库ID获取文档"""
        return self.db.query(Document).filter(Document.warehouse_id == warehouse_id).first()
    
    def create_document(self, document_data: DocumentCreate) -> DocumentResponse:
        """创建文档"""
        # 检查仓库是否存在且状态正确
        warehouse = self.db.query(Warehouse).filter(Warehouse.id == document_data.warehouse_id).first()
        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="仓库不存在"
            )
        
        if warehouse.status not in [WarehouseStatus.COMPLETED, WarehouseStatus.PROCESSING]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仓库状态不正确，无法创建文档"
            )
        
        # 检查是否已存在文档
        existing_document = self.get_document_by_warehouse(document_data.warehouse_id)
        if existing_document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该仓库已存在文档"
            )
        
        # 创建文档
        document = Document(
            id=self._generate_document_id(),
            warehouse_id=document_data.warehouse_id,
            title=document_data.title,
            description=document_data.description,
            git_path=document_data.git_path,
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return DocumentResponse.from_orm(document)
    
    def update_document(self, document_id: str, document_data: DocumentUpdate) -> DocumentResponse:
        """更新文档"""
        document = self.get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 更新字段
        if document_data.title is not None:
            document.title = document_data.title
        if document_data.description is not None:
            document.description = document_data.description
        if document_data.status is not None:
            document.status = document_data.status
        
        document.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(document)
        
        return DocumentResponse.from_orm(document)
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        document = self.get_document_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 删除相关的文档目录和文件项
        self.db.query(DocumentCatalog).filter(DocumentCatalog.document_id == document_id).delete()
        self.db.query(DocumentFileItem).filter(DocumentFileItem.document_id == document_id).delete()
        
        # 删除文档
        self.db.delete(document)
        self.db.commit()
        
        return True
    
    def get_document_catalogs(self, warehouse_id: str) -> List[DocumentCatalogResponse]:
        """获取文档目录列表"""
        catalogs = self.db.query(DocumentCatalog).filter(
            and_(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.is_deleted == False
            )
        ).order_by(DocumentCatalog.order_index).all()
        
        # 构建树形结构
        catalog_tree = self._build_catalog_tree(catalogs)
        
        return catalog_tree
    
    def get_document_catalog_by_id(self, catalog_id: str) -> Optional[DocumentCatalog]:
        """根据ID获取文档目录"""
        return self.db.query(DocumentCatalog).filter(DocumentCatalog.id == catalog_id).first()
    
    def create_document_catalog(self, catalog_data: DocumentCatalogCreate) -> DocumentCatalogResponse:
        """创建文档目录"""
        # 检查父目录是否存在
        if catalog_data.parent_id:
            parent_catalog = self.get_document_catalog_by_id(catalog_data.parent_id)
            if not parent_catalog:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="父目录不存在"
                )
        
        # 创建目录
        catalog = DocumentCatalog(
            id=self._generate_catalog_id(),
            warehouse_id=catalog_data.warehouse_id,
            parent_id=catalog_data.parent_id,
            title=catalog_data.title,
            name=catalog_data.name,
            type=catalog_data.type,
            prompt=catalog_data.prompt,
            order_index=catalog_data.order_index or 0,
            is_completed=False,
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(catalog)
        self.db.commit()
        self.db.refresh(catalog)
        
        return DocumentCatalogResponse.from_orm(catalog)
    
    def update_document_catalog(self, catalog_id: str, catalog_data: DocumentCatalogUpdate) -> DocumentCatalogResponse:
        """更新文档目录"""
        catalog = self.get_document_catalog_by_id(catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档目录不存在"
            )
        
        # 更新字段
        if catalog_data.title is not None:
            catalog.title = catalog_data.title
        if catalog_data.name is not None:
            catalog.name = catalog_data.name
        if catalog_data.prompt is not None:
            catalog.prompt = catalog_data.prompt
        if catalog_data.order_index is not None:
            catalog.order_index = catalog_data.order_index
        
        catalog.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(catalog)
        
        return DocumentCatalogResponse.from_orm(catalog)
    
    def delete_document_catalog(self, catalog_id: str) -> bool:
        """删除文档目录"""
        catalog = self.get_document_catalog_by_id(catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档目录不存在"
            )
        
        # 软删除
        catalog.is_deleted = True
        catalog.deleted_time = datetime.utcnow()
        catalog.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    def get_document_file_item(self, catalog_id: str) -> Optional[DocumentFileItem]:
        """根据目录ID获取文档文件项"""
        return self.db.query(DocumentFileItem).filter(
            DocumentFileItem.document_catalog_id == catalog_id
        ).first()
    
    def create_document_file_item(self, file_item_data: DocumentFileItemCreate) -> DocumentFileItemResponse:
        """创建文档文件项"""
        # 检查目录是否存在
        catalog = self.get_document_catalog_by_id(file_item_data.document_catalog_id)
        if not catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档目录不存在"
            )
        
        # 创建文件项
        file_item = DocumentFileItem(
            id=self._generate_file_item_id(),
            document_catalog_id=file_item_data.document_catalog_id,
            title=file_item_data.title,
            content=file_item_data.content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(file_item)
        self.db.commit()
        self.db.refresh(file_item)
        
        return DocumentFileItemResponse.from_orm(file_item)
    
    def update_document_file_item(self, file_item_id: str, content: str) -> DocumentFileItemResponse:
        """更新文档文件项内容"""
        file_item = self.db.query(DocumentFileItem).filter(DocumentFileItem.id == file_item_id).first()
        if not file_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档文件项不存在"
            )
        
        file_item.content = content
        file_item.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(file_item)
        
        return DocumentFileItemResponse.from_orm(file_item)
    
    def get_document_file_sources(self, file_item_id: str) -> List[DocumentFileItemSource]:
        """获取文档文件源列表"""
        return self.db.query(DocumentFileItemSource).filter(
            DocumentFileItemSource.document_file_item_id == file_item_id
        ).all()
    
    def create_document_file_source(self, source_data: Dict[str, Any]) -> DocumentFileItemSource:
        """创建文档文件源"""
        source = DocumentFileItemSource(
            id=self._generate_source_id(),
            document_file_item_id=source_data["document_file_item_id"],
            name=source_data["name"],
            address=source_data["address"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        
        return source
    
    def _build_catalog_tree(self, catalogs: List[DocumentCatalog]) -> List[DocumentCatalogResponse]:
        """构建目录树形结构"""
        # 创建ID到目录的映射
        catalog_map = {catalog.id: catalog for catalog in catalogs}
        
        # 构建树形结构
        tree = []
        for catalog in catalogs:
            if not catalog.parent_id or catalog.parent_id not in catalog_map:
                # 顶级目录
                tree.append(self._build_catalog_node(catalog, catalog_map))
        
        return tree
    
    def _build_catalog_node(self, catalog: DocumentCatalog, catalog_map: Dict[str, DocumentCatalog]) -> DocumentCatalogResponse:
        """构建目录节点"""
        # 查找子目录
        children = []
        for c in catalog_map.values():
            if c.parent_id == catalog.id:
                children.append(self._build_catalog_node(c, catalog_map))
        
        # 构建响应对象
        catalog_response = DocumentCatalogResponse(
            id=catalog.id,
            warehouse_id=catalog.warehouse_id,
            parent_id=catalog.parent_id,
            title=catalog.title,
            name=catalog.name,
            type=catalog.type.value,
            prompt=catalog.prompt,
            content=catalog.content,
            order_index=catalog.order_index,
            is_completed=catalog.is_completed,
            is_deleted=catalog.is_deleted,
            created_at=catalog.created_at,
            updated_at=catalog.updated_at,
            children=children if children else None
        )
        
        return catalog_response
    
    def _generate_document_id(self) -> str:
        """生成文档ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_catalog_id(self) -> str:
        """生成目录ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_file_item_id(self) -> str:
        """生成文件项ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _generate_source_id(self) -> str:
        """生成源文件ID"""
        import uuid
        return str(uuid.uuid4()) 