from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from loguru import logger

from src.models.warehouse import Warehouse, WarehouseStatus
from src.models.document import Document
from src.models.document_catalog import DocumentCatalog, DocumentFileItem, DocumentFileItemSource
from src.dto.document_catalog_dto import (
    DocumentCatalogResponse, DocumentCatalogTreeItem, UpdateCatalogRequest,
    UpdateDocumentContentRequest, DocumentFileItemResponse, DocumentFileItemSourceResponse
)


class DocumentCatalogService:
    """文档目录服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_document_catalogs(self, organization_name: str, name: str, branch: Optional[str] = None) -> DocumentCatalogResponse:
        """获取目录列表"""
        try:
            # 查找仓库
            warehouse_query = select(Warehouse).where(
                and_(
                    Warehouse.name == name,
                    Warehouse.organization_name == organization_name,
                    Warehouse.status.in_([WarehouseStatus.Completed, WarehouseStatus.Processing])
                )
            )
            
            if branch:
                warehouse_query = warehouse_query.where(Warehouse.branch == branch)
            
            warehouse_result = await self.db.execute(warehouse_query)
            warehouse = warehouse_result.scalar_one_or_none()
            
            if not warehouse:
                raise ValueError(f"仓库不存在，请检查仓库名称和组织名称:{organization_name} {name}")
            
            # 查找文档
            document_result = await self.db.execute(
                select(Document).where(Document.warehouse_id == warehouse.id)
            )
            document = document_result.scalar_one_or_none()
            
            # 查找目录
            catalogs_result = await self.db.execute(
                select(DocumentCatalog).where(
                    and_(
                        DocumentCatalog.warehouse_id == warehouse.id,
                        DocumentCatalog.is_deleted == False
                    )
                )
            )
            document_catalogs = catalogs_result.scalars().all()
            
            # 获取分支列表
            branches_result = await self.db.execute(
                select(Warehouse.branch).where(
                    and_(
                        Warehouse.name == name,
                        Warehouse.organization_name == organization_name,
                        Warehouse.type == "git",
                        Warehouse.status == WarehouseStatus.Completed
                    )
                ).order_by(Warehouse.status == WarehouseStatus.Completed.desc())
            )
            branches = [row[0] for row in branches_result.fetchall()]
            
            # 构建目录树
            items = self._build_document_tree(document_catalogs)
            
            # 计算进度
            completed_count = sum(1 for catalog in document_catalogs if catalog.is_completed)
            progress = (completed_count * 100 // len(document_catalogs)) if document_catalogs else 0
            
            return DocumentCatalogResponse(
                items=items,
                last_update=document.last_update if document else None,
                description=document.description if document else None,
                progress=progress,
                git=warehouse.address,
                branchs=branches,
                warehouse_id=document.warehouse_id if document else None,
                like_count=document.like_count if document else 0,
                status=document.status if document else None,
                comment_count=document.comment_count if document else 0
            )
            
        except Exception as e:
            logger.error(f"获取文档目录失败: {e}")
            raise
    
    async def get_document_by_id(self, owner: str, name: str, path: str, 
                                 branch: Optional[str] = None) -> Optional[DocumentFileItemResponse]:
        """根据目录id获取文件"""
        try:
            # 查找仓库
            warehouse_query = select(Warehouse).where(
                and_(
                    Warehouse.name == name,
                    Warehouse.organization_name == owner,
                    Warehouse.status.in_([WarehouseStatus.Completed, WarehouseStatus.Processing])
                )
            )
            
            if branch:
                warehouse_query = warehouse_query.where(Warehouse.branch == branch)
            
            warehouse_result = await self.db.execute(warehouse_query)
            warehouse = warehouse_result.scalar_one_or_none()
            
            if not warehouse:
                raise ValueError(f"仓库不存在，请检查仓库名称和组织名称:{owner} {name}")
            
            # 查找目录
            catalog_result = await self.db.execute(
                select(DocumentCatalog).where(
                    and_(
                        DocumentCatalog.warehouse_id == warehouse.id,
                        DocumentCatalog.url == path,
                        DocumentCatalog.is_deleted == False
                    )
                )
            )
            catalog = catalog_result.scalar_one_or_none()
            
            if not catalog:
                return None
            
            # 查找文件项
            file_item_result = await self.db.execute(
                select(DocumentFileItem)
                .options(selectinload(DocumentFileItem.sources))
                .where(DocumentFileItem.document_catalog_id == catalog.id)
            )
            file_item = file_item_result.scalar_one_or_none()
            
            if not file_item:
                return None
            
            # 构建响应
            sources = []
            for source in file_item.sources:
                sources.append(DocumentFileItemSourceResponse(
                    id=source.id,
                    file_path=source.file_path,
                    line_start=source.line_start,
                    line_end=source.line_end,
                    content=source.content
                ))
            
            return DocumentFileItemResponse(
                id=file_item.id,
                title=file_item.title,
                description=file_item.description,
                content=file_item.content,
                comment_count=file_item.comment_count,
                size=file_item.size,
                request_token=file_item.request_token,
                response_token=file_item.response_token,
                is_embedded=file_item.is_embedded,
                metadata=file_item.metadata,
                extra=file_item.extra,
                sources=sources
            )
            
        except Exception as e:
            logger.error(f"获取文档文件失败: {e}")
            raise
    
    async def update_catalog(self, request: UpdateCatalogRequest) -> bool:
        """更新目录"""
        try:
            catalog_result = await self.db.execute(
                select(DocumentCatalog).where(DocumentCatalog.id == request.id)
            )
            catalog = catalog_result.scalar_one_or_none()
            
            if not catalog:
                return False
            
            catalog.name = request.name
            catalog.prompt = request.prompt
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新目录失败: {e}")
            raise
    
    async def update_document_content(self, request: UpdateDocumentContentRequest) -> bool:
        """更新文档内容"""
        try:
            file_item_result = await self.db.execute(
                select(DocumentFileItem).where(DocumentFileItem.id == request.id)
            )
            file_item = file_item_result.scalar_one_or_none()
            
            if not file_item:
                return False
            
            file_item.content = request.content
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新文档内容失败: {e}")
            raise
    
    def _build_document_tree(self, documents: List[DocumentCatalog]) -> List[DocumentCatalogTreeItem]:
        """构建文档树"""
        # 创建根节点列表
        root_items = []
        
        # 创建所有节点的映射
        node_map = {}
        for doc in documents:
            node_map[doc.id] = DocumentCatalogTreeItem(
                id=doc.id,
                name=doc.name,
                url=doc.url,
                description=doc.description,
                parent_id=doc.parent_id,
                order=doc.order,
                is_completed=doc.is_completed,
                prompt=doc.prompt,
                children=[]
            )
        
        # 构建树结构
        for doc in documents:
            node = node_map[doc.id]
            if doc.parent_id and doc.parent_id in node_map:
                # 添加到父节点
                parent = node_map[doc.parent_id]
                parent.children.append(node)
            else:
                # 根节点
                root_items.append(node)
        
        # 按order排序
        def sort_children(items):
            items.sort(key=lambda x: x.order)
            for item in items:
                sort_children(item.children)
        
        sort_children(root_items)
        return root_items 