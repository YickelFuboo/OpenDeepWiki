import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase

from config import get_settings
from ..core.kernel_factory import KernelFactory

logger = logging.getLogger(__name__)


class AIService:
    """AI服务类，提供各种AI功能的核心服务"""
    
    def __init__(self, db: Session):
        """
        初始化AI服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.settings = get_settings()
    
    async def analyze_code(self, code_content: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        分析代码
        
        Args:
            code_content: 代码内容
            language: 编程语言
            
        Returns:
            代码分析结果
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",  # 临时路径
                model=self.settings.analysis_model
            )
            
            # 构建分析提示词
            prompt = f"""
            请分析以下代码：
            
            语言：{language or '未知'}
            代码：
            {code_content}
            
            请提供以下分析：
            1. 代码功能描述
            2. 代码结构分析
            3. 潜在问题和改进建议
            4. 复杂度评估
            """
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "analysis": result,
                "language": language
            }
            
        except Exception as e:
            logger.error(f"代码分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_documentation(self, code_content: str, doc_type: str = "markdown") -> Dict[str, Any]:
        """
        生成文档
        
        Args:
            code_content: 代码内容
            doc_type: 文档类型
            
        Returns:
            生成的文档
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.analysis_model
            )
            
            # 构建文档生成提示词
            prompt = f"""
            请为以下代码生成{doc_type}格式的文档：
            
            {code_content}
            
            请包含：
            1. 功能描述
            2. 参数说明
            3. 返回值说明
            4. 使用示例
            5. 注意事项
            """
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "documentation": result,
                "doc_type": doc_type
            }
            
        except Exception as e:
            logger.error(f"文档生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def chat(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        与AI对话
        
        Args:
            message: 用户消息
            context: 上下文信息
            
        Returns:
            对话结果
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.chat_model
            )
            
            # 构建对话提示词
            prompt = message
            if context:
                prompt = f"上下文：{context}\n\n用户问题：{message}"
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "response": result,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_code(self, query: str, warehouse_id: Optional[str] = None) -> Dict[str, Any]:
        """
        搜索代码
        
        Args:
            query: 搜索查询
            warehouse_id: 仓库ID
            
        Returns:
            搜索结果
        """
        try:
            # 如果有仓库ID，使用RAG搜索
            if warehouse_id:
                from ..functions.rag_function import RagFunction
                rag = RagFunction(warehouse_id)
                result = await rag.search(query)
                await rag.close()
                return {
                    "success": True,
                    "results": result,
                    "query": query,
                    "warehouse_id": warehouse_id
                }
            
            # 否则使用普通AI搜索
            kernel = KernelFactory.get_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.chat_model
            )
            
            prompt = f"请搜索与以下查询相关的代码：{query}"
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "results": result,
                "query": query
            }
            
        except Exception as e:
            logger.error(f"代码搜索失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def explain_code(self, code_content: str) -> Dict[str, Any]:
        """
        解释代码
        
        Args:
            code_content: 代码内容
            
        Returns:
            代码解释
        """
        try:
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.analysis_model
            )
            
            prompt = f"""
            请详细解释以下代码：
            
            {code_content}
            
            请包含：
            1. 代码功能说明
            2. 逐行解释
            3. 关键概念说明
            4. 可能的改进建议
            """
            
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "explanation": result
            }
            
        except Exception as e:
            logger.error(f"代码解释失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_code(self, code_content: str, optimization_type: str = "performance") -> Dict[str, Any]:
        """
        优化代码
        
        Args:
            code_content: 代码内容
            optimization_type: 优化类型
            
        Returns:
            优化后的代码
        """
        try:
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.analysis_model
            )
            
            prompt = f"""
            请对以下代码进行{optimization_type}优化：
            
            {code_content}
            
            请提供：
            1. 优化后的代码
            2. 优化说明
            3. 性能提升分析
            """
            
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "optimized_code": result,
                "optimization_type": optimization_type
            }
            
        except Exception as e:
            logger.error(f"代码优化失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_tests(self, code_content: str, test_framework: str = "pytest") -> Dict[str, Any]:
        """
        生成测试代码
        
        Args:
            code_content: 代码内容
            test_framework: 测试框架
            
        Returns:
            生成的测试代码
        """
        try:
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=self.settings.analysis_model
            )
            
            prompt = f"""
            请为以下代码生成{test_framework}测试：
            
            {code_content}
            
            请包含：
            1. 单元测试
            2. 集成测试
            3. 边界条件测试
            4. 测试说明
            """
            
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "tests": result,
                "test_framework": test_framework
            }
            
        except Exception as e:
            logger.error(f"测试代码生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _invoke_ai_model(self, kernel: Kernel, prompt: str) -> str:
        """
        调用AI模型
        
        Args:
            kernel: AI内核
            prompt: 提示词
            
        Returns:
            AI模型响应
        """
        try:
            # 获取聊天完成服务
            chat_service = kernel.get_service(ChatCompletionClientBase)
            
            # 调用AI模型
            messages = [{"role": "user", "content": prompt}]
            response = await chat_service.complete_chat(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            raise 