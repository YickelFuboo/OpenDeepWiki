import re
import os
from typing import List

from ..interfaces import ILanguageParser
from ..models import Function


class PythonParser(ILanguageParser):
    """Python语言解析器"""
    
    def extract_imports(self, file_content: str) -> List[str]:
        """提取导入语句"""
        imports = []
        
        # 匹配import语句
        import_regex = re.compile(r'import\s+([^\s,;]+)(?:\s*,\s*([^\s,;]+))*')
        matches = import_regex.finditer(file_content)
        
        for match in matches:
            for i in range(1, len(match.groups()) + 1):
                if match.group(i) and match.group(i).strip():
                    imports.append(match.group(i))
        
        # 匹配from...import语句
        from_import_regex = re.compile(r'from\s+([^\s]+)\s+import\s+(?:([^\s,;]+)(?:\s*,\s*([^\s,;]+))*|\*)')
        matches = from_import_regex.finditer(file_content)
        
        for match in matches:
            imports.append(match.group(1))
        
        return imports
    
    def extract_functions(self, file_content: str) -> List[Function]:
        """提取函数"""
        functions = []
        
        # 匹配函数定义
        func_regex = re.compile(r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?\s*:(.*?)(?=\n(?:def|class)|\Z)', re.DOTALL)
        matches = func_regex.finditer(file_content)
        
        for match in matches:
            functions.append(Function(
                name=match.group(1),
                body=match.group(2)
            ))
        
        return functions
    
    def extract_function_calls(self, function_body: str) -> List[str]:
        """提取函数调用"""
        function_calls = []
        
        # 过滤的Python内置函数和关键字
        builtin_functions = {
            'print', 'len', 'int', 'str', 'list', 'dict', 'set', 'tuple',
            'if', 'while', 'for', 'try', 'except', 'finally', 'with',
            'return', 'yield', 'raise', 'assert', 'pass', 'break', 'continue',
            'True', 'False', 'None', 'self', 'cls', 'super', 'isinstance',
            'type', 'dir', 'help', 'id', 'hash', 'repr', 'format'
        }
        
        # 匹配函数调用
        call_regex = re.compile(r'(\w+)\s*\(')
        matches = call_regex.finditer(function_body)
        
        for match in matches:
            name = match.group(1)
            if name not in builtin_functions:
                function_calls.append(name)
        
        # 匹配方法调用
        method_call_regex = re.compile(r'(\w+)\.(\w+)\s*\(')
        matches = method_call_regex.finditer(function_body)
        
        for match in matches:
            function_calls.append(match.group(2))
        
        return function_calls
    
    def resolve_import_path(self, import_statement: str, current_file_path: str, base_path: str) -> str:
        """解析导入路径"""
        current_dir = os.path.dirname(current_file_path)
        
        # 处理相对导入（以.开头）
        if import_statement.startswith('.'):
            parts = import_statement.split('.')
            dir_path = current_dir
            
            # 处理上级目录导入
            for i, part in enumerate(parts):
                if part == '':
                    dir_path = os.path.dirname(dir_path)
                else:
                    break
            
            # 构建完整路径
            if len(parts) > 1:
                module_path = os.path.join(dir_path, *parts[1:])
                return os.path.join(module_path, '__init__.py')
            else:
                return os.path.join(dir_path, '__init__.py')
        
        # 处理绝对导入
        else:
            # 将点分隔的模块路径转换为文件路径
            module_parts = import_statement.split('.')
            file_path = os.path.join(base_path, *module_parts)
            
            # 尝试不同的文件扩展名
            for ext in ['.py', '/__init__.py']:
                full_path = file_path + ext
                if os.path.exists(full_path):
                    return full_path
            
            return file_path + '.py'
    
    def get_function_line_number(self, file_content: str, function_name: str) -> int:
        """获取函数行号"""
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 匹配函数定义
            if re.match(rf'def\s+{re.escape(function_name)}\s*\(', line):
                return i
        
        return 0 