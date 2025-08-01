import asyncio
import os
import re
from typing import Optional, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import Document
from src.models.warehouse import Warehouse
from src.services.kernel_factory import KernelFactory
from src.conf.settings import settings
from src.koala_warehouse.overview.overview_service import OverviewService
from src.koala_warehouse.generate_think_catalogue.generate_think_catalogue_service import GenerateThinkCatalogueService
from src.koala_warehouse.document_pending.document_pending_service import DocumentPendingService


class DocumentsService:
    """文档处理服务 - 核心业务逻辑"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def handle_async(
        self, 
        document: Document, 
        warehouse: Warehouse, 
        git_repository: str
    ) -> None:
        """
        处理文档的完整流程
        包括解析目录结构、生成更新日志、保存结果到数据库
        """
        logger.info(f"开始处理文档: {document.title}, 仓库: {warehouse.name}")
        
        # 获取仓库的本地路径
        path = document.git_path
        
        # 创建AI内核实例
        kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key,
            path, 
            settings.openai.chat_model
        )
        
        # 创建文件操作专用的AI内核实例
        file_kernel = KernelFactory.get_kernel(
            settings.openai.endpoint,
            settings.openai.chat_api_key, 
            path, 
            settings.openai.chat_model, 
            False
        )
        
        try:
            # 步骤1: 读取生成README
            logger.info("步骤1: 生成README文档")
            readme = await self.generate_readme(warehouse, path)
            
            # 步骤2: 读取并且生成目录结构
            logger.info("步骤2: 生成目录结构")
            catalogue = await self.get_catalogue_smart_filter_optimized_async(path, readme)
            
            # 如果成功生成目录结构，保存到数据库
            if catalogue:
                warehouse.optimized_directory_structure = catalogue
                await self.db.commit()
            
            # 步骤3: 生成项目概述
            logger.info("步骤3: 生成项目概述")
            overview = await OverviewService.generate_project_overview(
                kernel, catalogue, git_repository, 
                document.branch or "main", readme, None
            )
            
            # 步骤4: 生成思维导图
            logger.info("步骤4: 生成思维导图")
            think_catalogue = await GenerateThinkCatalogueService.generate_think_catalogue_async(
                kernel, catalogue, git_repository, 
                document.branch or "main", readme
            )
            
            # 步骤5: 处理待处理文档
            logger.info("步骤5: 处理待处理文档")
            await DocumentPendingService.process_pending_documents_async(
                kernel, catalogue, git_repository, 
                document.branch or "main", readme
            )
            
            logger.info(f"文档处理完成: {document.title}")
            
        except Exception as e:
            logger.error(f"文档处理失败: {document.title}, 错误: {str(e)}")
            raise
    
    async def generate_readme(
        self, 
        warehouse: Warehouse, 
        path: str
    ) -> str:
        """生成README文档"""
        try:
            # 检查是否存在README文件
            readme_files = [
                "README.md", "readme.md", "README.txt", "readme.txt",
                "README", "readme"
            ]
            
            for readme_file in readme_files:
                readme_path = os.path.join(path, readme_file)
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            # 如果没有找到README文件，生成一个基础的
            return f"# {warehouse.name}\n\n{warehouse.description or '暂无描述'}"
            
        except Exception as e:
            logger.error(f"生成README失败: {str(e)}")
            return f"# {warehouse.name}\n\n{warehouse.description or '暂无描述'}"
    
    async def get_catalogue_smart_filter_optimized_async(
        self, 
        path: str, 
        readme: str, 
        format: str = "compact"
    ) -> str:
        """智能过滤生成优化的目录结构"""
        try:
            # 获取目录下的所有文件
            file_list = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, path)
                    file_list.append(relative_path)
            
            # 过滤掉不需要的文件
            filtered_files = []
            exclude_patterns = [
                r'\.git', r'\.vscode', r'\.idea', r'node_modules',
                r'\.DS_Store', r'Thumbs\.db', r'\.log$', r'\.tmp$',
                r'\.cache', r'\.env', r'\.pyc$', r'__pycache__'
            ]
            
            for file_path in file_list:
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, file_path, re.IGNORECASE):
                        should_exclude = True
                        break
                
                if not should_exclude:
                    filtered_files.append(file_path)
            
            # 构建目录结构字符串
            catalogue_lines = []
            for file_path in sorted(filtered_files):
                # 计算缩进级别
                indent_level = file_path.count('/') + file_path.count('\\')
                indent = "  " * indent_level
                
                # 判断是文件还是目录
                full_path = os.path.join(path, file_path)
                if os.path.isdir(full_path):
                    catalogue_lines.append(f"{indent}{os.path.basename(file_path)}/")
                else:
                    catalogue_lines.append(f"{indent}{os.path.basename(file_path)}")
            
            return "\n".join(catalogue_lines)
            
        except Exception as e:
            logger.error(f"生成目录结构失败: {str(e)}")
            return ""
    
    async def get_catalogue_smart_filter_async(
        self, 
        path: str, 
        readme: str
    ) -> str:
        """智能过滤生成目录结构（简化版本）"""
        return await self.get_catalogue_smart_filter_optimized_async(path, readme) 