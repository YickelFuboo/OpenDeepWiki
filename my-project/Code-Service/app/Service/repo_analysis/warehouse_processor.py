import logging
import asyncio
import os
import shutil
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models.warehouse import Warehouse, WarehouseStatus
from utils.git_utils import GitUtils
from utils.file_utils import FileUtils
from ai.services.document_service import DocumentService
from ai.services.overview_service import OverviewService
from ai.services.minimap_service import MiniMapService
from config import get_settings

logger = logging.getLogger(__name__)

class WarehouseProcessor:
    """仓库处理器，负责后台处理仓库的克隆、分析和文档生成"""
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
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
            
            # 2. 分析仓库结构
            structure_result = await self._analyze_structure(warehouse, git_path)
            if not structure_result["success"]:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = structure_result["error"]
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return structure_result
            
            # 3. 生成项目概述
            overview_result = await self._generate_overview(warehouse, git_path)
            if overview_result["success"]:
                warehouse.description = overview_result["overview"]
            
            # 4. 生成知识图谱
            minimap_result = await self._generate_minimap(warehouse, git_path)
            if minimap_result["success"]:
                warehouse.optimized_directory_structure = minimap_result["minimap"]
            
            # 5. 生成文档
            document_result = await self._generate_documents(warehouse, git_path)
            if not document_result["success"]:
                warehouse.status = WarehouseStatus.FAILED
                warehouse.error = document_result["error"]
                warehouse.updated_at = datetime.utcnow()
                self.db.commit()
                return document_result
            
            # 更新状态为完成
            warehouse.status = WarehouseStatus.COMPLETED
            warehouse.updated_at = datetime.utcnow()
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
    
    async def _generate_documents(self, warehouse: Warehouse, git_path: str) -> Dict[str, Any]:
        """生成文档"""
        try:
            logger.info(f"开始生成文档: {warehouse.name}")
            
            # 创建文档服务
            document_service = DocumentService(self.db)
            
            # 生成文档
            document_result = await document_service.generate_documents(
                warehouse=warehouse,
                git_path=git_path
            )
            
            if not document_result["success"]:
                return {"success": False, "error": document_result["error"]}
            
            logger.info(f"文档生成完成: {warehouse.name}")
            
            return {
                "success": True,
                "documents": document_result["documents"],
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