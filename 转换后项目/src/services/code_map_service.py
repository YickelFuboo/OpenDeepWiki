from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from src.code_map import DependencyAnalyzer
from src.code_map.models import DependencyTree


class CodeMapService:
    """代码映射服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analyzers: Dict[str, DependencyAnalyzer] = {}
    
    async def analyze_file_dependency_tree(self, base_path: str, file_path: str) -> Optional[DependencyTree]:
        """分析文件依赖树"""
        try:
            analyzer = self._get_or_create_analyzer(base_path)
            return await analyzer.analyze_file_dependency_tree(file_path)
        except Exception as e:
            logger.error(f"分析文件依赖树失败: {e}")
            return None
    
    async def analyze_function_dependency_tree(self, base_path: str, file_path: str, function_name: str) -> Optional[DependencyTree]:
        """分析函数依赖树"""
        try:
            analyzer = self._get_or_create_analyzer(base_path)
            return await analyzer.analyze_function_dependency_tree(file_path, function_name)
        except Exception as e:
            logger.error(f"分析函数依赖树失败: {e}")
            return None
    
    def generate_dependency_tree_visualization(self, tree: DependencyTree) -> str:
        """生成依赖树可视化"""
        try:
            analyzer = DependencyAnalyzer("")  # 临时创建用于可视化
            return analyzer.generate_dependency_tree_visualization(tree)
        except Exception as e:
            logger.error(f"生成依赖树可视化失败: {e}")
            return f"生成可视化失败: {str(e)}"
    
    def generate_dot_graph(self, tree: DependencyTree) -> str:
        """生成DOT图"""
        try:
            analyzer = DependencyAnalyzer("")  # 临时创建用于可视化
            return analyzer.generate_dot_graph(tree)
        except Exception as e:
            logger.error(f"生成DOT图失败: {e}")
            return f"生成DOT图失败: {str(e)}"
    
    def _get_or_create_analyzer(self, base_path: str) -> DependencyAnalyzer:
        """获取或创建分析器"""
        if base_path not in self.analyzers:
            self.analyzers[base_path] = DependencyAnalyzer(base_path)
        return self.analyzers[base_path] 