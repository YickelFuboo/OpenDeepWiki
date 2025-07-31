"""
C#代码解析器

解析C#代码结构，提取类、方法、属性等信息
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class CSharpParser:
    """C#代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.cs']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析C#文件
        
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
            logger.error(f"解析C#文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析C#代码内容
        
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
                "language": "csharp",
                "usings": self._extract_usings(content),
                "namespaces": self._extract_namespaces(content),
                "classes": self._extract_classes(content),
                "interfaces": self._extract_interfaces(content),
                "enums": self._extract_enums(content),
                "structs": self._extract_structs(content),
                "methods": self._extract_methods(content),
                "properties": self._extract_properties(content),
                "fields": self._extract_fields(content),
                "events": self._extract_events(content),
                "attributes": self._extract_attributes(content),
                "comments": self._extract_comments(content),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析C#内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_usings(self, content: str) -> List[Dict[str, Any]]:
        """提取using语句"""
        usings = []
        
        # using语句模式
        using_pattern = r'using\s+([^;]+);'
        
        for match in re.finditer(using_pattern, content):
            using_info = {
                "namespace": match.group(1).strip(),
                "line_number": content[:match.start()].count('\n') + 1
            }
            usings.append(using_info)
        
        return usings
    
    def _extract_namespaces(self, content: str) -> List[Dict[str, Any]]:
        """提取命名空间"""
        namespaces = []
        
        # 命名空间定义模式
        namespace_pattern = r'namespace\s+([^{]+)\s*\{'
        
        for match in re.finditer(namespace_pattern, content):
            namespace_name = match.group(1).strip()
            
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
                "classes": self._extract_classes(namespace_content),
                "interfaces": self._extract_interfaces(namespace_content),
                "enums": self._extract_enums(namespace_content),
                "structs": self._extract_structs(namespace_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            namespaces.append(namespace_info)
        
        return namespaces
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """提取类定义"""
        classes = []
        
        # 类定义模式
        class_patterns = [
            r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:abstract\s+|sealed\s+|static\s+)?class\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{',
            r'class\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{'
        ]
        
        for pattern in class_patterns:
            for match in re.finditer(pattern, content):
                class_name = match.group(1)
                base_classes = match.group(2) if len(match.groups()) > 1 else None
                
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
                    "base_classes": [b.strip() for b in base_classes.split(',')] if base_classes else [],
                    "modifiers": self._extract_modifiers(match.group(0)),
                    "methods": self._extract_methods(class_content),
                    "properties": self._extract_properties(class_content),
                    "fields": self._extract_fields(class_content),
                    "events": self._extract_events(class_content),
                    "constructors": self._extract_constructors(class_content),
                    "line_number": content[:match.start()].count('\n') + 1
                }
                classes.append(class_info)
        
        return classes
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """提取接口定义"""
        interfaces = []
        
        # 接口定义模式
        interface_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?interface\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{'
        
        for match in re.finditer(interface_pattern, content):
            interface_name = match.group(1)
            base_interfaces = match.group(2) if len(match.groups()) > 1 else None
            
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
                "base_interfaces": [b.strip() for b in base_interfaces.split(',')] if base_interfaces else [],
                "methods": self._extract_interface_methods(interface_content),
                "properties": self._extract_properties(interface_content),
                "events": self._extract_events(interface_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        """提取枚举定义"""
        enums = []
        
        # 枚举定义模式
        enum_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?enum\s+(\w+)(?:\s*:\s*(\w+))?\s*\{'
        
        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            enum_type = match.group(2) if len(match.groups()) > 1 else None
            
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
                "type": enum_type,
                "values": self._extract_enum_values(enum_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            enums.append(enum_info)
        
        return enums
    
    def _extract_structs(self, content: str) -> List[Dict[str, Any]]:
        """提取结构体定义"""
        structs = []
        
        # 结构体定义模式
        struct_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?struct\s+(\w+)(?:\s*:\s*([^{]+))?\s*\{'
        
        for match in re.finditer(struct_pattern, content):
            struct_name = match.group(1)
            base_structs = match.group(2) if len(match.groups()) > 1 else None
            
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
                "base_structs": [b.strip() for b in base_structs.split(',')] if base_structs else [],
                "fields": self._extract_fields(struct_content),
                "properties": self._extract_properties(struct_content),
                "methods": self._extract_methods(struct_content),
                "line_number": content[:match.start()].count('\n') + 1
            }
            structs.append(struct_info)
        
        return structs
    
    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """提取方法定义"""
        methods = []
        
        # 方法定义模式
        method_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:virtual\s+|override\s+|abstract\s+|static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:where\s+[^{]+)?\s*\{'
        
        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            method_name = match.group(2)
            
            method_info = {
                "name": method_name,
                "return_type": return_type,
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0)),
                "parameters": self._extract_method_parameters(match.group(0))
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_properties(self, content: str) -> List[Dict[str, Any]]:
        """提取属性定义"""
        properties = []
        
        # 属性定义模式
        property_patterns = [
            r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:virtual\s+|override\s+|abstract\s+|static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\{\s*(?:get\s*;\s*)?(?:set\s*;\s*)?\}',
            r'(?:public\s+|private\s+|protected\s+|internal\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*=>\s*[^;]+;'
        ]
        
        for pattern in property_patterns:
            for match in re.finditer(pattern, content):
                property_type = match.group(1)
                property_name = match.group(2)
                
                property_info = {
                    "name": property_name,
                    "type": property_type,
                    "line_number": content[:match.start()].count('\n') + 1,
                    "modifiers": self._extract_modifiers(match.group(0)),
                    "has_getter": "get" in match.group(0),
                    "has_setter": "set" in match.group(0)
                }
                properties.append(property_info)
        
        return properties
    
    def _extract_fields(self, content: str) -> List[Dict[str, Any]]:
        """提取字段定义"""
        fields = []
        
        # 字段定义模式
        field_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:readonly\s+|const\s+|static\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
        for match in re.finditer(field_pattern, content):
            field_type = match.group(1)
            field_name = match.group(2)
            
            field_info = {
                "name": field_name,
                "type": field_type,
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0)),
                "is_readonly": "readonly" in match.group(0),
                "is_const": "const" in match.group(0),
                "is_static": "static" in match.group(0)
            }
            fields.append(field_info)
        
        return fields
    
    def _extract_events(self, content: str) -> List[Dict[str, Any]]:
        """提取事件定义"""
        events = []
        
        # 事件定义模式
        event_pattern = r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:virtual\s+|override\s+|abstract\s+)?event\s+(\w+(?:<[^>]+>)?)\s+(\w+);'
        
        for match in re.finditer(event_pattern, content):
            event_type = match.group(1)
            event_name = match.group(2)
            
            event_info = {
                "name": event_name,
                "type": event_type,
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            events.append(event_info)
        
        return events
    
    def _extract_attributes(self, content: str) -> List[Dict[str, Any]]:
        """提取特性定义"""
        attributes = []
        
        # 特性定义模式
        attribute_pattern = r'\[([^\]]+)\]'
        
        for match in re.finditer(attribute_pattern, content):
            attribute_content = match.group(1)
            
            attribute_info = {
                "content": attribute_content,
                "line_number": content[:match.start()].count('\n') + 1
            }
            attributes.append(attribute_info)
        
        return attributes
    
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
        
        # XML文档注释
        xml_comment_pattern = r'///\s*(.+)'
        for match in re.finditer(xml_comment_pattern, content):
            comment_info = {
                "content": match.group(1),
                "line_number": content[:match.start()].count('\n') + 1,
                "type": "xml_documentation"
            }
            comments.append(comment_info)
        
        return comments
    
    def _extract_interface_methods(self, interface_content: str) -> List[Dict[str, Any]]:
        """提取接口方法"""
        methods = []
        
        # 接口方法定义模式
        method_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*;'
        
        for match in re.finditer(method_pattern, interface_content):
            return_type = match.group(1)
            method_name = match.group(2)
            
            method_info = {
                "name": method_name,
                "return_type": return_type,
                "line_number": interface_content[:match.start()].count('\n') + 1
            }
            methods.append(method_info)
        
        return methods
    
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
                "parameters": self._extract_method_parameters(match.group(0))
            }
            constructors.append(constructor_info)
        
        return constructors
    
    def _extract_enum_values(self, enum_content: str) -> List[str]:
        """提取枚举值"""
        values = []
        
        # 枚举值模式
        value_pattern = r'(\w+)(?:\s*=\s*[^,}]+)?(?:\s*,|\s*$)'
        
        for match in re.finditer(value_pattern, enum_content):
            value = match.group(1)
            if value not in ['enum', 'class', 'struct', 'public', 'private', 'protected', 'internal']:
                values.append(value)
        
        return values
    
    def _extract_modifiers(self, text: str) -> List[str]:
        """提取修饰符"""
        modifiers = []
        modifier_keywords = ['public', 'private', 'protected', 'internal', 'virtual', 'override', 'abstract', 'static', 'sealed', 'readonly', 'const']
        
        for modifier in modifier_keywords:
            if modifier in text:
                modifiers.append(modifier)
        
        return modifiers
    
    def _extract_method_parameters(self, method_text: str) -> List[str]:
        """提取方法参数"""
        parameters = []
        
        # 提取参数列表
        param_match = re.search(r'\(([^)]*)\)', method_text)
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
            "language": "csharp",
            "error": error,
            "usings": [],
            "namespaces": [],
            "classes": [],
            "interfaces": [],
            "enums": [],
            "structs": [],
            "methods": [],
            "properties": [],
            "fields": [],
            "events": [],
            "attributes": [],
            "comments": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 