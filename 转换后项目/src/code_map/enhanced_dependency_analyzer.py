import os
import asyncio
from typing import Dict, List, Set, Optional
from collections import defaultdict
from loguru import logger

from .interfaces import ISemanticAnalyzer
from .models import (
    DependencyTree, DependencyNodeType, CodeMapFunctionInfo,
    ProjectSemanticModel, SemanticModel, FunctionInfo, TypeInfo
)


class EnhancedDependencyAnalyzer:
    """增强的依赖分析器，使用语义分析替代正则表达式"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.analyzers: Dict[str, ISemanticAnalyzer] = {}
        self.project_model: Optional[ProjectSemanticModel] = None
        self.is_initialized = False
        
        # 注册语义分析器
        self._register_analyzers()
    
    def _register_analyzers(self):
        """注册语义分析器"""
        # 这里可以注册各种语言的语义分析器
        pass
    
    async def initialize(self):
        """初始化分析器"""
        if self.is_initialized:
            return
        
        files = self._get_all_source_files(self.base_path)
        grouped_files = self._group_files_by_extension(files)
        
        all_models = []
        
        # 并行处理不同语言的文件
        tasks = []
        for ext, file_list in grouped_files.items():
            if ext in self.analyzers:
                analyzer = self.analyzers[ext]
                task = analyzer.analyze_project(file_list)
                tasks.append(task)
        
        if tasks:
            models = await asyncio.gather(*tasks)
            all_models.extend(models)
        
        # 合并所有语言的语义模型
        self.project_model = self._merge_project_models(all_models)
        self.is_initialized = True
    
    async def analyze_file_dependency_tree(self, file_path: str) -> DependencyTree:
        """分析文件依赖树"""
        await self.initialize()
        
        normalized_path = os.path.abspath(file_path)
        visited = set()
        
        return self._build_semantic_file_dependency_tree(normalized_path, visited, 0)
    
    def _build_semantic_file_dependency_tree(self, file_path: str, visited: Set[str], 
                                           level: int, max_depth: int = 10) -> DependencyTree:
        """构建语义文件依赖树"""
        if level > max_depth or file_path in visited:
            return DependencyTree(
                node_type=DependencyNodeType.FILE,
                name=os.path.basename(file_path),
                full_path=file_path,
                is_cyclic=file_path in visited
            )
        
        visited.add(file_path)
        
        tree = DependencyTree(
            node_type=DependencyNodeType.FILE,
            name=os.path.basename(file_path),
            full_path=file_path,
            is_cyclic=False,
            children=[],
            functions=[]
        )
        
        # 使用语义模型获取依赖
        if self.project_model and file_path in self.project_model.files:
            file_model = self.project_model.files[file_path]
            
            # 添加导入依赖
            if file_path in self.project_model.dependencies:
                dependencies = self.project_model.dependencies[file_path]
                for dep_file in dependencies:
                    if os.path.exists(dep_file):
                        child_tree = self._build_semantic_file_dependency_tree(
                            dep_file, visited.copy(), level + 1, max_depth
                        )
                        tree.children.append(child_tree)
            
            # 添加函数信息
            for func in file_model.functions:
                tree.functions.append(
                    DependencyTreeFunction(
                        name=func.name,
                        line_number=func.line_number
                    )
                )
        
        return tree
    
    def _get_all_source_files(self, path: str) -> List[str]:
        """获取所有源文件"""
        source_files = []
        source_extensions = {'.py', '.js', '.ts', '.java', '.cs', '.go', '.cpp', '.c'}
        
        for root, dirs, files in os.walk(path):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in source_extensions):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
        
        return source_files
    
    def _group_files_by_extension(self, files: List[str]) -> Dict[str, List[str]]:
        """按扩展名分组文件"""
        grouped = defaultdict(list)
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            grouped[ext].append(file_path)
        return dict(grouped)
    
    def _merge_project_models(self, models: List[ProjectSemanticModel]) -> ProjectSemanticModel:
        """合并项目模型"""
        merged = ProjectSemanticModel()
        
        for model in models:
            # 合并文件
            merged.files.update(model.files)
            
            # 合并依赖
            for file_path, deps in model.dependencies.items():
                if file_path in merged.dependencies:
                    merged.dependencies[file_path].extend(deps)
                else:
                    merged.dependencies[file_path] = deps.copy()
            
            # 合并类型
            merged.all_types.update(model.all_types)
            
            # 合并函数
            merged.all_functions.update(model.all_functions)
        
        return merged 