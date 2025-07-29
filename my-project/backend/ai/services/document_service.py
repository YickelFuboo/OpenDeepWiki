import logging
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from config import get_settings
from models.warehouse import Warehouse
from models.document import Document, DocumentCatalog
from ..core.kernel_factory import KernelFactory

logger = logging.getLogger(__name__)


class DocumentService:
    """文档服务类，负责文档生成和处理"""
    
    def __init__(self, db: Session):
        """
        初始化文档服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.settings = get_settings()
    
    async def generate_readme(self, warehouse: Warehouse, git_path: str) -> str:
        """
        生成README文档
        
        Args:
            warehouse: 仓库信息
            git_path: Git仓库路径
            
        Returns:
            生成的README内容
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_file_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=git_path,
                model=self.settings.analysis_model
            )
            
            # 获取目录结构
            from ..functions.file_function import FileFunction
            file_function = FileFunction(git_path)
            tree = file_function.get_tree()
            
            # 构建README生成提示词
            prompt = f"""
            请根据以下仓库信息生成README文档：
            
            仓库名称：{warehouse.name}
            仓库地址：{warehouse.address}
            分支：{warehouse.branch}
            目录结构：
            {tree}
            
            请生成一个完整的README文档，包含：
            1. 项目简介
            2. 功能特性
            3. 安装说明
            4. 使用方法
            5. 贡献指南
            6. 许可证信息
            """
            
            # 调用AI模型生成README
            result = await self._invoke_ai_model(kernel, prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"README生成失败: {e}")
            return f"README生成失败: {str(e)}"
    
    async def generate_catalogue(self, git_path: str, readme: str) -> str:
        """
        生成目录结构分析
        
        Args:
            git_path: Git仓库路径
            readme: README内容
            
        Returns:
            生成的目录结构分析
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=git_path,
                model=self.settings.analysis_model
            )
            
            # 获取目录结构
            from ..functions.file_function import FileFunction
            file_function = FileFunction(git_path)
            tree = file_function.get_tree()
            
            # 构建目录分析提示词
            prompt = f"""
            请分析以下项目的目录结构：
            
            README内容：
            {readme}
            
            目录结构：
            {tree}
            
            请提供：
            1. 项目结构分析
            2. 主要模块说明
            3. 文件组织逻辑
            4. 架构设计分析
            """
            
            # 调用AI模型分析目录
            result = await self._invoke_ai_model(kernel, prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"目录结构分析失败: {e}")
            return f"目录结构分析失败: {str(e)}"
    
    async def generate_project_overview(self, warehouse: Warehouse, catalogue: str, readme: str) -> str:
        """
        生成项目概述
        
        Args:
            warehouse: 仓库信息
            catalogue: 目录结构
            readme: README内容
            
        Returns:
            生成的项目概述
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=warehouse.local_path,
                model=self.settings.analysis_model
            )
            
            # 构建项目概述提示词
            prompt = f"""
            请根据以下信息生成项目概述：
            
            仓库信息：
            - 名称：{warehouse.name}
            - 地址：{warehouse.address}
            - 分支：{warehouse.branch}
            
            README内容：
            {readme}
            
            目录结构：
            {catalogue}
            
            请生成一个详细的项目概述，包含：
            1. 项目背景和目标
            2. 技术栈分析
            3. 核心功能说明
            4. 项目特色
            5. 应用场景
            """
            
            # 调用AI模型生成项目概述
            result = await self._invoke_ai_model(kernel, prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"项目概述生成失败: {e}")
            return f"项目概述生成失败: {str(e)}"
    
    async def generate_document_catalog(self, git_path: str, warehouse: Warehouse, catalogue: str) -> List[DocumentCatalog]:
        """
        生成文档目录
        
        Args:
            git_path: Git仓库路径
            warehouse: 仓库信息
            catalogue: 目录结构
            
        Returns:
            生成的文档目录列表
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=git_path,
                model=self.settings.analysis_model
            )
            
            # 构建文档目录生成提示词
            prompt = f"""
            请根据以下信息生成文档目录结构：
            
            仓库信息：
            - 名称：{warehouse.name}
            - 地址：{warehouse.address}
            
            目录结构：
            {catalogue}
            
            请生成一个完整的文档目录结构，包含：
            1. 主要功能模块文档
            2. API文档
            3. 配置说明文档
            4. 部署文档
            5. 开发指南
            6. 故障排除文档
            
            请以JSON格式返回，包含每个文档的标题、描述和优先级。
            """
            
            # 调用AI模型生成文档目录
            result = await self._invoke_ai_model(kernel, prompt)
            
            # 解析JSON结果
            try:
                catalog_data = json.loads(result)
                document_catalogs = []
                
                for item in catalog_data.get("documents", []):
                    catalog = DocumentCatalog(
                        id=item.get("id"),
                        title=item.get("title"),
                        description=item.get("description"),
                        priority=item.get("priority", 1),
                        status="pending",
                        warehouse_id=warehouse.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    document_catalogs.append(catalog)
                
                return document_catalogs
                
            except json.JSONDecodeError:
                logger.error("解析文档目录JSON失败")
                return []
            
        except Exception as e:
            logger.error(f"文档目录生成失败: {e}")
            return []
    
    async def generate_document_content(self, catalog: DocumentCatalog, git_path: str) -> str:
        """
        生成文档内容
        
        Args:
            catalog: 文档目录
            git_path: Git仓库路径
            
        Returns:
            生成的文档内容
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_file_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path=git_path,
                model=self.settings.chat_model
            )
            
            # 构建文档内容生成提示词
            prompt = f"""
            请根据以下信息生成文档内容：
            
            文档标题：{catalog.title}
            文档描述：{catalog.description}
            
            请生成一个详细的文档内容，包含：
            1. 概述
            2. 详细说明
            3. 使用示例
            4. 注意事项
            5. 相关链接
            
            请使用Markdown格式。
            """
            
            # 调用AI模型生成文档内容
            result = await self._invoke_ai_model(kernel, prompt)
            
            return result
            
        except Exception as e:
            logger.error(f"文档内容生成失败: {e}")
            return f"文档内容生成失败: {str(e)}"
    
    async def _invoke_ai_model(self, kernel, prompt: str) -> str:
        """
        调用AI模型
        
        Args:
            kernel: AI内核
            prompt: 提示词
            
        Returns:
            AI模型响应
        """
        try:
            from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
            
            # 获取聊天完成服务
            chat_service = kernel.get_service(ChatCompletionClientBase)
            
            # 调用AI模型
            messages = [{"role": "user", "content": prompt}]
            response = await chat_service.complete_chat(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            raise 