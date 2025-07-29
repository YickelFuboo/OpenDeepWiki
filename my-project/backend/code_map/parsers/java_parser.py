"""
Java代码解析器

解析Java代码结构，提取类、方法、变量等信息
"""

import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class JavaParser:
    """Java代码解析器"""
    
    def __init__(self):
        self.supported_extensions = ['.java']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        解析Java文件
        
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
            logger.error(f"解析Java文件异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def parse_content(self, content: str, file_path: str = None) -> Dict[str, Any]:
        """
        解析Java代码内容
        
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
                "language": "java",
                "package": self._extract_package(content),
                "imports": self._extract_imports(content),
                "classes": self._extract_classes(content),
                "interfaces": self._extract_interfaces(content),
                "enums": self._extract_enums(content),
                "annotations": self._extract_annotations(content),
                "line_count": len(content.split('\n')),
                "char_count": len(content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"解析Java内容异常: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _extract_package(self, content: str) -> Optional[str]:
        """提取包声明"""
        package_match = re.search(r'package\s+([\w.]+);', content)
        if package_match:
            return package_match.group(1)
        return None
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """提取导入语句"""
        imports = []
        import_pattern = r'import\s+(static\s+)?([\w.*]+);'
        
        for match in re.finditer(import_pattern, content):
            import_info = {
                "import": match.group(2),
                "is_static": bool(match.group(1)),
                "line_number": content[:match.start()].count('\n') + 1
            }
            imports.append(import_info)
        
        return imports
    
    def _extract_classes(self, content: str) -> List[Dict[str, Any]]:
        """提取类定义"""
        classes = []
        
        # 类定义模式
        class_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w\s,]+))?\s*\{'
        
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            extends_class = match.group(2)
            implements_interfaces = match.group(3)
            
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
                "implements": [i.strip() for i in implements_interfaces.split(',')] if implements_interfaces else [],
                "methods": self._extract_methods(class_content),
                "fields": self._extract_fields(class_content),
                "constructors": self._extract_constructors(class_content),
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            classes.append(class_info)
        
        return classes
    
    def _extract_interfaces(self, content: str) -> List[Dict[str, Any]]:
        """提取接口定义"""
        interfaces = []
        
        # 接口定义模式
        interface_pattern = r'(?:public\s+|private\s+|protected\s+)?interface\s+(\w+)(?:\s+extends\s+([\w\s,]+))?\s*\{'
        
        for match in re.finditer(interface_pattern, content):
            interface_name = match.group(1)
            extends_interfaces = match.group(2)
            
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
                "extends": [i.strip() for i in extends_interfaces.split(',')] if extends_interfaces else [],
                "methods": self._extract_interface_methods(interface_content),
                "constants": self._extract_constants(interface_content),
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            interfaces.append(interface_info)
        
        return interfaces
    
    def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        """提取枚举定义"""
        enums = []
        
        # 枚举定义模式
        enum_pattern = r'(?:public\s+|private\s+|protected\s+)?enum\s+(\w+)(?:\s+implements\s+([\w\s,]+))?\s*\{'
        
        for match in re.finditer(enum_pattern, content):
            enum_name = match.group(1)
            implements_interfaces = match.group(2)
            
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
                "implements": [i.strip() for i in implements_interfaces.split(',')] if implements_interfaces else [],
                "values": self._extract_enum_values(enum_content),
                "methods": self._extract_methods(enum_content),
                "line_number": content[:match.start()].count('\n') + 1,
                "modifiers": self._extract_modifiers(match.group(0))
            }
            enums.append(enum_info)
        
        return enums
    
    def _extract_methods(self, content: str) -> List[Dict[str, Any]]:
        """提取方法定义"""
        methods = []
        
        # 方法定义模式
        method_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+|final\s+|abstract\s+|native\s+|synchronized\s+)*(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{?'
        
        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            method_name = match.group(2)
            
            # 跳过构造函数
            if method_name == return_type:
                continue
            
            method_info = {
                "name": method_name,
                "return_type": return_type,
                "modifiers": self._extract_modifiers(match.group(0)),
                "parameters": self._extract_parameters(match.group(0)),
                "line_number": content[:match.start()].count('\n') + 1
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_interface_methods(self, content: str) -> List[Dict[str, Any]]:
        """提取接口方法定义"""
        methods = []
        
        # 接口方法定义模式（默认public abstract）
        method_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)\s*;'
        
        for match in re.finditer(method_pattern, content):
            return_type = match.group(1)
            method_name = match.group(2)
            
            method_info = {
                "name": method_name,
                "return_type": return_type,
                "modifiers": ["public", "abstract"],
                "parameters": self._extract_parameters(match.group(0)),
                "line_number": content[:match.start()].count('\n') + 1
            }
            methods.append(method_info)
        
        return methods
    
    def _extract_fields(self, content: str) -> List[Dict[str, Any]]:
        """提取字段定义"""
        fields = []
        
        # 字段定义模式
        field_pattern = r'(?:public\s+|private\s+|protected\s+)?(?:static\s+|final\s+|volatile\s+|transient\s+)*(\w+(?:<[^>]+>)?)\s+(\w+)\s*(?:=\s*[^;]+)?;'
        
        for match in re.finditer(field_pattern, content):
            field_type = match.group(1)
            field_name = match.group(2)
            
            field_info = {
                "name": field_name,
                "type": field_type,
                "modifiers": self._extract_modifiers(match.group(0)),
                "line_number": content[:match.start()].count('\n') + 1
            }
            fields.append(field_info)
        
        return fields
    
    def _extract_constructors(self, content: str) -> List[Dict[str, Any]]:
        """提取构造函数定义"""
        constructors = []
        
        # 构造函数定义模式
        constructor_pattern = r'(?:public\s+|private\s+|protected\s+)?(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w\s,]+)?\s*\{'
        
        for match in re.finditer(constructor_pattern, content):
            constructor_name = match.group(1)
            
            constructor_info = {
                "name": constructor_name,
                "modifiers": self._extract_modifiers(match.group(0)),
                "parameters": self._extract_parameters(match.group(0)),
                "line_number": content[:match.start()].count('\n') + 1
            }
            constructors.append(constructor_info)
        
        return constructors
    
    def _extract_constants(self, content: str) -> List[Dict[str, Any]]:
        """提取常量定义"""
        constants = []
        
        # 常量定义模式（接口中的常量默认public static final）
        constant_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)\s*=\s*([^;]+);'
        
        for match in re.finditer(constant_pattern, content):
            constant_type = match.group(1)
            constant_name = match.group(2)
            constant_value = match.group(3)
            
            constant_info = {
                "name": constant_name,
                "type": constant_type,
                "value": constant_value.strip(),
                "modifiers": ["public", "static", "final"],
                "line_number": content[:match.start()].count('\n') + 1
            }
            constants.append(constant_info)
        
        return constants
    
    def _extract_enum_values(self, content: str) -> List[str]:
        """提取枚举值"""
        values = []
        
        # 枚举值模式
        value_pattern = r'(\w+)(?:\s*\([^)]*\))?(?:\s*,\s*|\s*;)'
        
        for match in re.finditer(value_pattern, content):
            value = match.group(1)
            if value not in ['public', 'private', 'protected', 'static', 'final', 'enum']:
                values.append(value)
        
        return values
    
    def _extract_annotations(self, content: str) -> List[Dict[str, Any]]:
        """提取注解定义"""
        annotations = []
        
        # 注解定义模式
        annotation_pattern = r'@(\w+)(?:\([^)]*\))?'
        
        for match in re.finditer(annotation_pattern, content):
            annotation_name = match.group(1)
            
            annotation_info = {
                "name": annotation_name,
                "line_number": content[:match.start()].count('\n') + 1
            }
            annotations.append(annotation_info)
        
        return annotations
    
    def _extract_modifiers(self, text: str) -> List[str]:
        """提取修饰符"""
        modifiers = []
        modifier_keywords = ['public', 'private', 'protected', 'static', 'final', 'abstract', 'native', 'synchronized', 'volatile', 'transient']
        
        for modifier in modifier_keywords:
            if modifier in text:
                modifiers.append(modifier)
        
        return modifiers
    
    def _extract_parameters(self, text: str) -> List[Dict[str, Any]]:
        """提取参数"""
        parameters = []
        
        # 提取参数列表
        param_match = re.search(r'\(([^)]*)\)', text)
        if param_match:
            param_str = param_match.group(1)
            if param_str.strip():
                param_parts = param_str.split(',')
                for i, part in enumerate(param_parts):
                    part = part.strip()
                    if part:
                        # 简单的参数解析
                        param_info = {
                            "index": i,
                            "text": part
                        }
                        parameters.append(param_info)
        
        return parameters
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "language": "java",
            "error": error,
            "package": None,
            "imports": [],
            "classes": [],
            "interfaces": [],
            "enums": [],
            "annotations": [],
            "line_count": 0,
            "char_count": 0
        }
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        return self.supported_extensions 