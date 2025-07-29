import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from fastapi import HTTPException, status
from datetime import datetime

from models.document import DocumentCatalog, DocumentFileItem, DocumentFileItemSource
from models.warehouse import Warehouse, WarehouseStatus
from models.document import Document
from schemas.document import (
    DocumentCatalogResponse, DocumentCatalogTreeResponse,
    UpdateCatalogRequest, UpdateDocumentContentRequest
)
from utils.auth import check_user_permission

logger = logging.getLogger(__name__)

class DocumentCatalogService:
    """文档目录服务类，负责文档目录管理的核心业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_document_catalogs_by_warehouse(self, organization_name: str, name: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """根据仓库信息获取文档目录列表"""
        try:
            # 查找仓库
            warehouse_query = self.db.query(Warehouse).filter(
                and_(
                    Warehouse.name == name,
                    Warehouse.organization_name == organization_name,
                    Warehouse.status.in_([WarehouseStatus.COMPLETED, WarehouseStatus.PROCESSING])
                )
            )
            
            if branch:
                warehouse_query = warehouse_query.filter(Warehouse.branch == branch)
            
            warehouse = warehouse_query.first()
            
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"仓库不存在，请检查仓库名称和组织名称:{organization_name} {name}"
                )
            
            # 获取文档信息
            document = self.db.query(Document).filter(Document.warehouse_id == warehouse.id).first()
            
            # 获取文档目录
            document_catalogs = self.db.query(DocumentCatalog).filter(
                and_(
                    DocumentCatalog.warehouse_id == warehouse.id,
                    DocumentCatalog.is_deleted == False
                )
            ).order_by(DocumentCatalog.order_index).all()
            
            # 获取分支列表
            branches = self.db.query(Warehouse.branch).filter(
                and_(
                    Warehouse.name == name,
                    Warehouse.organization_name == organization_name,
                    Warehouse.type == "git",
                    Warehouse.status == WarehouseStatus.COMPLETED
                )
            ).order_by(Warehouse.status == WarehouseStatus.COMPLETED.desc()).all()
            
            branches = [branch[0] for branch in branches if branch[0]]
            
            # 构建树形结构
            items = self._build_document_tree(document_catalogs)
            
            # 计算进度
            total_catalogs = len(document_catalogs)
            completed_catalogs = len([c for c in document_catalogs if c.is_completed])
            progress = (completed_catalogs * 100 // total_catalogs) if total_catalogs > 0 else 0
            
            return {
                "items": items,
                "last_update": document.last_update if document else None,
                "description": document.description if document else None,
                "progress": progress,
                "git": warehouse.address,
                "branches": branches,
                "warehouse_id": document.warehouse_id if document else None,
                "like_count": document.like_count if document else 0,
                "status": document.status.value if document else "pending",
                "comment_count": document.comment_count if document else 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取文档目录失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文档目录失败: {str(e)}"
            )
    
    def get_document_by_path(self, owner: str, name: str, path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """根据路径获取文档内容"""
        try:
            # 查找仓库
            warehouse_query = self.db.query(Warehouse).filter(
                and_(
                    Warehouse.name == name,
                    Warehouse.organization_name == owner,
                    Warehouse.status.in_([WarehouseStatus.COMPLETED, WarehouseStatus.PROCESSING])
                )
            )
            
            if branch:
                warehouse_query = warehouse_query.filter(Warehouse.branch == branch)
            
            warehouse = warehouse_query.first()
            
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"仓库不存在，请检查仓库名称和组织名称:{owner} {name}"
                )
            
            # 查找目录
            catalog = self.db.query(DocumentCatalog).filter(
                and_(
                    DocumentCatalog.warehouse_id == warehouse.id,
                    DocumentCatalog.url == path,
                    DocumentCatalog.is_deleted == False
                )
            ).first()
            
            if not catalog:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档目录不存在"
                )
            
            # 查找文档文件项
            file_item = self.db.query(DocumentFileItem).filter(
                DocumentFileItem.document_catalog_id == catalog.id
            ).first()
            
            if not file_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档内容不存在"
                )
            
            # 查找文件源
            file_sources = self.db.query(DocumentFileItemSource).filter(
                DocumentFileItemSource.document_file_item_id == file_item.id
            ).all()
            
            return {
                "content": file_item.content,
                "title": file_item.title,
                "file_sources": [
                    {
                        "id": source.id,
                        "name": source.name,
                        "address": source.address,
                        "created_at": source.created_at,
                        "updated_at": source.updated_at
                    }
                    for source in file_sources
                ],
                "address": warehouse.address.replace(".git", ""),
                "branch": warehouse.branch,
                "last_update": file_item.created_at,
                "document_catalog_id": catalog.id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取文档内容失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文档内容失败: {str(e)}"
            )
    
    def update_catalog(self, request: UpdateCatalogRequest) -> bool:
        """更新目录信息"""
        try:
            catalog = self.db.query(DocumentCatalog).filter(DocumentCatalog.id == request.id).first()
            if not catalog:
                return False
            
            catalog.name = request.name
            catalog.prompt = request.prompt
            catalog.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新目录失败: {e}")
            return False
    
    def update_document_content(self, request: UpdateDocumentContentRequest) -> bool:
        """更新文档内容"""
        try:
            file_item = self.db.query(DocumentFileItem).filter(
                DocumentFileItem.document_catalog_id == request.id
            ).first()
            
            if not file_item:
                return False
            
            file_item.content = request.content
            file_item.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新文档内容失败: {e}")
            return False
    
    def _build_document_tree(self, documents: List[DocumentCatalog]) -> List[Dict[str, Any]]:
        """递归构建文档目录树形结构"""
        result = []
        
        # 获取顶级目录
        top_level = [doc for doc in documents if not doc.parent_id]
        top_level.sort(key=lambda x: x.order_index)
        
        for item in top_level:
            children = self._get_children(item.id, documents)
            if not children:
                result.append({
                    "label": item.name,
                    "url": item.url,
                    "description": item.description,
                    "key": item.id,
                    "last_update": item.created_at,
                    "disabled": not item.is_completed
                })
            else:
                result.append({
                    "label": item.name,
                    "description": item.description,
                    "url": item.url,
                    "key": item.id,
                    "last_update": item.created_at,
                    "children": children,
                    "disabled": not item.is_completed
                })
        
        return result
    
    def _get_children(self, parent_id: str, documents: List[DocumentCatalog]) -> List[Dict[str, Any]]:
        """递归获取子目录"""
        children = []
        direct_children = [doc for doc in documents if doc.parent_id == parent_id]
        direct_children.sort(key=lambda x: x.order_index)
        
        for child in direct_children:
            # 递归获取子目录的子目录
            sub_children = self._get_children(child.id, documents)
            
            if not sub_children:
                children.append({
                    "label": child.name,
                    "last_update": child.created_at,
                    "url": child.url,
                    "key": child.id,
                    "description": child.description,
                    "disabled": not child.is_completed
                })
            else:
                children.append({
                    "label": child.name,
                    "key": child.id,
                    "url": child.url,
                    "description": child.description,
                    "last_update": child.created_at,
                    "children": sub_children,
                    "disabled": not child.is_completed
                })
        
        return children
    
    def get_catalog_by_id(self, catalog_id: str) -> Optional[DocumentCatalog]:
        """根据ID获取目录"""
        return self.db.query(DocumentCatalog).filter(DocumentCatalog.id == catalog_id).first()
    
    def get_catalog_by_url(self, warehouse_id: str, url: str) -> Optional[DocumentCatalog]:
        """根据URL获取目录"""
        return self.db.query(DocumentCatalog).filter(
            and_(
                DocumentCatalog.warehouse_id == warehouse_id,
                DocumentCatalog.url == url,
                DocumentCatalog.is_deleted == False
            )
        ).first()
    
    def create_catalog(self, catalog_data: Dict[str, Any]) -> DocumentCatalog:
        """创建目录"""
        catalog = DocumentCatalog(
            id=catalog_data["id"],
            warehouse_id=catalog_data["warehouse_id"],
            parent_id=catalog_data.get("parent_id"),
            title=catalog_data["title"],
            name=catalog_data["name"],
            url=catalog_data["url"],
            description=catalog_data.get("description", ""),
            prompt=catalog_data.get("prompt", ""),
            order_index=catalog_data.get("order_index", 0),
            is_completed=catalog_data.get("is_completed", False),
            is_deleted=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(catalog)
        self.db.commit()
        self.db.refresh(catalog)
        
        return catalog
    
    def update_catalog_status(self, catalog_id: str, is_completed: bool) -> bool:
        """更新目录状态"""
        try:
            catalog = self.get_catalog_by_id(catalog_id)
            if not catalog:
                return False
            
            catalog.is_completed = is_completed
            catalog.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新目录状态失败: {e}")
            return False
    
    def delete_catalog(self, catalog_id: str) -> bool:
        """删除目录（软删除）"""
        try:
            catalog = self.get_catalog_by_id(catalog_id)
            if not catalog:
                return False
            
            catalog.is_deleted = True
            catalog.deleted_time = datetime.utcnow()
            catalog.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"删除目录失败: {e}")
            return False
    
    def get_catalog_progress(self, warehouse_id: str) -> Dict[str, Any]:
        """获取目录处理进度"""
        try:
            catalogs = self.db.query(DocumentCatalog).filter(
                and_(
                    DocumentCatalog.warehouse_id == warehouse_id,
                    DocumentCatalog.is_deleted == False
                )
            ).all()
            
            total = len(catalogs)
            completed = len([c for c in catalogs if c.is_completed])
            progress = (completed * 100 // total) if total > 0 else 0
            
            return {
                "total": total,
                "completed": completed,
                "pending": total - completed,
                "progress": progress
            }
            
        except Exception as e:
            logger.error(f"获取目录进度失败: {e}")
            return {
                "total": 0,
                "completed": 0,
                "pending": 0,
                "progress": 0
            }
    
    def get_catalog_statistics(self, warehouse_id: str) -> Dict[str, Any]:
        """获取目录统计信息"""
        try:
            catalogs = self.db.query(DocumentCatalog).filter(
                and_(
                    DocumentCatalog.warehouse_id == warehouse_id,
                    DocumentCatalog.is_deleted == False
                )
            ).all()
            
            # 按类型统计
            type_stats = {}
            for catalog in catalogs:
                catalog_type = catalog.type.value if catalog.type else "unknown"
                if catalog_type not in type_stats:
                    type_stats[catalog_type] = 0
                type_stats[catalog_type] += 1
            
            # 按状态统计
            status_stats = {
                "completed": len([c for c in catalogs if c.is_completed]),
                "pending": len([c for c in catalogs if not c.is_completed])
            }
            
            return {
                "total_catalogs": len(catalogs),
                "type_statistics": type_stats,
                "status_statistics": status_stats,
                "last_updated": max([c.updated_at for c in catalogs]) if catalogs else None
            }
            
        except Exception as e:
            logger.error(f"获取目录统计失败: {e}")
            return {
                "total_catalogs": 0,
                "type_statistics": {},
                "status_statistics": {"completed": 0, "pending": 0},
                "last_updated": None
            } 