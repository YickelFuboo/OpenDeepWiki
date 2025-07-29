"""
JavaScript代码解析器

解析JavaScript代码结构，提取函数、类、变量等信息
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class JavaScriptParser:
    """JavaScript代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.js', '.ts', '.jsx', '.tsx']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析JavaScript文件
        
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
            logger.error(f"解析JavaScript文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析JavaScript代码内容
        
        Args:
            content: 代码内容
            file_path: 文件路径（可选）
            
        Returns:
            解析结果
        """
        try:
            # 提取信息
            result = {
                "file_path": file_path,
                "language": "javascript",
                "imports": self._extract_imports(content),
                "exports": self._extract_exports(content),
                "functions": self._extract_functions(content),
                "classes": self._extract_classes(content),
                "variables": self._extract_variables(content),
                "constants": self._extract_constants(content),
                "comments": self._extract_comments(content),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析JavaScript内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """提取导入语句"""
        imports = []
        
        # ES6 import语句
        import_patterns = [
            r'import\s+(\{[^}]*\})\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                import_info = {
                    "imports": match.group(1) if match.groups() > 1 else None,
                    "module": match.group(2) if match.groups() > 1 else match.group(1),
                    "line_number": content[:match.start()].count('\n') + 1,
                    "type": "es6_import"
                }
                imports.append(import_info)
        
        # CommonJS require语句
        require_pattern = r'const\s+(\w+)\s*=\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for match in re.finditer(require_pattern, content):
            import_info = {
                "imports": match.group(1),
                "module": match.group(2),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "commonjs_require"
            }
            imports.append(import_info)
        
        return imports
    
    def _extract_exports(self, content: str) -> List[Dict[str, Any]]:
        """提取导出语句"""
        exports = []
        
        # ES6 export语句
        export_patterns = [
            r'export\s+default\s+(\w+)',
            r'export\s+(\{[^}]*\})',
            r'export\s+(?:const|let|var|function|class)\s+(\w+)',
            r'export\s+default\s+function\s+(\w+)',
            r'export\s+default\s+class\s+(\w+)'
        ]
        
        for pattern in export_patterns:
            for match in re.finditer(pattern, content):
                export_info = {
                    "exports": match.group(1),
                    "line_number": content[:match.start()].count('\n') + 1,
                    "type": "es6_export"
                }
                exports.append(export_info)
        
        # CommonJS module.exports
        module_export_pattern = r'module\.exports\s*=\s*(\w+)'
        for match in re.finditer(module_export_pattern, content):
            export_info = {
                "exports": match.group(1),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "commonjs_export"
            }
            exports.append(export_info)
        
        return exports
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """提取函数定义"""
        functions = []
        
        # 函数定义模式
        function_patterns = [
            r'function\s+(\w+)\s*\([^)]*\)',
            r'const\s+(\w+)\s*=\s*function\s*\([^)]*\)',
            r'let\s+(\w+)\s*=\s*function\s*\([^)]*\)',
            r'var\s+(\w+)\s*=\s*function\s*\([^)]*\)',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'let\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'var\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'(\w+)\s*:\s*function\s*\([^)]*\)',
            r'(\w+)\s*:\s*\([^)]*\)\s*=>'
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                function_name = match.group(1)
                
                function_info = {
                    "name": function_name,
                    "line_number": content[:match.start()].count('\n') + 1,
                    "type": self._get_function_type(match.group(0)),
                    "parameters": self._extract_function_parameters(match.group(0))
                }
                functions.append(function_info)
        
        return functions
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """提取类定义"""
        classes = []
        
        # 类定义模式
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            extends_class = match.group(2)
            
            # 找到类的结束位置
            start_pos = match.end()
            brace_count = 1
            end_pos = start_pos
            
            for i, char in enumerate(content[start_pos:], start_pos):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            
            class_content = content[start_pos:end_pos]
            
            class_info = {
                "name": class_name,
                "extends": extends_class,
                "methods": self._extract_class_methods(class_content),
                "properties": self._extract_class_properties(class_content),
                "constructor": self._extract_constructor(class_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_variables(self, content: str) -> List[Dict[str, Any]]:
        """提取变量定义"""
        variables = []
        
        # 变量定义模式
        variable_patterns = [
            r'const\s+(\w+)\s*=\s*([^;]+)',
            r'let\s+(\w+)\s*=\s*([^;]+)',
            r'var\s+(\w+)\s*=\s*([^;]+)'
        ]
        
        for pattern in variable_patterns:
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                var_value = match.group(2)
                
                # 跳过函数定义
                if 'function' in var_value or '=>' in var_value:
                    continue
                
                variable_info = {
                    "name": var_name,
                    "value": var_value.strip(),
                    "type": self._get_variable_type(var_value),
                    "line_number": content[:match.start()].count('\n') + 1
                }
                variables.append(variable_info)
        
        return variables
    
    def _extract_constants(self, content: str) -> List[Dict[str, Any]]:
        """提取常量定义"""
        constants = []
        
        # 常量定义模式
        constant_pattern = r'const\s+(\w+)\s*=\s*([^;]+)'
        
        for match in re.finditer(constant_pattern, content):
            const_name = match.group(1)
            const_value = match.group(2)
            
            # 跳过函数定义
            if 'function' in const_value or '=>' in const_value:
                continue
            
            constant_info = {
                "name": const_name,
                "value": const_value.strip(),
                "type": self._get_variable_type(const_value),
                "line_number": content[:match.start()].count('\n') + 1
            }
            constants.append(constant_info)
        
        return constants
    
    def _extract_comments(self, content: str) -> List[Dict[str, Any]]:
        """提取注释"""
        comments = []
        
        # 单行注释
        single_line_pattern = r'//\s*(.+)'
        for match in re.finditer(single_line_pattern, content):
            comment_info = {
                "content": match.group(1),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "single_line"
            }
            comments.append(comment_info)
        
        # 多行注释
        multi_line_pattern = r'/\*([^*]|\*(?!/))*\*/'
        for match in re.finditer(multi_line_pattern, content):
            comment_info = {
                "content": match.group(0),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "multi_line"
            }
            comments.append(comment_info)
        
        return comments
    
    def _extract_class_methods(self, class_content: str) -> List[Dict[str, Any]]:
        """提取类方法"""
        methods = []
        
        # 方法定义模式
        method_patterns = [
            r'(\w+)\s*\([^)]*\)\s*\{',
            r'(\w+)\s*:\s*function\s*\([^)]*\)',
            r'(\w+)\s*:\s*\([^)]*\)\s*=>'
        ]
        
        for pattern in method_patterns:
            for match in re.finditer(pattern, class_content):
                method_name = match.group(1)
                
                # 跳过构造函数
                if method_name == 'constructor':
                    continue
                
                method_info = {
                    "name": method_name,
                    "line_number": class_content[:match.start()].count('\n') + 1,
                    "type": self._get_method_type(match.group(0))
                }
                methods.append(method_info)
        
        return methods
    
    def _extract_class_properties(self, class_content: str) -> List[Dict[str, Any]]:
        """提取类属性"""
        properties = []
        
        # 属性定义模式
        property_pattern = r'(\w+)\s*[:=]\s*([^;,\n]+)'
        
        for match in re.finditer(property_pattern, class_content):
            prop_name = match.group(1)
            prop_value = match.group(2)
            
            # 跳过方法定义
            if '(' in prop_name or 'function' in prop_value:
                continue
            
            property_info = {
                "name": prop_name,
                "value": prop_value.strip(),
                "line_number": class_content[:match.start()].count('\n') + 1
            }
            properties.append(property_info)
        
        return properties
    
    def _extract_constructor(self, class_content: str) -> Optional[Dict[str, Any]]:
        """提取构造函数"""
        constructor_pattern = r'constructor\s*\([^)]*\)\s*\{'
        
        match = re.search(constructor_pattern, class_content)
        if match:
            return {
                "line_number": class_content[:match.start()].count('\n') + 1,
                "parameters": self._extract_function_parameters(match.group(0))
            }
        
        return None
    
    def _get_function_type(self, function_text: str) -> str:
        """获取函数类型"""
        if 'function' in function_text:
            return "function_declaration"
        elif '=>' in function_text:
            return "arrow_function"
        elif ':' in function_text:
            return "method"
        else:
            return "unknown"
    
    def _get_method_type(self, method_text: str) -> str:
        """获取方法类型"""
        if 'function' in method_text:
            return "function_method"
        elif '=>' in method_text:
            return "arrow_method"
        else:
            return "method"
    
    def _get_variable_type(self, value: str) -> str:
        """获取变量类型"""
        value = value.strip()
        
        if value.startswith('"') or value.startswith("'"):
            return "string"
        elif value.isdigit():
            return "number"
        elif value in ['true', 'false']:
            return "boolean"
        elif value.startswith('['):
            return "array"
        elif value.startswith('{'):
            return "object"
        elif value.startswith('null'):
            return "null"
        elif value.startswith('undefined'):
            return "undefined"
        else:
            return "unknown"
    
    def _extract_function_parameters(self, function_text: str) -> List[str]:
        """提取函数参数"""
        parameters = []
        
        # 提取参数列表
        param_match = re.search(r'\(([^)]*)\)', function_text)
        if param_match:
            param_str = param_match.group(1)
            if param_str.strip():
                param_parts = param_str.split(',')
                for part in param_parts:
                    part = part.strip()
                    if part:
                        parameters.append(part)
        
        return parameters
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "language": "javascript",
            "error": error,
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "variables": [],
            "constants": [],
            "comments": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 