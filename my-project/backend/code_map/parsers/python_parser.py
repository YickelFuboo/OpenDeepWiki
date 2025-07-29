"""
Python代码解析器

解析Python代码结构，提取类、函数、变量等信息
"""

import ast
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class PythonParser:
    """Python代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.py']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析Python文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析结果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_content(content, file_path)
            
        except Exception as e:
            logger.error(f"解析Python文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析Python代码内容
        
        Args:
            content: 代码内容
            file_path: 文件路径（可选）
            
        Returns:
            解析结果
        """
        try:
            # 解析AST
            tree = ast.parse(content)
            
            # 提取信息
            result = {
                "file_path": file_path,
                "language": "python",
                "classes": self._extract_classes(tree),
                "functions": self._extract_functions(tree),
                "imports": self._extract_imports(tree),
                "variables": self._extract_variables(tree),
                "docstrings": self._extract_docstrings(tree),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析Python内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取类定义"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                    "bases": [self._get_name(base) for base in node.bases],
                    "methods": self._extract_methods(node),
                    "attributes": self._extract_class_attributes(node),
                    "docstring": ast.get_docstring(node)
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取函数定义"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 跳过类中的方法（在_extract_methods中处理）
                if not self._is_in_class(node, tree):
                    func_info = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "args": self._extract_function_args(node),
                        "returns": self._extract_function_returns(node),
                        "docstring": ast.get_docstring(node)
                    }
                    functions.append(func_info)
        
        return functions
    
    def _extract_methods(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """提取类中的方法"""
        methods = []
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_info = {
                    "name": node.name,
                    "line_number": node.lineno,
                    "args": self._extract_function_args(node),
                    "returns": self._extract_function_returns(node),
                    "docstring": ast.get_docstring(node),
                    "is_static": self._is_static_method(node),
                    "is_class_method": self._is_class_method(node)
                }
                methods.append(method_info)
        
        return methods
    
    def _extract_imports(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取导入语句"""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_info = {
                        "module": alias.name,
                        "alias": alias.asname,
                        "line_number": node.lineno,
                        "type": "import"
                    }
                    imports.append(import_info)
            
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    import_info = {
                        "module": node.module or "",
                        "name": alias.name,
                        "alias": alias.asname,
                        "line_number": node.lineno,
                        "type": "from_import"
                    }
                    imports.append(import_info)
        
        return imports
    
    def _extract_variables(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取变量定义"""
        variables = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_info = {
                            "name": target.id,
                            "line_number": node.lineno,
                            "value_type": self._get_value_type(node.value)
                        }
                        variables.append(var_info)
        
        return variables
    
    def _extract_docstrings(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """提取文档字符串"""
        docstrings = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    doc_info = {
                        "content": docstring,
                        "line_number": node.lineno,
                        "type": type(node).__name__
                    }
                    docstrings.append(doc_info)
        
        return docstrings
    
    def _extract_class_attributes(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """提取类属性"""
        attributes = []
        
        for node in class_node.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attr_info = {
                            "name": target.id,
                            "line_number": node.lineno,
                            "value_type": self._get_value_type(node.value)
                        }
                        attributes.append(attr_info)
        
        return attributes
    
    def _extract_function_args(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """提取函数参数"""
        args = []
        
        for arg in func_node.args.args:
            arg_info = {
                "name": arg.arg,
                "annotation": self._get_annotation_name(arg.annotation) if arg.annotation else None
            }
            args.append(arg_info)
        
        return args
    
    def _extract_function_returns(self, func_node: ast.FunctionDef) -> Optional[str]:
        """提取函数返回类型"""
        if func_node.returns:
            return self._get_annotation_name(func_node.returns)
        return None
    
    def _get_name(self, node: ast.AST) -> str:
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)
    
    def _get_annotation_name(self, node: ast.AST) -> str:
        """获取注解名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return str(node)
    
    def _get_value_type(self, node: ast.AST) -> str:
        """获取值类型"""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Tuple):
            return "tuple"
        elif isinstance(node, ast.Call):
            return "function_call"
        return "unknown"
    
    def _is_in_class(self, func_node: ast.FunctionDef, tree: ast.AST) -> bool:
        """检查函数是否在类中"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if child == func_node:
                        return True
        return False
    
    def _is_static_method(self, func_node: ast.FunctionDef) -> bool:
        """检查是否为静态方法"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "staticmethod":
                return True
        return False
    
    def _is_class_method(self, func_node: ast.FunctionDef) -> bool:
        """检查是否为类方法"""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "classmethod":
                return True
        return False
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "language": "python",
            "error": error,
            "classes": [],
            "functions": [],
            "imports": [],
            "variables": [],
            "docstrings": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 