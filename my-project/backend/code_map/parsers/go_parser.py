"""
Go代码解析器

解析Go代码结构，提取包、函数、结构体等信息
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class GoParser:
    """Go代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.go']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析Go文件
        
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
            logger.error(f"解析Go文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析Go代码内容
        
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
                "language": "go",
                "package": self._extract_package(content),
                "imports": self._extract_imports(content),
                "functions": self._extract_functions(content),
                "structs": self._extract_structs(content),
                "interfaces": self._extract_interfaces(content),
                "variables": self._extract_variables(content),
                "constants": self._extract_constants(content),
                "comments": self._extract_comments(content),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析Go内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_package(self, content: str) -> Optional[str]:
        """提取包声明"""
        package_match = re.search(r'package\s+(\w+)', content)
        if package_match:
            return package_match.group(1)
        return None
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """提取导入语句"""
        imports = []
        
        # 单行导入
        single_import_pattern = r'import\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(single_import_pattern, content):
            import_info = {
                "import": match.group(1),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "single_import"
            }
            imports.append(import_info)
        
        # 多行导入
        multi_import_pattern = r'import\s*\(\s*((?:[\'"][^\'"]+[\'"]\s*\n?)+)\s*\)'
        for match in re.finditer(multi_import_pattern, content):
            import_block = match.group(1)
            for import_line in import_block.split('\n'):
                import_match = re.search(r'[\'"]([^\'"]+)[\'"]', import_line)
                if import_match:
                    import_info = {
                        "import": import_match.group(1),
                        "line_number": content[:match.start()].count('\n') + 1,
                        "type": "multi_import"
                    }
                    imports.append(import_info)
        
        return imports
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """提取函数定义"""
        functions = []
        
        # 函数定义模式
        function_pattern = r'func\s+(?:\(\s*[^)]*\s*\)\s+)?(\w+)\s*\([^)]*\)\s*(?:[\w\[\]]+)?\s*\{'
        
        for match in re.finditer(function_pattern, content):
            function_name = match.group(1)
            
            function_info = {
                "name": function_name,
                "line_number": content[:match.start()].count('\n') + 1,
                "receiver": self._extract_receiver(match.group(0)),
                "parameters": self._extract_function_parameters(match.group(0)),
                "return_type": self._extract_return_type(match.group(0))
            }
            functions.append(function_info)
        
        return functions
    
    def _extract_structs(self, content: str) -> List[Dict[str, Any]]:
        """提取结构体定义"""
        structs = []
        
        # 结构体定义模式
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            
            # 找到结构体的结束位置
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
            
            struct_content = content[start_pos:end_pos]
            
            struct_info = {
                "name": struct_name,
                "fields": self._extract_struct_fields(struct_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            structs.append(struct_info)
        
        return structs
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """提取接口定义"""
        interfaces = []
        
        # 接口定义模式
        interface_pattern = r'type\s+(\w+)\s+interface\s*\{'
        
        for match in re.finditer(interface_pattern, content):
            interface_name = match.group(1)
            
            # 找到接口的结束位置
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
            
            interface_content = content[start_pos:end_pos]
            
            interface_info = {
                "name": interface_name,
                "methods": self._extract_interface_methods(interface_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_variables(self, content: str) -> List[Dict[str, Any]]:
        """提取变量定义"""
        variables = []
        
        # 变量定义模式
        variable_patterns = [
            r'var\s+(\w+)\s+([^\s=]+)(?:\s*=\s*([^;]+))?',
            r'(\w+)\s*:=\s*([^;]+)'
        ]
        
        for pattern in variable_patterns:
            for match in re.finditer(pattern, content):
                var_name = match.group(1)
                var_type = match.group(2) if len(match.groups()) > 1 else None
                var_value = match.group(3) if len(match.groups()) > 2 else None
                
                variable_info = {
                    "name": var_name,
                    "type": var_type,
                    "value": var_value.strip() if var_value else None,
                    "line_number": content[:match.start()].count('\n') + 1
                }
                variables.append(variable_info)
        
        return variables
    
    def _extract_constants(self, content: str) -> List[Dict[str, Any]]:
        """提取常量定义"""
        constants = []
        
        # 常量定义模式
        const_pattern = r'const\s+(\w+)\s+([^\s=]+)(?:\s*=\s*([^;]+))?'
        
        for match in re.finditer(const_pattern, content):
            const_name = match.group(1)
            const_type = match.group(2)
            const_value = match.group(3)
            
            constant_info = {
                "name": const_name,
                "type": const_type,
                "value": const_value.strip() if const_value else None,
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
    
    def _extract_receiver(self, function_text: str) -> Optional[str]:
        """提取接收者"""
        receiver_match = re.search(r'func\s*\(\s*([^)]*)\s*\)', function_text)
        if receiver_match:
            return receiver_match.group(1).strip()
        return None
    
    def _extract_function_parameters(self, function_text: str) -> List[str]:
        """提取函数参数"""
        parameters = []
        
        # 提取参数列表
        param_match = re.search(r'func\s*(?:\(\s*[^)]*\s*\)\s+)?\w+\s*\(([^)]*)\)', function_text)
        if param_match:
            param_str = param_match.group(1)
            if param_str.strip():
                param_parts = param_str.split(',')
                for part in param_parts:
                    part = part.strip()
                    if part:
                        parameters.append(part)
        
        return parameters
    
    def _extract_return_type(self, function_text: str) -> Optional[str]:
        """提取返回类型"""
        return_match = re.search(r'func\s*(?:\(\s*[^)]*\s*\)\s+)?\w+\s*\([^)]*\)\s*([\w\[\]]+)', function_text)
        if return_match:
            return return_match.group(1)
        return None
    
    def _extract_struct_fields(self, struct_content: str) -> List[Dict[str, Any]]:
        """提取结构体字段"""
        fields = []
        
        # 字段定义模式
        field_pattern = r'(\w+)\s+([^\s\n]+)(?:\s+`[^`]*`)?'
        
        for match in re.finditer(field_pattern, struct_content):
            field_name = match.group(1)
            field_type = match.group(2)
            
            # 跳过方法定义
            if field_name == 'func':
                continue
            
            field_info = {
                "name": field_name,
                "type": field_type,
                "line_number": struct_content[:match.start()].count('\n') + 1
            }
            fields.append(field_info)
        
        return fields
    
    def _extract_interface_methods(self, interface_content: str) -> List[Dict[str, Any]]:
        """提取接口方法"""
        methods = []
        
        # 方法定义模式
        method_pattern = r'(\w+)\s*\([^)]*\)\s*([^\s\n]+)'
        
        for match in re.finditer(method_pattern, interface_content):
            method_name = match.group(1)
            return_type = match.group(2)
            
            method_info = {
                "name": method_name,
                "return_type": return_type,
                "line_number": interface_content[:match.start()].count('\n') + 1
            }
            methods.append(method_info)
        
        return methods
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "language": "go",
            "error": error,
            "package": None,
            "imports": [],
            "functions": [],
            "structs": [],
            "interfaces": [],
            "variables": [],
            "constants": [],
            "comments": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 