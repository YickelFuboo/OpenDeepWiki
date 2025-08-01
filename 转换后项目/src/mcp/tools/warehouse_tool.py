import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from src.models.warehouse import Warehouse
from src.models.document import Document
from src.models.mcp_history import MCPHistory
from src.services.kernel_factory import KernelFactory
from src.services.prompt_service import PromptService
from src.core.config import settings


class WarehouseTool:
    """仓库工具"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.prompt_service = PromptService()
    
    async def generate_document(self, question: str, owner: str = "", name: str = "") -> str:
        """生成仓库文档"""
        try:
            # 查找仓库
            warehouse_result = await self.db.execute(
                select(Warehouse).where(
                    Warehouse.organization_name == owner,
                    Warehouse.name == name
                )
            )
            warehouse = warehouse_result.scalar_one_or_none()
            
            if not warehouse:
                raise Exception(f"抱歉，您的仓库 {owner}/{name} 不存在或已被删除。")
            
            # 查找文档
            document_result = await self.db.execute(
                select(Document).where(Document.warehouse_id == warehouse.id)
            )
            document = document_result.scalar_one_or_none()
            
            if not document:
                raise Exception("抱歉，您的仓库没有文档，请先生成仓库文档。")
            
            # 查找是否有相似的提问
            similar_question_result = await self.db.execute(
                select(MCPHistory).where(
                    MCPHistory.warehouse_id == warehouse.id,
                    MCPHistory.question == question
                ).order_by(MCPHistory.created_at.desc())
            )
            similar_question = similar_question_result.scalar_one_or_none()
            
            # 如果是3天内的提问，直接返回
            if similar_question and (datetime.utcnow() - similar_question.created_at).days < 3:
                return similar_question.answer
            
            # 创建内核
            kernel = await KernelFactory().get_kernel(
                settings.openai.endpoint,
                settings.openai.chat_api_key,
                document.git_path,
                settings.openai.deep_research_model,
                is_code_analysis=False
            )
            
            # 获取README
            readme = await self._generate_readme(warehouse, document.git_path)
            
            # 获取目录结构
            catalogue = warehouse.optimized_directory_structure
            if not catalogue:
                catalogue = await self._get_catalogue_smart_filter(document.git_path, readme)
                if catalogue:
                    # 更新仓库的优化目录结构
                    warehouse.optimized_directory_structure = catalogue
                    await self.db.commit()
            
            # 构建聊天历史
            chat_history = []
            
            # 获取提示词模板
            prompt_template = await self.prompt_service.get_prompt_template("Chat", "Responses")
            if not prompt_template:
                raise Exception("无法获取提示词模板")
            
            # 构建提示词参数
            prompt_args = {
                "catalogue": catalogue,
                "repository_url": warehouse.address,
                "question": question
            }
            
            # 添加用户消息
            user_message = prompt_template.format(**prompt_args)
            chat_history.append({"role": "user", "content": user_message})
            
            # 调用AI生成回答
            response = await self._call_ai_model(kernel, chat_history)
            
            # 保存历史记录
            await self._save_mcp_history(warehouse.id, question, response)
            
            return response
            
        except Exception as e:
            logger.error(f"生成文档失败: {e}")
            raise
    
    async def _generate_readme(self, warehouse: Warehouse, git_path: str) -> str:
        """生成README"""
        try:
            readme_path = os.path.join(git_path, "README.md")
            if os.path.exists(readme_path):
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # 尝试其他README格式
            for ext in [".rst", ".txt", ""]:
                readme_path = os.path.join(git_path, f"README{ext}")
                if os.path.exists(readme_path):
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            return ""
            
        except Exception as e:
            logger.error(f"生成README失败: {e}")
            return ""
    
    async def _get_catalogue_smart_filter(self, git_path: str, readme: str) -> str:
        """获取智能过滤的目录结构"""
        try:
            # 这里实现目录结构的智能过滤
            # 简化实现，实际应该调用AI模型
            return "目录结构"
        except Exception as e:
            logger.error(f"获取目录结构失败: {e}")
            return ""
    
    async def _call_ai_model(self, kernel, chat_history: list) -> str:
        """调用AI模型"""
        try:
            # 这里实现AI模型调用
            # 简化实现，实际应该使用Semantic Kernel
            return "AI生成的回答"
        except Exception as e:
            logger.error(f"调用AI模型失败: {e}")
            return f"生成回答失败: {str(e)}"
    
    async def _save_mcp_history(self, warehouse_id: str, question: str, answer: str):
        """保存MCP历史记录"""
        try:
            history = MCPHistory(
                warehouse_id=warehouse_id,
                question=question,
                answer=answer
            )
            self.db.add(history)
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存MCP历史记录失败: {e}")
            await self.db.rollback() 