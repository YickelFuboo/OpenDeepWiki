import os
import zipfile
import io
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.document import Document
from src.models.document_overview import DocumentOverview
from src.models.document_catalog import DocumentCatalog
from src.models.document_file_item import DocumentFileItem


class WarehouseContentService:
    """仓库内容服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_file_content(self, warehouse_id: str, path: str, user_id: str) -> str:
        """获取指定仓库代码文件"""
        try:
            # 检查用户权限
            from src.services.warehouse_permission_service import WarehousePermissionService
            permission_service = WarehousePermissionService(self.db)
            if not await permission_service.check_warehouse_access(warehouse_id, user_id):
                raise HTTPException(status_code=403, detail="您没有权限访问此仓库")
            
            # 获取仓库信息
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 构建文件路径
            file_path = os.path.join(warehouse.git_path or "", path)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")
    
    async def get_file_content_line(
        self, 
        organization_name: str, 
        name: str, 
        file_path: str
    ) -> str:
        """获取指定组织下仓库的指定文件代码内容"""
        try:
            # 获取仓库信息
            result = await self.db.execute(
                select(Warehouse).where(
                    Warehouse.organization_name == organization_name,
                    Warehouse.name == name
                )
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 构建文件路径
            full_file_path = os.path.join(warehouse.git_path or "", file_path)
            
            if not os.path.exists(full_file_path):
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 读取文件内容
            with open(full_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取文件内容失败: {str(e)}")
    
    async def export_markdown_zip(self, warehouse_id: str, user_id: str) -> bytes:
        """导出Markdown压缩包"""
        try:
            # 检查用户权限
            from src.services.warehouse_permission_service import WarehousePermissionService
            permission_service = WarehousePermissionService(self.db)
            if not await permission_service.check_warehouse_access(warehouse_id, user_id):
                raise HTTPException(status_code=403, detail="您没有权限访问此仓库")
            
            # 获取仓库信息
            result = await self.db.execute(
                select(Warehouse).where(Warehouse.id == warehouse_id)
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 获取文档信息
            document_result = await self.db.execute(
                select(Document).where(Document.warehouse_id == warehouse_id)
            )
            document = document_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail="文档不存在")
            
            # 获取文档概述
            overview_result = await self.db.execute(
                select(DocumentOverview).where(DocumentOverview.document_id == document.id)
            )
            overview = overview_result.scalar_one_or_none()
            
            # 获取文档目录
            catalog_result = await self.db.execute(
                select(DocumentCatalog).where(
                    DocumentCatalog.warehouse_id == warehouse_id,
                    DocumentCatalog.is_deleted == False
                )
            )
            catalogs = catalog_result.scalars().all()
            
            catalog_ids = [catalog.id for catalog in catalogs]
            
            # 获取文档文件条目
            file_items_result = await self.db.execute(
                select(DocumentFileItem).where(
                    DocumentFileItem.document_catalog_id.in_(catalog_ids)
                )
            )
            file_items = file_items_result.scalars().all()
            
            # 创建ZIP文件
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 添加README.md
                if overview:
                    readme_content = f"# {warehouse.name}\n\n{overview.content}"
                else:
                    readme_content = f"# {warehouse.name}\n\n{warehouse.description or '暂无描述'}"
                
                zip_file.writestr("README.md", readme_content)
                
                # 添加文档文件
                for file_item in file_items:
                    if file_item.content:
                        # 构建文件路径
                        file_path = file_item.path or f"docs/{file_item.title}.md"
                        zip_file.writestr(file_path, file_item.content)
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"导出Markdown压缩包失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"导出Markdown压缩包失败: {str(e)}")
    
    async def get_warehouse_overview(
        self, 
        owner: str, 
        name: str, 
        branch: str = "main",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取仓库概述"""
        try:
            # 获取仓库信息
            result = await self.db.execute(
                select(Warehouse).where(
                    Warehouse.organization_name == owner,
                    Warehouse.name == name,
                    Warehouse.branch == branch,
                    Warehouse.status.in_(["completed", "processing"])
                )
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(
                    status_code=404, 
                    detail=f"仓库不存在，请检查仓库名称和组织名称: {owner} {name} {branch}"
                )
            
            # 检查用户权限
            from src.services.warehouse_permission_service import WarehousePermissionService
            permission_service = WarehousePermissionService(self.db)
            if not await permission_service.check_warehouse_access(warehouse.id, user_id):
                raise HTTPException(status_code=403, detail="您没有权限访问此仓库")
            
            # 获取文档信息
            document_result = await self.db.execute(
                select(Document).where(Document.warehouse_id == warehouse.id)
            )
            document = document_result.scalar_one_or_none()
            
            if not document:
                raise HTTPException(status_code=404, detail="没有找到文档, 可能在生成中或者已经出现错误")
            
            # 获取文档概述
            overview_result = await self.db.execute(
                select(DocumentOverview).where(DocumentOverview.document_id == document.id)
            )
            overview = overview_result.scalar_one_or_none()
            
            if not overview:
                raise HTTPException(status_code=404, detail="没有找到概述")
            
            return {
                "content": overview.content,
                "title": overview.title
            }
            
        except Exception as e:
            logger.error(f"获取仓库概述失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取仓库概述失败: {str(e)}")
    
    async def get_mini_map(
        self, 
        owner: str, 
        name: str, 
        branch: str = ""
    ) -> Dict[str, Any]:
        """获取思维导图"""
        try:
            # 获取仓库信息
            result = await self.db.execute(
                select(Warehouse).where(
                    Warehouse.organization_name == owner,
                    Warehouse.name == name,
                    Warehouse.status.in_(["completed", "processing"])
                )
            )
            warehouse = result.scalar_one_or_none()
            
            if not warehouse:
                raise HTTPException(status_code=404, detail="仓库不存在")
            
            # 获取思维导图数据
            from src.models.mini_map import MiniMap
            mini_map_result = await self.db.execute(
                select(MiniMap).where(MiniMap.warehouse_id == warehouse.id)
            )
            mini_map = mini_map_result.scalar_one_or_none()
            
            if not mini_map:
                return {
                    "code": 200,
                    "message": "没有找到知识图谱",
                    "data": {}
                }
            
            # 解析思维导图数据
            import json
            mini_map_data = json.loads(mini_map.value)
            
            # 构建跳转地址
            address = warehouse.address.replace(".git", "").rstrip('/').lower()
            
            if "github.com" in address:
                address += f"/tree/{warehouse.branch}/"
            elif "gitee.com" in address:
                address += f"/tree/{warehouse.branch}/"
            
            # 更新节点URL
            def update_url(node):
                if node.get("url", "").startswith("http"):
                    node["url"] = node["url"].replace(warehouse.address, "")
                
                if node.get("url") and not node["url"].startswith("http"):
                    node["url"] = address + node["url"].lstrip('/')
                
                for child in node.get("nodes", []):
                    update_url(child)
            
            for node in mini_map_data.get("nodes", []):
                update_url(node)
            
            return {
                "code": 200,
                "message": "获取知识图谱成功",
                "data": mini_map_data
            }
            
        except Exception as e:
            logger.error(f"获取思维导图失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取思维导图失败: {str(e)}") 