import re
import asyncio
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger
from semantic_kernel import Kernel
from semantic_kernel.connectors.openai import OpenAIPromptExecutionSettings

from src.services.prompt_service import PromptService
from src.koala_warehouse.warehouse_classify import ClassifyType
from src.models.warehouse import Warehouse
from src.models.document_catalog import DocumentCatalog, DocumentFileItem, DocumentFileItemSource
from src.conf.settings import settings


@dataclass
class DocumentStore:
    """文档存储"""
    files: List[str] = field(default_factory=list)


@dataclass
class DocumentContext:
    """文档上下文"""
    document_store: DocumentStore = field(default_factory=DocumentStore)


class DocumentPendingService:
    """文档待处理服务"""
    
    def __init__(self):
        self.prompt_service = PromptService()
        # 从环境变量读取任务最大并发数
        self.task_max_size_per_user = int(os.getenv("TASK_MAX_SIZE_PER_USER", "5"))
    
    async def handle_pending_documents_async(
        self,
        documents: List[DocumentCatalog],
        file_kernel: Kernel,
        catalogue: str,
        git_repository: str,
        warehouse: Warehouse,
        path: str,
        db: AsyncSession,
        classify_type: Optional[ClassifyType] = None
    ):
        """处理文档生成"""
        try:
            # 创建信号量控制并发
            semaphore = asyncio.Semaphore(self.task_max_size_per_user)
            
            # 等待中的任务列表
            pending_documents = documents.copy()
            running_tasks = []
            
            # 开始处理文档，直到所有文档都处理完成
            while pending_documents or running_tasks:
                # 尝试启动新任务，直到达到并发限制
                while pending_documents and len(running_tasks) < self.task_max_size_per_user:
                    document_catalog = pending_documents.pop(0)
                    
                    task = self._process_document_async(
                        document_catalog, file_kernel, catalogue, git_repository,
                        warehouse.branch, path, semaphore, classify_type
                    )
                    running_tasks.append(task)
                    
                    # 延迟避免过于频繁的任务启动
                    await asyncio.sleep(1)
                
                # 如果没有正在运行的任务，退出循环
                if not running_tasks:
                    break
                
                # 等待任意一个任务完成
                done, pending = await asyncio.wait(
                    running_tasks, 
                    return_when=asyncio.FIRST_COMPLETED
                )
                running_tasks = list(pending)
                
                for task in done:
                    try:
                        catalog, file_item, files = await task
                        
                        if file_item is None:
                            logger.error(f"处理仓库 {path}, 处理标题 {catalog.name} 失败: 文件内容为空")
                            raise Exception(f"处理失败，文件内容为空: {catalog.name}")
                        
                        # 更新文档状态
                        await db.execute(
                            update(DocumentCatalog)
                            .where(DocumentCatalog.id == catalog.id)
                            .values(is_completed=True)
                        )
                        
                        # 修复Mermaid语法错误
                        self._repair_mermaid(file_item)
                        
                        # 保存文件项
                        db.add(file_item)
                        
                        # 保存文件源
                        for file_path in files:
                            file_source = DocumentFileItemSource(
                                address=file_path,
                                document_file_item_id=file_item.id,
                                name=file_path,
                                id=self._generate_id()
                            )
                            db.add(file_source)
                        
                        await db.commit()
                        
                        logger.info(f"处理仓库 {path}, 处理标题 {catalog.name} 完成并保存到数据库！")
                        
                    except Exception as e:
                        logger.error(f"处理文档失败: {e}")
                        await db.rollback()
                        
        except Exception as e:
            logger.error(f"处理待处理文档失败: {e}")
            raise
    
    async def _process_document_async(
        self,
        catalog: DocumentCatalog,
        kernel: Kernel,
        catalogue: str,
        git_repository: str,
        branch: str,
        path: str,
        semaphore: asyncio.Semaphore,
        classify_type: Optional[ClassifyType] = None
    ) -> Tuple[DocumentCatalog, Optional[DocumentFileItem], List[str]]:
        """处理单个文档的异步方法"""
        retry_count = 0
        max_retries = 5
        files = []
        
        while True:
            try:
                async with semaphore:
                    logger.info(f"处理仓库 {path}, 处理标题 {catalog.name}")
                    
                    file_item = await self._process_catalogue_items(
                        catalog, kernel, catalogue, git_repository, branch, path, classify_type
                    )
                    
                    # 获取文档存储的文件列表
                    files = DocumentContext().document_store.files.copy()
                    
                    logger.info(f"处理仓库 {path}, 处理标题 {catalog.name} 完成！")
                    
                    return catalog, file_item, files
                    
            except Exception as e:
                logger.error(f"处理仓库 {path}, 处理标题 {catalog.name} 失败: {e}")
                
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"处理 {catalog.name} 失败，已重试 {retry_count} 次，错误：{e}")
                    raise
                else:
                    # 等待一段时间后重试
                    await asyncio.sleep(10 * retry_count)
    
    async def _process_catalogue_items(
        self,
        catalog: DocumentCatalog,
        kernel: Kernel,
        catalogue: str,
        git_repository: str,
        branch: str,
        path: str,
        classify: Optional[ClassifyType] = None
    ) -> DocumentFileItem:
        """处理每一个标题产生文件内容"""
        try:
            # 构建提示词名称
            prompt_name = "GenerateDocs"
            if classify:
                prompt_name += classify.value
            
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Warehouse", prompt_name)
            if not prompt_template:
                prompt_template = """
                请根据以下信息生成文档内容：
                
                目录结构：{catalogue}
                提示词：{prompt}
                仓库地址：{git_repository}
                分支名称：{branch}
                标题：{title}
                
                请生成详细的文档内容，使用Markdown格式。
                """
            
            # 构建提示词参数
            prompt_args = {
                "catalogue": catalogue,
                "prompt": catalog.prompt,
                "git_repository": git_repository.replace(".git", ""),
                "branch": branch,
                "title": catalog.name
            }
            
            # 替换提示词中的参数
            prompt = prompt_template.format(**prompt_args)
            
            # 配置执行设置
            execution_settings = OpenAIPromptExecutionSettings(
                max_tokens=self._get_max_tokens(settings.openai.chat_model),
                temperature=0.5
            )
            
            # 执行提示词
            response = await kernel.invoke(prompt, execution_settings=execution_settings)
            content = str(response)
            
            # 如果需要优化质量
            if hasattr(settings, 'refine_and_enhance_quality') and settings.refine_and_enhance_quality:
                refine_prompt = """
                You need to further refine the previous content and provide more detailed information. All the content comes from the code repository and the style of the documentation should be more standardized.
                Create thorough documentation that:
                - Covers all key functionality with precise technical details
                - Includes practical code examples and usage patterns  
                - Ensures completeness without gaps or omissions
                - Maintains clarity and professional quality throughout
                Please do your best and spare no effort.
                """
                
                refine_response = await kernel.invoke(refine_prompt, execution_settings=execution_settings)
                content = str(refine_response)
            
            # 删除thinking标签内容
            thinking_pattern = r'<thinking>.*?</thinking>'
            content = re.sub(thinking_pattern, '', content, flags=re.DOTALL)
            
            # 提取<blog></blog>中的内容
            blog_pattern = r'<blog>(.*?)</blog>'
            blog_match = re.search(blog_pattern, content, re.DOTALL)
            
            if blog_match:
                content = blog_match.group(1)
            
            content = content.strip()
            
            # 删除<think></think>标签
            think_pattern = r'<think>(.*?)</think>'
            content = re.sub(think_pattern, '', content, flags=re.DOTALL)
            
            # 从docs提取
            docs_pattern = r'<docs>(.*?)</docs>'
            docs_match = re.search(docs_pattern, content, re.DOTALL)
            if docs_match:
                extracted_docs = docs_match.group(1)
                content = content.replace(docs_match.group(0), extracted_docs)
            
            # 创建文件项
            file_item = DocumentFileItem(
                content=content,
                document_catalog_id=catalog.id,
                description="",
                extra={},
                metadata={},
                source=[],
                comment_count=0,
                request_token=0,
                created_at=datetime.now(),
                id=self._generate_id(),
                response_token=0,
                size=0,
                title=catalog.name
            )
            
            return file_item
            
        except Exception as e:
            logger.error(f"处理目录项失败: {e}")
            raise
    
    def _repair_mermaid(self, file_item: DocumentFileItem):
        """修复Mermaid语法错误"""
        try:
            mermaid_pattern = r'```mermaid\s*([\s\S]*?)```'
            matches = re.finditer(mermaid_pattern, file_item.content, re.MULTILINE)
            
            for match in matches:
                code = match.group(1)
                
                # 删除[]里面的(和)
                code_without_brackets = re.sub(
                    r'\[[^\]]*\]',
                    lambda m: m.group(0).replace('(', '').replace(')', '').replace('（', '').replace('）', ''),
                    code
                )
                
                # 替换原有内容
                file_item.content = file_item.content.replace(
                    match.group(0), 
                    f"```mermaid\n{code_without_brackets}```"
                )
                
        except Exception as e:
            logger.error(f"修复mermaid语法失败: {e}")
    
    def _get_max_tokens(self, model: str) -> int:
        """获取模型的最大token数"""
        token_limits = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384
        }
        return token_limits.get(model, 4096)
    
    def _generate_id(self) -> str:
        """生成ID"""
        import uuid
        return uuid.uuid4().hex 