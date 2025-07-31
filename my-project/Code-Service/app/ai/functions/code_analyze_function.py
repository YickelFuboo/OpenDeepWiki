import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str
    file_path: str
    line_number: int
    dependencies: List[str] = None
    called_by: List[str] = None


class CodeAnalyzeFunction:
    """代码依赖分析函数类"""
    
    def __init__(self, git_path: str):
        """
        初始化代码分析函数
        
        Args:
            git_path: Git仓库的本地路径
        """
        self.git_path = git_path
        self._file_to_functions: Dict[str, List[FunctionInfo]] = {}
        self._function_map: Dict[str, FunctionInfo] = {}
        self._initialized = False
    
    def analyze_function_dependency_tree(self, file_path: str, function_name: str) -> str:
        """
        分析指定文件中特定函数的依赖关系树
        
        Args:
            file_path: 包含要分析函数的文件路径
            function_name: 要分析依赖关系的函数名称
            
        Returns:
            表示指定函数依赖树的JSON字符串
        """
        try:
            if not self._initialized:
                self._initialize()
            
            # 查找函数
            function_key = f"{file_path}:{function_name}"
            if function_key not in self._function_map:
                return json.dumps({"error": f"函数 {function_name} 在文件 {file_path} 中未找到"})
            
            function_info = self._function_map[function_key]
            
            # 构建依赖树
            dependency_tree = {
                "function": {
                    "name": function_info.name,
                    "file": function_info.file_path,
                    "line": function_info.line_number
                },
                "dependencies": self._get_function_dependencies(function_info),
                "called_by": self._get_function_callers(function_info)
            }
            
            return json.dumps(dependency_tree, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"分析函数依赖失败: {e}")
            return json.dumps({"error": f"分析函数依赖失败: {str(e)}"})
    
    def analyze_file_dependency_tree(self, file_path: str) -> str:
        """
        分析指定文件的依赖关系树
        
        Args:
            file_path: 要分析依赖关系的文件路径
            
        Returns:
            表示指定文件依赖树的JSON字符串
        """
        try:
            if not self._initialized:
                self._initialize()
            
            if file_path not in self._file_to_functions:
                return json.dumps({"error": f"文件 {file_path} 未找到或无法分析"})
            
            file_functions = self._file_to_functions[file_path]
            
            # 构建文件依赖树
            dependency_tree = {
                "file": file_path,
                "functions": [],
                "dependencies": [],
                "dependents": []
            }
            
            for func_info in file_functions:
                dependency_tree["functions"].append({
                    "name": func_info.name,
                    "line": func_info.line_number,
                    "dependencies": self._get_function_dependencies(func_info),
                    "called_by": self._get_function_callers(func_info)
                })
            
            # 分析文件级依赖
            dependency_tree["dependencies"] = self._get_file_dependencies(file_path)
            dependency_tree["dependents"] = self._get_file_dependents(file_path)
            
            return json.dumps(dependency_tree, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"分析文件依赖失败: {e}")
            return json.dumps({"error": f"分析文件依赖失败: {str(e)}"})
    
    def _initialize(self):
        """初始化代码分析"""
        try:
            logger.info("初始化代码分析...")
            
            # 扫描所有源文件
            source_files = self._scan_source_files()
            
            # 解析每个文件中的函数
            for file_path in source_files:
                self._parse_file_functions(file_path)
            
            # 建立函数调用关系
            self._build_function_relationships()
            
            self._initialized = True
            logger.info("代码分析初始化完成")
            
        except Exception as e:
            logger.error(f"初始化代码分析失败: {e}")
            raise
    
    def _scan_source_files(self) -> List[str]:
        """扫描源文件"""
        source_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php'}
        source_files = []
        
        for root, dirs, files in os.walk(self.git_path):
            # 忽略某些目录
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.vscode'}]
            
            for file in files:
                if any(file.endswith(ext) for ext in source_extensions):
                    relative_path = os.path.relpath(os.path.join(root, file), self.git_path)
                    source_files.append(relative_path.replace("\\", "/"))
        
        return source_files
    
    def _parse_file_functions(self, file_path: str):
        """解析文件中的函数"""
        try:
            full_path = os.path.join(self.git_path, file_path)
            if not os.path.exists(full_path):
                return
            
            functions = []
            
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    # 简单的函数检测（可以根据语言扩展）
                    if self._is_function_definition(line, file_path):
                        func_name = self._extract_function_name(line)
                        if func_name:
                            func_info = FunctionInfo(
                                name=func_name,
                                file_path=file_path,
                                line_number=line_num
                            )
                            functions.append(func_info)
                            self._function_map[f"{file_path}:{func_name}"] = func_info
            
            self._file_to_functions[file_path] = functions
            
        except Exception as e:
            logger.error(f"解析文件函数失败 {file_path}: {e}")
    
    def _is_function_definition(self, line: str, file_path: str) -> bool:
        """检查是否是函数定义"""
        line = line.strip()
        
        # Python函数定义
        if file_path.endswith('.py'):
            return (line.startswith('def ') or 
                   line.startswith('async def ') or
                   line.startswith('class '))
        
        # JavaScript/TypeScript函数定义
        elif file_path.endswith(('.js', '.ts')):
            return (line.startswith('function ') or
                   'function(' in line or
                   '=>' in line or
                   line.startswith('const ') and '=' in line and '(' in line)
        
        # 其他语言的函数定义检测可以在这里扩展
        return False
    
    def _extract_function_name(self, line: str) -> Optional[str]:
        """提取函数名称"""
        line = line.strip()
        
        # Python函数名提取
        if line.startswith('def '):
            return line[4:].split('(')[0].strip()
        elif line.startswith('async def '):
            return line[10:].split('(')[0].strip()
        elif line.startswith('class '):
            return line[6:].split('(')[0].split(':')[0].strip()
        
        # JavaScript函数名提取
        elif line.startswith('function '):
            return line[9:].split('(')[0].strip()
        elif 'function(' in line:
            # 匿名函数，生成一个标识符
            return f"anonymous_{hash(line) % 10000}"
        elif '=>' in line:
            # 箭头函数
            return f"arrow_{hash(line) % 10000}"
        
        return None
    
    def _build_function_relationships(self):
        """建立函数调用关系"""
        # 这里可以实现更复杂的函数调用关系分析
        # 目前使用简化的实现
        pass
    
    def _get_function_dependencies(self, func_info: FunctionInfo) -> List[Dict[str, Any]]:
        """获取函数的依赖关系"""
        # 简化的依赖分析实现
        return []
    
    def _get_function_callers(self, func_info: FunctionInfo) -> List[Dict[str, Any]]:
        """获取调用该函数的函数列表"""
        # 简化的调用者分析实现
        return []
    
    def _get_file_dependencies(self, file_path: str) -> List[str]:
        """获取文件的依赖文件列表"""
        # 简化的文件依赖分析实现
        return []
    
    def _get_file_dependents(self, file_path: str) -> List[str]:
        """获取依赖该文件的文件列表"""
        # 简化的文件被依赖分析实现
        return [] 