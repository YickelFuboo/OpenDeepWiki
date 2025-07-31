"""
代码分析插件模块

提供各种代码分析插件：
- README生成插件
- 描述生成插件
- 函数提示插件
- 提交分析插件
- 代码目录简化插件
"""

from .generate_readme import GenerateReadmePlugin
from .generate_description import GenerateDescriptionPlugin
from .function_prompt import FunctionPromptPlugin
from .commit_analyze import CommitAnalyzePlugin
from .code_dir_simplifier import CodeDirSimplifierPlugin

__all__ = [
    "GenerateReadmePlugin",
    "GenerateDescriptionPlugin", 
    "FunctionPromptPlugin",
    "CommitAnalyzePlugin",
    "CodeDirSimplifierPlugin"
] 