import logging
import asyncio
import os
import shutil
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models.warehouse import Warehouse, WarehouseStatus
from models.document import Document, DocumentStatus
from utils.git_utils import GitUtils
from utils.file_utils import FileUtils
from ai.services.document_service import DocumentService as AIDocumentService
from ai.services.overview_service import OverviewService
from ai.services.minimap_service import MiniMapService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WarehouseProcessor:
    """仓库处理器，负责后台处理仓库的克隆、分析和文档生成"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = settings
        self.git_utils = GitUtils()
        self.file_utils = FileUtils()
    
    async def process_warehouse(self, warehouse_id: str) -> Dict[str, Any]:
        """处理仓库的主要方法"""
        try:
            # 获取仓库信息
            warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if not warehouse:
                return {"success": False, "error": "仓库不存在"}
            
            # 更新状态为处理中
            warehouse.status = WarehouseStatus.PROCESSING
            warehouse.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"开始处理仓库: {warehouse.name}")
            
            # 1. 克隆仓库
            clone_result = await self._clone_repository(warehouse)
            if not clone_result["success"]:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = clone_result["error"]
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return clone_result
            
            git_path = clone_result["git_path"]
            
            # 2. 创建或获取Document对象
            document = self._create_or_get_document(warehouse, git_path)
            if not document:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = "创建文档记录失败"
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return {"success": False, "error": "创建文档记录失败"}
            
            # 3. 分析仓库结构
            structure_result = await self._analyze_structure(warehouse, git_path)
            if not structure_result["success"]:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = structure_result["error"]
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return structure_result
            
            # 4. 生成项目概述
            overview_result = await self._generate_overview(warehouse, git_path)
            if overview_result["success"]:
                warehouse.description = overview_result["overview"]
            
            # 5. 生成知识图谱
            minimap_result = await self._generate_minimap(warehouse, git_path)
            if minimap_result["success"]:
                warehouse.optimized_directory_structure = minimap_result["minimap"]
            
            # 6. 生成文档
            document_result = await self._generate_documents(warehouse, git_path, document)
            if not document_result["success"]:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = document_result["error"]
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return document_result
            
            # 更新状态为完成
            warehouse.status = WarehouseStatus.COMPLETED
            warehouse.updated_at = datetime.utcnow()
            document.status = DocumentStatus.COMPLETED
            document.last_update = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"仓库处理完成: {warehouse.name}")
            
            return {
                "success": True,
                "warehouse_id": warehouse_id,
                "message": "仓库处理完成"
            }
            
        except Exception as e:
            logger.error(f"仓库处理失败: {e}")
            
            # 更新状态为失败
            warehouse = self.db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
            if warehouse:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = str(e)
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
            
            return {"success": False, "error": str(e)}
    
    async def _clone_repository(self, warehouse: Warehouse) -> Dict[str, Any]:
        """克隆仓库"""
        try:
            logger.info(f"开始克隆仓库: {warehouse.address}")
            
            # 构建本地路径
            local_path = os.path.join(self.settings.git_repository_path, warehouse.organization_name, warehouse.name)
            
            # 确保目录存在
            os.makedirs(local_path, exist_ok=True)
            
            # 克隆仓库
            clone_result = await self.git_utils.clone_repository(
                repository_url=warehouse.address,
                local_path=local_path,
                branch=warehouse.branch,
                username=warehouse.git_user_name,
                password=warehouse.git_password
            )
            
            if not clone_result["success"]:
                return {"success": False, "error": f"克隆仓库失败: {clone_result['error']}"}
            
            logger.info(f"仓库克隆成功: {warehouse.name}")
            
            return {
                "success": True,
                "git_path": local_path,
                "message": "仓库克隆成功"
            }
            
        except Exception as e:
            logger.error(f"克隆仓库失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_structure(self, warehouse: Warehouse, git_path: str) -> Dict[str, Any]:
        """分析仓库结构"""
        try:
            logger.info(f"开始分析仓库结构: {warehouse.name}")
            
            # 扫描文件结构
            file_structure = await self.file_utils.scan_directory(git_path)
            
            # 过滤掉不需要的文件和目录
            filtered_structure = self._filter_structure(file_structure)
            
            logger.info(f"仓库结构分析完成: {warehouse.name}")
            
            return {
                "success": True,
                "structure": filtered_structure,
                "message": "仓库结构分析完成"
            }
            
        except Exception as e:
            logger.error(f"分析仓库结构失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_overview(self, warehouse: Warehouse, git_path: str) -> Dict[str, Any]:
        """生成项目概述"""
        try:
            logger.info(f"开始生成项目概述: {warehouse.name}")
            
            # 获取README文件内容
            readme_content = await self._get_readme_content(git_path)
            
            # 创建AI服务
            overview_service = OverviewService(self.db)
            
            # 生成概述
            overview = await overview_service.generate_project_overview(
                kernel=None,  # 这里需要传入kernel实例
                catalogue="",  # 这里需要传入目录信息
                git_repository=warehouse.address,
                branch=warehouse.branch,
                readme=readme_content
            )
            
            logger.info(f"项目概述生成完成: {warehouse.name}")
            
            return {
                "success": True,
                "overview": overview,
                "message": "项目概述生成完成"
            }
            
        except Exception as e:
            logger.error(f"生成项目概述失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_minimap(self, warehouse: Warehouse, git_path: str) -> Dict[str, Any]:
        """生成知识图谱"""
        try:
            logger.info(f"开始生成知识图谱: {warehouse.name}")
            
            # 创建知识图谱服务
            minimap_service = MiniMapService(self.db)
            
            # 生成知识图谱
            minimap_result = await minimap_service.generate_minimap(
                catalogue="",  # 这里需要传入目录信息
                warehouse=warehouse,
                git_path=git_path
            )
            
            if not minimap_result["success"]:
                return {"success": False, "error": minimap_result["error"]}
            
            logger.info(f"知识图谱生成完成: {warehouse.name}")
            
            return {
                "success": True,
                "minimap": minimap_result["minimap"],
                "message": "知识图谱生成完成"
            }
            
        except Exception as e:
            logger.error(f"生成知识图谱失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_documents(self, warehouse: Warehouse, git_path: str, document: Document) -> Dict[str, Any]:
        """生成文档"""
        try:
            logger.info(f"开始生成文档: {warehouse.name}")
            
            # 创建AI文档服务
            ai_document_service = AIDocumentService(self.db)
            
            # 1. 生成README文档
            readme_content = await ai_document_service.generate_readme(warehouse, git_path)
            
            # 2. 生成文档目录
            catalogue = ""  # 这里需要传入目录结构信息
            document_catalogs = await ai_document_service.generate_document_catalog(
                git_path=git_path,
                warehouse=warehouse,
                catalogue=catalogue
            )
            
            # 3. 为每个目录项生成文档内容
            for catalog in document_catalogs:
                catalog.document_id = document.id
                catalog.created_at = datetime.utcnow()
                catalog.updated_at = datetime.utcnow()
                
                # 生成文档内容
                content = await ai_document_service.generate_document_content(catalog, git_path)
                catalog.content = content
                
                # 保存到数据库
                self.db.add(catalog)
            
            self.db.commit()
            
            logger.info(f"文档生成完成: {warehouse.name}, 生成了 {len(document_catalogs)} 个文档")
            
            return {
                "success": True,
                "documents": document_catalogs,
                "message": "文档生成完成"
            }
            
        except Exception as e:
            logger.error(f"生成文档失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_readme_content(self, git_path: str) -> str:
        """获取README文件内容"""
        try:
            readme_files = ["README.md", "README.txt", "readme.md", "readme.txt"]
            
            for readme_file in readme_files:
                readme_path = os.path.join(git_path, readme_file)
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            return ""
            
        except Exception as e:
            logger.error(f"读取README文件失败: {e}")
            return ""
    
    def _filter_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """过滤仓库结构，移除不需要的文件和目录"""
        # 定义需要忽略的文件和目录
        ignore_patterns = [
            '.git', '.gitignore', '.gitattributes',
            'node_modules', 'dist', 'build',
            '.vscode', '.idea', '.vs',
            '__pycache__', '*.pyc', '*.pyo',
            '.DS_Store', 'Thumbs.db',
            '*.log', '*.tmp', '*.temp'
        ]
        
        def should_ignore(path: str) -> bool:
            for pattern in ignore_patterns:
                if pattern in path:
                    return True
            return False
        
        def filter_recursive(data: Dict[str, Any]) -> Dict[str, Any]:
            if isinstance(data, dict):
                filtered = {}
                for key, value in data.items():
                    if not should_ignore(key):
                        filtered[key] = filter_recursive(value)
                return filtered
            elif isinstance(data, list):
                return [filter_recursive(item) for item in data if not should_ignore(str(item))]
            else:
                return data
        
        return filter_recursive(structure) 
    
    def _create_or_get_document(self, warehouse: Warehouse, git_path: str) -> Document:
        """创建或获取Document对象"""
        try:
            # 检查是否已存在文档
            existing_document = self.db.query(Document).filter(
                Document.warehouse_id == warehouse.id
            ).first()
            
            if existing_document:
                # 更新现有文档
                existing_document.git_path = git_path
                existing_document.status = DocumentStatus.PENDING
                existing_document.last_update = datetime.utcnow()
                self.db.commit()
                return existing_document
            
            # 创建新的文档记录
            document = Document(
                id=self._generate_document_id(),
                warehouse_id=warehouse.id,
                git_path=git_path,
                status=DocumentStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"创建文档记录: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"创建文档记录失败: {e}")
            return None
    
    def _generate_document_id(self) -> str:
        """生成文档ID"""
        import uuid
        return f"doc_{uuid.uuid4().hex[:16]}" 