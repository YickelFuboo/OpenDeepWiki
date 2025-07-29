"""
Prompts模块

提供各种AI提示词模板，包括：
- 文档生成提示词
- 聊天响应提示词
- 代码分析提示词
- 仓库分类提示词
"""

from .warehouse import *
from .chat import *
from .mem0 import *

__all__ = [
    "WAREHOUSE_PROMPTS",
    "CHAT_PROMPTS", 
    "MEM0_PROMPTS"
] 