import os
import asyncio
from typing import Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.azure_open_ai import AzureOpenAIChatCompletion
from semantic_kernel.connectors.ai.anthropic import AnthropicChatCompletion
from semantic_kernel.plugin_definition import kernel_function
from loguru import logger
import json

from src.conf.settings import settings


class KernelFactory:
    """AI内核工厂类"""
    
    def __init__(self):
        self.kernel_cache = {}
    
    async def get_kernel(self, chat_endpoint: str, api_key: str, git_path: str,
                        model: str = "gpt-4", is_code_analysis: bool = True) -> Kernel:
        """创建和配置AI内核实例"""
        try:
            # 创建缓存键
            cache_key = f"{chat_endpoint}_{api_key}_{git_path}_{model}_{is_code_analysis}"
            
            # 检查缓存
            if cache_key in self.kernel_cache:
                return self.kernel_cache[cache_key]
            
            # 创建内核
            kernel = Kernel()
            
            # 配置AI模型服务
            await self._configure_ai_service(kernel, chat_endpoint, api_key, model)
            
            # 配置代码分析插件
            if is_code_analysis:
                await self._configure_code_analysis_plugins(kernel, git_path)
            
            # 配置文件操作插件
            await self._configure_file_plugins(kernel, git_path)
            
            # 配置代码依赖分析插件
            if settings.document.enable_code_dependency_analysis:
                await self._configure_code_dependency_plugins(kernel, git_path)
            
            # 缓存内核
            self.kernel_cache[cache_key] = kernel
            
            logger.info(f"创建AI内核成功: {model}")
            return kernel
            
        except Exception as e:
            logger.error(f"创建AI内核失败: {e}")
            raise
    
    async def _configure_ai_service(self, kernel: Kernel, chat_endpoint: str, 
                                   api_key: str, model: str):
        """配置AI模型服务"""
        try:
            if settings.openai.model_provider.lower() == "openai":
                # 配置OpenAI服务
                chat_service = OpenAIChatCompletion(
                    service_id="openai",
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=chat_endpoint
                )
                kernel.add_service(chat_service)
                
            elif settings.openai.model_provider.lower() == "azureopenai":
                # 配置Azure OpenAI服务
                chat_service = AzureOpenAIChatCompletion(
                    service_id="azure_openai",
                    ai_model_id=model,
                    api_key=api_key,
                    endpoint=chat_endpoint
                )
                kernel.add_service(chat_service)
                
            elif settings.openai.model_provider.lower() == "anthropic":
                # 配置Anthropic服务
                chat_service = AnthropicChatCompletion(
                    service_id="anthropic",
                    ai_model_id=model,
                    api_key=api_key
                )
                kernel.add_service(chat_service)
                
            else:
                raise Exception(f"不支持的模型提供者: {settings.openai.model_provider}")
                
        except Exception as e:
            logger.error(f"配置AI服务失败: {e}")
            raise
    
    async def _configure_code_analysis_plugins(self, kernel: Kernel, git_path: str):
        """配置代码分析插件"""
        try:
            # 添加代码分析插件
            plugins_path = os.path.join(os.getcwd(), "plugins", "CodeAnalysis")
            if os.path.exists(plugins_path):
                # 这里可以添加代码分析插件的加载逻辑
                logger.info("加载代码分析插件")
                
                # 添加生成README插件
                kernel.add_function(
                    function=self._generate_readme,
                    plugin_name="CodeAnalysis"
                )
                
                # 添加生成描述插件
                kernel.add_function(
                    function=self._generate_description,
                    plugin_name="CodeAnalysis"
                )
                
                # 添加代码目录简化插件
                kernel.add_function(
                    function=self._simplify_code_directory,
                    plugin_name="CodeAnalysis"
                )
                
                # 添加提交分析插件
                kernel.add_function(
                    function=self._analyze_commit,
                    plugin_name="CodeAnalysis"
                )
                
        except Exception as e:
            logger.error(f"配置代码分析插件失败: {e}")
    
    async def _configure_file_plugins(self, kernel: Kernel, git_path: str):
        """配置文件操作插件"""
        try:
            # 添加文件操作函数
            file_function = FileFunction(git_path)
            kernel.add_function(
                function=file_function.get_tree,
                plugin_name="FileFunction"
            )
            kernel.add_function(
                function=file_function.get_file_info,
                plugin_name="FileFunction"
            )
            kernel.add_function(
                function=file_function.read_files,
                plugin_name="FileFunction"
            )
            kernel.add_function(
                function=file_function.read_file,
                plugin_name="FileFunction"
            )
            
            logger.info("加载文件操作插件")
            
        except Exception as e:
            logger.error(f"配置文件操作插件失败: {e}")
    
    async def _configure_code_dependency_plugins(self, kernel: Kernel, git_path: str):
        """配置代码依赖分析插件"""
        try:
            # 添加代码依赖分析函数
            code_analyze_function = CodeAnalyzeFunction(git_path)
            kernel.add_function(
                function=code_analyze_function.analyze_function_dependencies,
                plugin_name="CodeAnalyzeFunction"
            )
            kernel.add_function(
                function=code_analyze_function.analyze_file_dependencies,
                plugin_name="CodeAnalyzeFunction"
            )
            
            logger.info("加载代码依赖分析插件")
            
        except Exception as e:
            logger.error(f"配置代码依赖分析插件失败: {e}")
    
    @kernel_function(
        name="GenerateReadme",
        description="生成项目的README文档"
    )
    async def _generate_readme(self, project_info: str) -> str:
        """生成README文档"""
        try:
            prompt = f"""请根据以下项目信息生成一个详细的README文档：

{project_info}

请包含以下内容：
1. 项目标题和简介
2. 功能特性
3. 安装说明
4. 使用方法
5. 技术栈
6. 贡献指南
7. 许可证信息
"""
            # 这里可以调用AI模型生成README
            return "生成的README内容"
            
        except Exception as e:
            logger.error(f"生成README失败: {e}")
            return f"生成README时发生错误: {str(e)}"
    
    @kernel_function(
        name="GenerateDescription",
        description="生成项目描述"
    )
    async def _generate_description(self, project_info: str) -> str:
        """生成项目描述"""
        try:
            prompt = f"""请根据以下项目信息生成一个简洁的项目描述：

{project_info}

请生成一个100-200字的项目描述，突出项目的主要功能和特点。
"""
            # 这里可以调用AI模型生成描述
            return "生成的项目描述"
            
        except Exception as e:
            logger.error(f"生成项目描述失败: {e}")
            return f"生成项目描述时发生错误: {str(e)}"
    
    @kernel_function(
        name="SimplifyCodeDirectory",
        description="简化代码目录结构"
    )
    async def _simplify_code_directory(self, directory_structure: str) -> str:
        """简化代码目录结构"""
        try:
            prompt = f"""请简化以下代码目录结构，保留重要的文件和目录：

{directory_structure}

请移除不必要的文件（如临时文件、构建文件等），保留核心代码文件。
"""
            # 这里可以调用AI模型简化目录结构
            return "简化后的目录结构"
            
        except Exception as e:
            logger.error(f"简化代码目录结构失败: {e}")
            return f"简化代码目录结构时发生错误: {str(e)}"
    
    @kernel_function(
        name="AnalyzeCommit",
        description="分析Git提交信息"
    )
    async def _analyze_commit(self, commit_info: str) -> str:
        """分析Git提交信息"""
        try:
            prompt = f"""请分析以下Git提交信息：

{commit_info}

请提供：
1. 提交类型（功能、修复、重构等）
2. 影响范围
3. 变更摘要
4. 风险评估
"""
            # 这里可以调用AI模型分析提交信息
            return "提交分析结果"
            
        except Exception as e:
            logger.error(f"分析Git提交信息失败: {e}")
            return f"分析Git提交信息时发生错误: {str(e)}"


class FileFunction:
    """文件操作函数类"""
    
    def __init__(self, git_path: str):
        self.git_path = git_path
    
    @kernel_function(
        name="GetTree",
        description="获取当前仓库的压缩目录结构"
    )
    def get_tree(self) -> str:
        """获取当前仓库的压缩目录结构"""
        try:
            # 这里实现目录结构扫描逻辑
            # 简化实现，实际应该扫描目录
            return "目录结构信息"
        except Exception as e:
            logger.error(f"获取目录结构失败: {e}")
            return f"获取目录结构时发生错误: {str(e)}"
    
    @kernel_function(
        name="GetFileInfo",
        description="获取文件基本信息"
    )
    async def get_file_info(self, file_paths: list) -> str:
        """获取文件基本信息"""
        try:
            file_info = {}
            for file_path in file_paths:
                full_path = os.path.join(self.git_path, file_path.lstrip('/'))
                if os.path.exists(full_path):
                    stat = os.stat(full_path)
                    file_info[file_path] = {
                        "name": os.path.basename(full_path),
                        "size": stat.st_size,
                        "extension": os.path.splitext(full_path)[1],
                        "creation_time": stat.st_ctime,
                        "last_write_time": stat.st_mtime,
                        "last_access_time": stat.st_atime
                    }
                else:
                    file_info[file_path] = "File not found"
            
            return json.dumps(file_info, indent=2)
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return f"获取文件信息时发生错误: {str(e)}"
    
    @kernel_function(
        name="ReadFiles",
        description="批量读取文件内容"
    )
    async def read_files(self, file_paths: list) -> str:
        """批量读取文件内容"""
        try:
            file_contents = {}
            for file_path in file_paths:
                full_path = os.path.join(self.git_path, file_path.lstrip('/'))
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_contents[file_path] = content
                    except Exception as e:
                        file_contents[file_path] = f"读取文件失败: {str(e)}"
                else:
                    file_contents[file_path] = "File not found"
            
            return json.dumps(file_contents, indent=2)
            
        except Exception as e:
            logger.error(f"批量读取文件失败: {e}")
            return f"批量读取文件时发生错误: {str(e)}"
    
    @kernel_function(
        name="ReadFile",
        description="读取单个文件内容"
    )
    async def read_file(self, file_path: str) -> str:
        """读取单个文件内容"""
        try:
            full_path = os.path.join(self.git_path, file_path.lstrip('/'))
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "File not found"
                
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return f"读取文件时发生错误: {str(e)}"


class CodeAnalyzeFunction:
    """代码分析函数类"""
    
    def __init__(self, git_path: str):
        self.git_path = git_path
    
    @kernel_function(
        name="AnalyzeFunctionDependencies",
        description="分析函数依赖关系"
    )
    async def analyze_function_dependencies(self, file_path: str) -> str:
        """分析函数依赖关系"""
        try:
            # 这里实现函数依赖分析逻辑
            return "函数依赖分析结果"
        except Exception as e:
            logger.error(f"分析函数依赖失败: {e}")
            return f"分析函数依赖时发生错误: {str(e)}"
    
    @kernel_function(
        name="AnalyzeFileDependencies",
        description="分析文件依赖关系"
    )
    async def analyze_file_dependencies(self, file_path: str) -> str:
        """分析文件依赖关系"""
        try:
            # 这里实现文件依赖分析逻辑
            return "文件依赖分析结果"
        except Exception as e:
            logger.error(f"分析文件依赖失败: {e}")
            return f"分析文件依赖时发生错误: {str(e)}" 