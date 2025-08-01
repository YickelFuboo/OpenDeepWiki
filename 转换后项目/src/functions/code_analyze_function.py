import json
import os
from typing import Optional
from semantic_kernel import kernel_function
from loguru import logger

from src.code_map.code_map import DependencyAnalyzer


class CodeAnalyzeFunction:
    """代码依赖分析函数类
    
    该类提供代码依赖关系分析功能，集成到AI内核中供AI模型调用
    支持分析函数级和文件级的依赖关系，帮助理解代码结构和调用关系
    """
    
    def __init__(self, git_path: str):
        """
        初始化代码分析函数
        
        Args:
            git_path: Git仓库的本地路径，用于定位和分析代码文件
        """
        self.git_path = git_path
    
    @kernel_function(
        name="AnalyzeFunctionDependencyTree",
        description="Analyze the dependency relationship of the specified method"
    )
    async def analyze_function_dependency_tree(
        self,
        file_path: str,
        function_name: str
    ) -> str:
        """
        分析指定文件中特定函数的依赖关系树
        
        该方法会分析指定函数的所有调用关系，构建完整的依赖树结构
        包括该函数调用的其他函数、被其他函数调用的情况等
        
        Args:
            file_path: 包含要分析函数的文件路径（相对于仓库根目录）
            function_name: 要分析依赖关系的函数名称
            
        Returns:
            表示指定函数依赖树的JSON字符串，包含完整的调用关系结构
        """
        try:
            # 步骤1：记录分析请求
            logger.info(f"ReadCodeFileAsync: {file_path} {function_name}")
            
            # 步骤2：构建完整文件路径
            # 将相对路径转换为绝对路径，确保能正确访问文件
            # lstrip('/') 移除路径开头的斜杠，避免路径拼接问题
            new_path = os.path.join(self.git_path, file_path.lstrip('/'))
            
            # 步骤3：创建依赖分析器实例
            # 创建DependencyAnalyzer实例，该分析器负责实际的代码依赖分析工作
            code = DependencyAnalyzer(self.git_path)
            
            # 步骤4：执行函数依赖分析
            # 调用依赖分析器的analyze_function_dependency_tree方法
            # 传入完整文件路径和函数名，获取函数的依赖关系树
            result = await code.analyze_function_dependency_tree(new_path, function_name)
            
            # 步骤5：序列化并返回结果
            # 将分析结果序列化为JSON格式
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as ex:
            # 异常处理
            # 捕获并处理分析过程中可能出现的异常
            # 记录错误信息，便于调试和问题排查
            logger.error(f"Error reading file: {ex}")
            
            # 返回错误信息字符串，让调用方知道分析失败的原因
            return f"Error reading file: {str(ex)}"
    
    @kernel_function(
        name="AnalyzeFileDependencyTree",
        description="Analyze the dependency relationship of the specified file"
    )
    async def analyze_file_dependency_tree(
        self,
        file_path: str
    ) -> str:
        """
        分析指定文件的整体依赖关系
        
        该方法会分析整个文件的依赖结构，包括文件中的所有函数、导入关系等
        提供文件级别的依赖关系视图，帮助理解文件的整体结构
        
        Args:
            file_path: 要分析依赖关系的文件路径（相对于仓库根目录）
            
        Returns:
            表示指定文件依赖树的JSON字符串，包含文件的完整依赖结构
        """
        try:
            # 步骤1：记录分析请求
            logger.info(f"ReadCodeFileAsync: {file_path}")
            
            # 步骤2：构建完整文件路径
            # 将相对路径转换为绝对路径，确保能正确访问文件
            # lstrip('/') 移除路径开头的斜杠，避免路径拼接问题
            new_path = os.path.join(self.git_path, file_path.lstrip('/'))
            
            # 步骤3：创建依赖分析器实例
            # 创建DependencyAnalyzer实例，该分析器负责实际的代码依赖分析工作
            code = DependencyAnalyzer(self.git_path)
            
            # 步骤4：执行文件依赖分析
            # 调用依赖分析器的analyze_file_dependency_tree方法
            # 传入完整文件路径，获取文件的整体依赖关系树
            result = await code.analyze_file_dependency_tree(new_path)
            
            # 步骤5：序列化并返回结果
            # 将分析结果序列化为JSON格式
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as ex:
            # 异常处理
            # 捕获并处理分析过程中可能出现的异常
            # 记录错误信息，便于调试和问题排查
            logger.error(f"Error reading file: {ex}")
            
            # 返回错误信息字符串，让调用方知道分析失败的原因
            return f"Error reading file: {str(ex)}" 