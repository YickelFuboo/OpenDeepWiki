"""
C++代码解析器

解析C++代码结构，提取类、函数、变量等信息
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CppParser:
    """C++代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析C++文件
        
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
            logger.error(f"解析C++文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析C++代码内容
        
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
                "language": "cpp",
                "includes": self._extract_includes(content),
                "namespaces": self._extract_namespaces(content),
                "classes": self._extract_classes(content),
                "functions": self._extract_functions(content),
                "variables": self._extract_variables(content),
                "enums": self._extract_enums(content),
                "structs": self._extract_structs(content),
                "templates": self._extract_templates(content),
                "comments": self._extract_comments(content),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析C++内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_includes(self, content: str) -> List[Dict[str, Any]]:
        """提取包含语句"""
        includes = []
        
        # #include语句
        include_pattern = r'#include\s*[<"]([^>"]+)[>"]'
        
        for match in re.finditer(include_pattern, content):
            include_info = {
                "include": match.group(1),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "system" if match.group(0).find('<') > -1 else "local"
            }
            includes.append(include_info)
        
        return includes
    
    def _extract_namespaces(self, content: str) -> List[Dict[str, Any]]:
        """提取命名空间"""
        namespaces = []
        
        # 命名空间定义模式
        namespace_pattern = r'namespace\s+(\w+)\s*\{'
        
        for match in re.finditer(namespace_pattern, content):
            namespace_name = match.group(1)
            
            # 找到命名空间的结束位置
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
            
            namespace_content = content[start_pos:end_pos]
            
            namespace_info = {
                "name": namespace_name,
                "functions": self._extract_functions(namespace_content),
                "classes": self._extract_classes(namespace_content),
                "variables": self._extract_variables(namespace_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            namespaces.append(namespace_info)
        
        return namespaces
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """提取类定义"""
        classes = []
        
        # 类定义模式
        class_patterns = [
            r'class\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?\s*\{',
            r'class\s+(\w+)\s*\{'
        ]
        
        for pattern in class_patterns:
            for match in re.finditer(pattern, content):
                class_name = match.group(1)
                base_class = match.group(2) if len(match.groups()) > 1 else None
                
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
                    "base_class": base_class,
                    "methods": self._extract_class_methods(class_content),
                    "members": self._extract_class_members(class_content),
                    "constructors": self._extract_constructors(class_content),
                    "destructors": self._extract_destructors(class_content),
                    "line_number": content[:match.start()].count('\n') + 1
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """提取函数定义"""
        functions = []
        
        # 函数定义模式
        function_patterns = [
            r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*\{',
            r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*;',
            r'(\w+)\s+(\w+)\s*\([^)]*\)\s*=\s*default;',
            r'(\w+)\s+(\w+)\s*\([^)]*\)\s*=\s*delete;'
        ]
        
        for pattern in function_patterns:
            for match in re.finditer(pattern, content):
                return_type = match.group(1)
                function_name = match.group(2)
                
                # 跳过构造函数和析构函数
                if function_name == return_type or function_name.startswith('~'):
                    continue
                
                function_info = {
                    "name": function_name,
                    "return_type": return_type,
                    "line_number": content[:match.start()].count('\n') + 1,
                    "parameters": self._extract_function_parameters(match.group(0)),
                    "is_const": "const" in match.group(0),
                    "is_virtual": "virtual" in match.group(0),
                    "is_static": "static" in match.group(0)
                }
                functions.append(function_info)
        
        return functions
    
    def _extract_variables(self, content: str) -> List[Dict[str, Any]]:
        """提取变量定义"""
        variables = []
        
        # 变量定义模式
        variable_patterns = [
            r'(?:static\s+)?(?:const\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*[^;]+)?;',
            r'(?:static\s+)?(?:const\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\[\s*\];'
        ]
        
        for pattern in variable_patterns:
            for match in re.finditer(pattern, content):
                var_type = match.group(1)
                var_name = match.group(2)
                
                # 跳过函数定义
                if '(' in var_name:
                    continue
                
                variable_info = {
                    "name": var_name,
                    "type": var_type,
                    "line_number": content[:match.start()].count('\n') + 1,
                    "is_static": "static" in match.group(0),
                    "is_const": "const" in match.group(0),
                    "is_array": '[' in match.group(0)
                }
                variables.append(variable_info)
        
        return variables
    
    def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        """提取枚举定义"""
        enums = []
        
        # 枚举定义模式
        enum_patterns = [
            r'enum\s+class\s+(\w+)\s*\{',
            r'enum\s+(\w+)\s*\{'
        ]
        
        for pattern in enum_patterns:
            for match in re.finditer(pattern, content):
                enum_name = match.group(1)
                
                # 找到枚举的结束位置
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
                
                enum_content = content[start_pos:end_pos]
                
                enum_info = {
                    "name": enum_name,
                    "values": self._extract_enum_values(enum_content),
                    "line_number": content[:match.start()].count('\n') + 1,
                    "is_class": "class" in match.group(0)
                }
                enums.append(enum_info)
        
        return enums
    
    def _extract_structs(self, content: str) -> List[Dict[str, Any]]:
        """提取结构体定义"""
        structs = []
        
        # 结构体定义模式
        struct_pattern = r'struct\s+(\w+)(?:\s*:\s*(?:public|private|protected)\s+(\w+))?\s*\{'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            base_struct = match.group(2) if len(match.groups()) > 1 else None
            
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
                "base_struct": base_struct,
                "members": self._extract_struct_members(struct_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            structs.append(struct_info)
        
        return structs
    
    def _extract_templates(self, content: str) -> List[Dict[str, Any]]:
        """提取模板定义"""
        templates = []
        
        # 模板定义模式
        template_patterns = [
            r'template\s*<\s*([^>]+)\s*>\s*class\s+(\w+)',
            r'template\s*<\s*([^>]+)\s*>\s*(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)'
        ]
        
        for pattern in template_patterns:
            for match in re.finditer(pattern, content):
                template_params = match.group(1)
                template_name = match.group(2)
                
                template_info = {
                    "name": template_name,
                    "parameters": template_params,
                    "line_number": content[:match.start()].count('\n') + 1
                }
                templates.append(template_info)
        
        return templates
    
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
            r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*\{',
            r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*;',
            r'virtual\s+(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:const)?\s*;'
        ]
        
        for pattern in method_patterns:
            for match in re.finditer(pattern, class_content):
                return_type = match.group(1)
                method_name = match.group(2)
                
                # 跳过构造函数和析构函数
                if method_name == return_type or method_name.startswith('~'):
                    continue
                
                method_info = {
                    "name": method_name,
                    "return_type": return_type,
                    "line_number": class_content[:match.start()].count('\n') + 1,
                    "is_virtual": "virtual" in match.group(0),
                    "is_const": "const" in match.group(0),
                    "is_static": "static" in match.group(0)
                }
                methods.append(method_info)
        
        return methods
    
    def _extract_class_members(self, class_content: str) -> List[Dict[str, Any]]:
        """提取类成员"""
        members = []
        
        # 成员定义模式
        member_pattern = r'(?:static\s+)?(?:const\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
        for match in re.finditer(member_pattern, class_content):
            member_type = match.group(1)
            member_name = match.group(2)
            
            # 跳过方法定义
            if '(' in member_name:
                continue
            
            member_info = {
                "name": member_name,
                "type": member_type,
                "line_number": class_content[:match.start()].count('\n') + 1,
                "is_static": "static" in match.group(0),
                "is_const": "const" in match.group(0)
            }
            members.append(member_info)
        
        return members
    
    def _extract_constructors(self, class_content: str) -> List[Dict[str, Any]]:
        """提取构造函数"""
        constructors = []
        
        # 构造函数定义模式
        constructor_pattern = r'(\w+)\s*\([^)]*\)\s*(?::\s*[^,{]+(?:,\s*[^,{]+)*)?\s*\{'
        
        for match in re.finditer(constructor_pattern, class_content):
            constructor_name = match.group(1)
            
            constructor_info = {
                "name": constructor_name,
                "line_number": class_content[:match.start()].count('\n') + 1,
                "parameters": self._extract_function_parameters(match.group(0))
            }
            constructors.append(constructor_info)
        
        return constructors
    
    def _extract_destructors(self, class_content: str) -> List[Dict[str, Any]]:
        """提取析构函数"""
        destructors = []
        
        # 析构函数定义模式
        destructor_pattern = r'~(\w+)\s*\([^)]*\)\s*\{'
        
        for match in re.finditer(destructor_pattern, class_content):
            destructor_name = match.group(1)
            
            destructor_info = {
                "name": destructor_name,
                "line_number": class_content[:match.start()].count('\n') + 1
            }
            destructors.append(destructor_info)
        
        return destructors
    
    def _extract_struct_members(self, struct_content: str) -> List[Dict[str, Any]]:
        """提取结构体成员"""
        members = []
        
        # 成员定义模式
        member_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:\[\s*\])?\s*;'
        
        for match in re.finditer(member_pattern, struct_content):
            member_type = match.group(1)
            member_name = match.group(2)
            
            member_info = {
                "name": member_name,
                "type": member_type,
                "line_number": struct_content[:match.start()].count('\n') + 1,
                "is_array": '[' in match.group(0)
            }
            members.append(member_info)
        
        return members
    
    def _extract_enum_values(self, enum_content: str) -> List[str]:
        """提取枚举值"""
        values = []
        
        # 枚举值模式
        value_pattern = r'(\w+)(?:\s*=\s*[^,}]+)?(?:\s*,|\s*$)'
        
        for match in re.finditer(value_pattern, enum_content):
            value = match.group(1)
            if value not in ['enum', 'class', 'struct', 'public', 'private', 'protected']:
                values.append(value)
        
        return values
    
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
            "language": "cpp",
            "error": error,
            "includes": [],
            "namespaces": [],
            "classes": [],
            "functions": [],
            "variables": [],
            "enums": [],
            "structs": [],
            "templates": [],
            "comments": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 