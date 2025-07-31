"""
AI响应服务

提供AI响应处理和流式响应功能
"""

import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from app.ai.core.kernel_factory import KernelFactory
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class ResponsesService:
    """AI响应服务"""
    
    def __init__(self):
        self.settings = get_settings()
    
    async def generate_streaming_response(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        生成流式响应
        
        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            
        Yields:
            流式响应内容
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=model
            )
            
            # 构建流式响应
            async for chunk in self._stream_ai_response(kernel, prompt, max_tokens, temperature):
                yield chunk
                
        except Exception as e:
            logger.error(f"生成流式响应失败: {e}")
            error_response = {
                "type": "error",
                "content": f"生成响应失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
    
    async def generate_structured_response(
        self,
        prompt: str,
        model: str = "gpt-4",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        生成结构化响应
        
        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            结构化响应
        """
        try:
            # 创建AI内核
            kernel = KernelFactory.get_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=model
            )
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt, max_tokens, temperature)
            
            return {
                "success": True,
                "response": result,
                "model": model,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"生成结构化响应失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "model": model,
                "prompt": prompt
            }
    
    async def generate_code_analysis_response(
        self,
        code_content: str,
        analysis_type: str = "structure",
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        生成代码分析响应
        
        Args:
            code_content: 代码内容
            analysis_type: 分析类型
            model: 模型名称
            
        Returns:
            代码分析响应
        """
        try:
            # 创建代码分析专用的AI内核
            kernel = KernelFactory.get_analysis_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=model
            )
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(code_content, analysis_type)
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "analysis": result,
                "analysis_type": analysis_type,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"生成代码分析响应失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": analysis_type,
                "model": model
            }
    
    async def generate_documentation_response(
        self,
        content: str,
        doc_type: str = "readme",
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        生成文档响应
        
        Args:
            content: 内容
            doc_type: 文档类型
            model: 模型名称
            
        Returns:
            文档响应
        """
        try:
            # 创建文档生成专用的AI内核
            kernel = KernelFactory.get_file_kernel(
                chat_endpoint=self.settings.endpoint,
                api_key=self.settings.chat_api_key,
                git_path="./temp",
                model=model
            )
            
            # 构建文档生成提示词
            prompt = self._build_documentation_prompt(content, doc_type)
            
            # 调用AI模型
            result = await self._invoke_ai_model(kernel, prompt)
            
            return {
                "success": True,
                "documentation": result,
                "doc_type": doc_type,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"生成文档响应失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "doc_type": doc_type,
                "model": model
            }
    
    async def _stream_ai_response(
        self,
        kernel,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """流式AI响应"""
        try:
            # 发送开始信号
            start_response = {
                "type": "start",
                "content": "开始生成响应..."
            }
            yield f"data: {json.dumps(start_response, ensure_ascii=False)}\n\n"
            
            # 模拟流式响应（实际项目中需要调用真实的流式API）
            words = prompt.split()
            for i, word in enumerate(words):
                progress_response = {
                    "type": "progress",
                    "content": word,
                    "progress": (i + 1) / len(words)
                }
                yield f"data: {json.dumps(progress_response, ensure_ascii=False)}\n\n"
                
                # 模拟延迟
                import asyncio
                await asyncio.sleep(0.1)
            
            # 发送完成信号
            complete_response = {
                "type": "complete",
                "content": "响应生成完成"
            }
            yield f"data: {json.dumps(complete_response, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式AI响应失败: {e}")
            error_response = {
                "type": "error",
                "content": f"流式响应失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_response, ensure_ascii=False)}\n\n"
    
    async def _invoke_ai_model(self, kernel, prompt: str, max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """调用AI模型"""
        try:
            # 这里应该调用真实的AI模型
            # 目前返回模拟响应
            return f"这是对以下提示词的AI响应：\n\n{prompt}\n\n这是一个模拟的AI响应内容。"
            
        except Exception as e:
            logger.error(f"AI模型调用失败: {e}")
            raise Exception(f"AI模型调用失败: {str(e)}")
    
    def _build_analysis_prompt(self, code_content: str, analysis_type: str) -> str:
        """构建代码分析提示词"""
        if analysis_type == "structure":
            return f"""
请分析以下代码的结构：

{code_content}

请提供：
1. 代码结构分析
2. 主要功能说明
3. 代码质量评估
4. 改进建议
"""
        elif analysis_type == "performance":
            return f"""
请分析以下代码的性能：

{code_content}

请提供：
1. 性能瓶颈分析
2. 优化建议
3. 复杂度分析
4. 最佳实践建议
"""
        else:
            return f"""
请分析以下代码：

{code_content}

请提供全面的代码分析。
"""
    
    def _build_documentation_prompt(self, content: str, doc_type: str) -> str:
        """构建文档生成提示词"""
        if doc_type == "readme":
            return f"""
请为以下内容生成README文档：

{content}

请生成包含以下部分的README：
1. 项目简介
2. 安装说明
3. 使用方法
4. 功能特性
5. 贡献指南
"""
        elif doc_type == "api":
            return f"""
请为以下内容生成API文档：

{content}

请生成包含以下部分的API文档：
1. 接口概述
2. 请求参数
3. 响应格式
4. 错误码
5. 示例代码
"""
        else:
            return f"""
请为以下内容生成文档：

{content}

请生成合适的文档格式。
""" 