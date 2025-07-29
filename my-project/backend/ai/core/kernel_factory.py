import os
import logging
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion
from semantic_kernel.plugins.core import KernelPlugin
from semantic_kernel.plugins.core.code_interpreter import CodeInterpreterPlugin

from config import get_settings

logger = logging.getLogger(__name__)


class KernelFactory:
    """AI内核工厂类，负责创建和配置Semantic Kernel实例"""
    
    @staticmethod
    def get_kernel(
        chat_endpoint: str,
        api_key: str,
        git_path: str,
        model: str = "gpt-4",
        is_code_analysis: bool = True
    ) -> Kernel:
        """
        创建和配置AI内核实例
        
        Args:
            chat_endpoint: AI服务的端点URL
            api_key: API密钥
            git_path: Git仓库的本地路径
            model: AI模型名称
            is_code_analysis: 是否启用代码分析功能
            
        Returns:
            配置完成的AI内核实例
        """
        settings = get_settings()
        
        logger.info(f"创建AI内核: model={model}, provider={settings.model_provider}")
        
        # 创建内核实例
        kernel = Kernel()
        
        # 根据模型提供商配置聊天完成服务
        if settings.model_provider.lower() == "openai":
            kernel.add_service(
                OpenAIChatCompletion(
                    service_id="chat",
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=chat_endpoint
                )
            )
        elif settings.model_provider.lower() == "azureopenai":
            kernel.add_service(
                AzureChatCompletion(
                    service_id="chat",
                    deployment_name=model,
                    endpoint=chat_endpoint,
                    api_key=api_key
                )
            )
        elif settings.model_provider.lower() == "anthropic":
            kernel.add_service(
                AnthropicChatCompletion(
                    service_id="chat",
                    model_id=model,
                    api_key=api_key
                )
            )
        else:
            raise ValueError(f"不支持的模型提供商: {settings.model_provider}")
        
        # 添加文件操作插件
        from ..functions.file_function import FileFunction
        file_function = FileFunction(git_path)
        kernel.add_plugin(file_function)
        
        # 如果启用代码分析，添加代码分析插件
        if is_code_analysis and settings.enable_code_dependency_analysis:
            from ..functions.code_analyze_function import CodeAnalyzeFunction
            code_analyze_function = CodeAnalyzeFunction(git_path)
            kernel.add_plugin(code_analyze_function)
        
        # 添加代码解释器插件
        code_interpreter = CodeInterpreterPlugin()
        kernel.add_plugin(code_interpreter)
        
        logger.info("AI内核创建完成")
        return kernel
    
    @staticmethod
    def get_file_kernel(
        chat_endpoint: str,
        api_key: str,
        git_path: str,
        model: str = "gpt-4"
    ) -> Kernel:
        """
        创建文件操作专用的AI内核实例（禁用某些功能以提高性能）
        
        Args:
            chat_endpoint: AI服务的端点URL
            api_key: API密钥
            git_path: Git仓库的本地路径
            model: AI模型名称
            
        Returns:
            配置完成的文件操作AI内核实例
        """
        return KernelFactory.get_kernel(
            chat_endpoint=chat_endpoint,
            api_key=api_key,
            git_path=git_path,
            model=model,
            is_code_analysis=False
        )
    
    @staticmethod
    def get_analysis_kernel(
        chat_endpoint: str,
        api_key: str,
        git_path: str,
        model: str = "gpt-4"
    ) -> Kernel:
        """
        创建代码分析专用的AI内核实例
        
        Args:
            chat_endpoint: AI服务的端点URL
            api_key: API密钥
            git_path: Git仓库的本地路径
            model: AI模型名称
            
        Returns:
            配置完成的代码分析AI内核实例
        """
        return KernelFactory.get_kernel(
            chat_endpoint=chat_endpoint,
            api_key=api_key,
            git_path=git_path,
            model=model,
            is_code_analysis=True
        ) 