from abc import ABC, abstractmethod
from typing import List
import asyncio

from .models import Function, SemanticModel, ProjectSemanticModel


class ILanguageParser(ABC):
    """语言解析器接口"""
    
    @abstractmethod
    def extract_imports(self, file_content: str) -> List[str]:
        """提取导入语句"""
        pass
    
    @abstractmethod
    def extract_functions(self, file_content: str) -> List[Function]:
        """提取函数"""
        pass
    
    @abstractmethod
    def extract_function_calls(self, function_body: str) -> List[str]:
        """提取函数调用"""
        pass
    
    @abstractmethod
    def resolve_import_path(self, import_statement: str, current_file_path: str, base_path: str) -> str:
        """解析导入路径"""
        pass
    
    @abstractmethod
    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        """获取函数行号"""
        pass


class ISemanticAnalyzer(ABC):
    """语义分析器接口"""
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        pass
    
    @abstractmethod
    async def analyze_file(self, file_path: str, content: str) -> SemanticModel:
        """解析文件的语义结构"""
        pass
    
    @abstractmethod
    async def analyze_project(self, file_paths: List[str]) -> ProjectSemanticModel:
        """解析项目的语义结构（用于跨文件依赖分析）"""
        pass 