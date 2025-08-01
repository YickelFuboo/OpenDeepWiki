import json
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import openai
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.prompt_template import PromptTemplateConfig

from src.core.config import settings
from src.models.repository import Repository
from src.models.document import Document
from src.dto.ai_dto import ResponsesInput, ChatMessage
from src.services.kernel_factory import KernelFactory


class AIService:
    """AI服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.kernel_factory = KernelFactory()
    
    async def process_responses(self, responses_input: ResponsesInput) -> Dict[str, Any]:
        """处理AI响应请求"""
        try:
            # 查找仓库
            warehouse = await self._get_warehouse(
                responses_input.organization_name, 
                responses_input.name
            )
            if not warehouse:
                return {
                    "message": "Warehouse not found",
                    "code": 404
                }
            
            # 查找文档
            document = await self._get_document(warehouse.id)
            if not document:
                return {
                    "message": "Document not found", 
                    "code": 404
                }
            
            # 创建AI内核
            kernel = await self.kernel_factory.get_kernel(
                chat_endpoint=settings.openai.endpoint,
                api_key=settings.openai.chat_api_key,
                git_path=document.file_path or "",
                model=settings.openai.chat_model,
                is_code_analysis=False
            )
            
            # 处理消息
            if responses_input.messages:
                return await self._process_chat_messages(kernel, responses_input.messages)
            else:
                return await self._process_simple_query(kernel, responses_input.query)
                
        except Exception as e:
            logger.error(f"AI响应处理错误: {e}")
            return {
                "message": f"处理请求时发生错误: {str(e)}",
                "code": 500
            }
    
    async def _get_warehouse(self, organization_name: str, name: str) -> Optional[Repository]:
        """获取仓库信息"""
        result = await self.db.execute(
            select(Repository).where(
                Repository.organization_name.ilike(organization_name),
                Repository.name.ilike(name)
            )
        )
        return result.scalar_one_or_none()
    
    async def _get_document(self, warehouse_id: str) -> Optional[Document]:
        """获取文档信息"""
        result = await self.db.execute(
            select(Document).where(Document.repository_id == warehouse_id)
        )
        return result.scalar_one_or_none()
    
    async def _process_chat_messages(self, kernel: Kernel, messages: List[ChatMessage]) -> Dict[str, Any]:
        """处理聊天消息"""
        try:
            # 构建聊天历史
            chat_history = []
            for message in messages:
                if message.role == "user":
                    chat_history.append({"role": "user", "content": message.content})
                elif message.role == "assistant":
                    chat_history.append({"role": "assistant", "content": message.content})
            
            # 调用AI模型
            chat_service = kernel.get_service(OpenAIChatCompletion)
            
            # 构建系统提示词
            system_prompt = """你是一个智能代码分析助手，可以帮助用户分析代码仓库、回答技术问题、生成文档等。
请根据用户的问题提供准确、有用的回答。"""
            
            # 调用AI服务
            response = await chat_service.complete_chat(
                messages=chat_history,
                settings={
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            return {
                "message": "success",
                "code": 200,
                "data": {
                    "response": response.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"处理聊天消息错误: {e}")
            return {
                "message": f"处理聊天消息时发生错误: {str(e)}",
                "code": 500
            }
    
    async def _process_simple_query(self, kernel: Kernel, query: str) -> Dict[str, Any]:
        """处理简单查询"""
        try:
            # 调用AI模型
            chat_service = kernel.get_service(OpenAIChatCompletion)
            
            # 构建消息
            messages = [
                {"role": "system", "content": "你是一个智能代码分析助手。"},
                {"role": "user", "content": query}
            ]
            
            # 调用AI服务
            response = await chat_service.complete_chat(
                messages=messages,
                settings={
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            return {
                "message": "success",
                "code": 200,
                "data": {
                    "response": response.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"处理简单查询错误: {e}")
            return {
                "message": f"处理查询时发生错误: {str(e)}",
                "code": 500
            }
    
    async def generate_project_overview(self, repository_path: str, catalog: str, 
                                      git_repository: str, branch: str, readme: str) -> str:
        """生成项目概述"""
        try:
            # 创建AI内核
            kernel = await self.kernel_factory.get_kernel(
                chat_endpoint=settings.openai.endpoint,
                api_key=settings.openai.chat_api_key,
                git_path=repository_path,
                model=settings.openai.chat_model,
                is_code_analysis=True
            )
            
            # 构建提示词
            prompt = f"""请根据以下信息生成项目概述：

项目目录结构：
{catalog}

Git仓库：{git_repository}
分支：{branch}

README内容：
{readme}

请生成一个详细的项目概述，包括：
1. 项目简介
2. 主要功能
3. 技术栈
4. 项目结构
5. 使用说明
"""
            
            # 调用AI服务
            chat_service = kernel.get_service(OpenAIChatCompletion)
            response = await chat_service.complete_chat(
                messages=[{"role": "user", "content": prompt}],
                settings={
                    "temperature": 0.7,
                    "max_tokens": 3000
                }
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"生成项目概述错误: {e}")
            return f"生成项目概述时发生错误: {str(e)}"
    
    async def analyze_code_structure(self, repository_path: str) -> Dict[str, Any]:
        """分析代码结构"""
        try:
            # 创建AI内核
            kernel = await self.kernel_factory.get_kernel(
                chat_endpoint=settings.openai.endpoint,
                api_key=settings.openai.chat_api_key,
                git_path=repository_path,
                model=settings.openai.chat_model,
                is_code_analysis=True
            )
            
            # 获取目录结构
            file_function = kernel.get_function("FileFunction", "GetTree")
            tree_result = await kernel.invoke(file_function)
            
            # 分析代码结构
            prompt = f"""请分析以下代码仓库的结构：

{tree_result}

请提供：
1. 项目类型和主要技术栈
2. 目录结构分析
3. 主要模块说明
4. 代码组织特点
"""
            
            chat_service = kernel.get_service(OpenAIChatCompletion)
            response = await chat_service.complete_chat(
                messages=[{"role": "user", "content": prompt}],
                settings={
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            return {
                "tree_structure": tree_result,
                "analysis": response.content
            }
            
        except Exception as e:
            logger.error(f"分析代码结构错误: {e}")
            return {
                "error": f"分析代码结构时发生错误: {str(e)}"
            } 