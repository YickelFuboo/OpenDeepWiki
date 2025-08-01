import os
import re
from typing import Dict, List, Set, Optional
from collections import defaultdict
from loguru import logger

from .interfaces import ILanguageParser
from .models import DependencyTree, DependencyNodeType, CodeMapFunctionInfo, Function
from .parsers.python_parser import PythonParser


class DependencyAnalyzer:
    """依赖分析器"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.function_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.file_to_functions: Dict[str, List[CodeMapFunctionInfo]] = defaultdict(list)
        self.function_to_file: Dict[str, str] = {}
        self.parsers: List[ILanguageParser] = []
        self.is_initialized = False
        
        # 注册解析器
        self.parsers.append(PythonParser())
    
    async def initialize(self):
        """初始化分析器"""
        if self.is_initialized:
            return
        
        files = self._get_all_source_files(self.base_path)
        
        for file_path in files:
            parser = self._get_parser_for_file(file_path)
            if parser:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    await self._process_file(file_path, file_content, parser)
                except Exception as e:
                    logger.error(f"处理文件失败 {file_path}: {e}")
        
        self.is_initialized = True
    
    async def analyze_file_dependency_tree(self, file_path: str) -> DependencyTree:
        """分析文件依赖树"""
        await self.initialize()
        
        normalized_path = os.path.abspath(file_path)
        visited = set()
        
        return self._build_file_dependency_tree(normalized_path, visited, 0)
    
    def _build_file_dependency_tree(self, file_path: str, visited: Set[str], 
                                   level: int, max_depth: int = 10) -> DependencyTree:
        """构建文件依赖树"""
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
        
        # 添加依赖文件
        if file_path in self.file_dependencies:
            for dep_file in self.file_dependencies[file_path]:
                if os.path.exists(dep_file):
                    child_tree = self._build_file_dependency_tree(
                        dep_file, visited.copy(), level + 1, max_depth
                    )
                    tree.children.append(child_tree)
        
        # 添加函数信息
        if file_path in self.file_to_functions:
            for func_info in self.file_to_functions[file_path]:
                tree.functions.append(
                    DependencyTreeFunction(
                        name=func_info.name,
                        line_number=func_info.line_number
                    )
                )
        
        return tree
    
    async def _process_file(self, file_path: str, file_content: str, parser: ILanguageParser):
        """处理文件"""
        try:
            # 提取导入
            imports = parser.extract_imports(file_content)
            
            # 解析导入路径
            for import_stmt in imports:
                resolved_path = parser.resolve_import_path(import_stmt, file_path, self.base_path)
                if resolved_path and os.path.exists(resolved_path):
                    self.file_dependencies[file_path].add(resolved_path)
            
            # 提取函数
            functions = parser.extract_functions(file_content)
            
            for func in functions:
                # 提取函数调用
                calls = parser.extract_function_calls(func.body)
                
                # 获取函数行号
                line_number = parser.get_function_line_number(file_content, func.name)
                
                func_info = CodeMapFunctionInfo(
                    name=func.name,
                    full_name=func.name,
                    body=func.body,
                    file_path=file_path,
                    line_number=line_number,
                    calls=calls
                )
                
                self.file_to_functions[file_path].append(func_info)
                self.function_to_file[func.name] = file_path
                
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
    
    def _get_parser_for_file(self, file_path: str) -> Optional[ILanguageParser]:
        """获取文件的解析器"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.py':
            return next((p for p in self.parsers if isinstance(p, PythonParser)), None)
        
        return None
    
    def _get_all_source_files(self, path: str) -> List[str]:
        """获取所有源文件"""
        source_files = []
        source_extensions = {'.py', '.js', '.ts', '.java', '.cs', '.go', '.cpp', '.c'}
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if any(file.endswith(ext) for ext in source_extensions):
                    file_path = os.path.join(root, file)
                    source_files.append(file_path)
        
        return source_files 