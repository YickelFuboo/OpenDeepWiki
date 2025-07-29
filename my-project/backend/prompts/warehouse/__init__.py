"""
仓库相关的提示词模板

包括：
- 文档生成提示词
- 目录分析提示词
- 项目概览提示词
- 思维导图生成提示词
"""

from .document_generation import *
from .catalog_analysis import *
from .project_overview import *
from .mindmap_generation import *

__all__ = [
    "DOCUMENT_GENERATION_PROMPTS",
    "CATALOG_ANALYSIS_PROMPTS",
    "PROJECT_OVERVIEW_PROMPTS", 
    "MINDMAP_GENERATION_PROMPTS"
] 