"""
Go语义分析器

分析Go代码的语义信息，包括依赖关系、调用链等
"""

import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class GoSemanticAnalyzer:
    """Go语义分析器"""
    
    def __init__(self):
        self.dependencies = {}
        self.function_calls = {}
        self.type_relationships = {}
    
    def analyze_file(self, file_path: str, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析Go文件的语义信息
        
        Args:
            file_path: 文件路径
            parsed_content: 解析后的内容
            
        Returns:
            语义分析结果
        """
        try:
            result = {
                "file_path": file_path,
                "dependencies": self._analyze_dependencies(parsed_content),
                "function_calls": self._analyze_function_calls(parsed_content),
                "type_relationships": self._analyze_type_relationships(parsed_content),
                "complexity_metrics": self._calculate_complexity_metrics(parsed_content),
                "code_quality": self._analyze_code_quality(parsed_content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析Go文件语义异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _analyze_dependencies(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析依赖关系"""
        dependencies = {
            "imports": [],
            "external_packages": set(),
            "internal_dependencies": set()
        }
        
        # 分析导入的包
        for import_info in parsed_content.get("imports", []):
            import_path = import_info.get("import", "")
            dependencies["imports"].append({
                "path": import_path,
                "type": import_info.get("type", "unknown"),
                "line_number": import_info.get("line_number", 0)
            })
            
            # 区分外部包和内部包
            if import_path.startswith(("fmt", "os", "io", "net", "http", "encoding", "crypto", "math", "time", "sync", "context")):
                dependencies["external_packages"].add(import_path)
            else:
                dependencies["internal_dependencies"].add(import_path)
        
        # 转换为列表
        dependencies["external_packages"] = list(dependencies["external_packages"])
        dependencies["internal_dependencies"] = list(dependencies["internal_dependencies"])
        
        return dependencies
    
    def _analyze_function_calls(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析函数调用关系"""
        function_calls = {
            "internal_calls": [],
            "external_calls": [],
            "method_calls": [],
            "call_graph": {}
        }
        
        # 获取所有函数名
        function_names = [func["name"] for func in parsed_content.get("functions", [])]
        
        # 分析函数调用（这里需要更复杂的AST分析）
        # 简化实现，实际项目中需要更精确的AST解析
        
        return function_calls
    
    def _analyze_type_relationships(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析类型关系"""
        type_relationships = {
            "structs": [],
            "interfaces": [],
            "type_implementations": [],
            "type_hierarchy": {}
        }
        
        # 分析结构体
        for struct in parsed_content.get("structs", []):
            struct_info = {
                "name": struct["name"],
                "fields": struct.get("fields", []),
                "field_count": len(struct.get("fields", [])),
                "line_number": struct.get("line_number", 0)
            }
            type_relationships["structs"].append(struct_info)
        
        # 分析接口
        for interface in parsed_content.get("interfaces", []):
            interface_info = {
                "name": interface["name"],
                "methods": interface.get("methods", []),
                "method_count": len(interface.get("methods", [])),
                "line_number": interface.get("line_number", 0)
            }
            type_relationships["interfaces"].append(interface_info)
        
        return type_relationships
    
    def _calculate_complexity_metrics(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """计算复杂度指标"""
        metrics = {
            "cyclomatic_complexity": 0,
            "function_count": len(parsed_content.get("functions", [])),
            "struct_count": len(parsed_content.get("structs", [])),
            "interface_count": len(parsed_content.get("interfaces", [])),
            "variable_count": len(parsed_content.get("variables", [])),
            "constant_count": len(parsed_content.get("constants", [])),
            "line_count": parsed_content.get("line_count", 0),
            "comment_count": len(parsed_content.get("comments", [])),
            "comment_ratio": 0.0
        }
        
        # 计算注释比例
        if metrics["line_count"] > 0:
            metrics["comment_ratio"] = metrics["comment_count"] / metrics["line_count"]
        
        # 计算圈复杂度（简化实现）
        metrics["cyclomatic_complexity"] = self._calculate_cyclomatic_complexity(parsed_content)
        
        return metrics
    
    def _analyze_code_quality(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析代码质量"""
        quality = {
            "naming_conventions": self._check_naming_conventions(parsed_content),
            "function_length": self._analyze_function_length(parsed_content),
            "variable_usage": self._analyze_variable_usage(parsed_content),
            "code_style": self._check_code_style(parsed_content),
            "documentation": self._check_documentation(parsed_content)
        }
        
        return quality
    
    def _calculate_cyclomatic_complexity(self, parsed_content: Dict[str, Any]) -> int:
        """计算圈复杂度"""
        # 简化实现，实际需要分析控制流
        complexity = 1  # 基础复杂度
        
        # 根据函数数量增加复杂度
        complexity += len(parsed_content.get("functions", []))
        
        return complexity
    
    def _check_naming_conventions(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查命名规范"""
        naming_issues = []
        
        # 检查函数命名
        for func in parsed_content.get("functions", []):
            name = func["name"]
            if not self._is_valid_go_identifier(name):
                naming_issues.append({
                    "type": "function",
                    "name": name,
                    "issue": "Invalid function name"
                })
        
        # 检查变量命名
        for var in parsed_content.get("variables", []):
            name = var["name"]
            if not self._is_valid_go_identifier(name):
                naming_issues.append({
                    "type": "variable",
                    "name": name,
                    "issue": "Invalid variable name"
                })
        
        return {
            "issues": naming_issues,
            "score": max(0, 100 - len(naming_issues) * 10)
        }
    
    def _analyze_function_length(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析函数长度"""
        function_lengths = []
        
        for func in parsed_content.get("functions", []):
            # 简化实现，实际需要计算函数体长度
            function_lengths.append({
                "name": func["name"],
                "line_number": func.get("line_number", 0),
                "estimated_length": 10  # 简化估计
            })
        
        return {
            "function_lengths": function_lengths,
            "average_length": sum(f["estimated_length"] for f in function_lengths) / len(function_lengths) if function_lengths else 0,
            "long_functions": [f for f in function_lengths if f["estimated_length"] > 50]
        }
    
    def _analyze_variable_usage(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析变量使用情况"""
        variable_usage = {
            "unused_variables": [],
            "global_variables": [],
            "local_variables": []
        }
        
        # 简化实现，实际需要分析变量使用情况
        for var in parsed_content.get("variables", []):
            if var["name"].startswith("global"):
                variable_usage["global_variables"].append(var)
            else:
                variable_usage["local_variables"].append(var)
        
        return variable_usage
    
    def _check_code_style(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查代码风格"""
        style_issues = []
        
        # 检查是否有适当的注释
        if len(parsed_content.get("comments", [])) < len(parsed_content.get("functions", [])):
            style_issues.append("Insufficient documentation")
        
        # 检查包声明
        if not parsed_content.get("package"):
            style_issues.append("Missing package declaration")
        
        return {
            "issues": style_issues,
            "score": max(0, 100 - len(style_issues) * 20)
        }
    
    def _check_documentation(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """检查文档"""
        documentation = {
            "package_comment": False,
            "function_comments": [],
            "struct_comments": [],
            "interface_comments": []
        }
        
        # 检查包注释
        comments = parsed_content.get("comments", [])
        if any("package" in comment.get("content", "").lower() for comment in comments):
            documentation["package_comment"] = True
        
        # 检查函数注释
        for func in parsed_content.get("functions", []):
            has_comment = any(
                comment.get("line_number", 0) == func.get("line_number", 0) - 1
                for comment in comments
            )
            documentation["function_comments"].append({
                "function": func["name"],
                "has_comment": has_comment
            })
        
        return documentation
    
    def _is_valid_go_identifier(self, name: str) -> bool:
        """检查是否是有效的Go标识符"""
        if not name:
            return False
        
        # Go标识符规则：以字母或下划线开头，后面可以是字母、数字或下划线
        import re
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "error": error,
            "dependencies": {},
            "function_calls": {},
            "type_relationships": {},
            "complexity_metrics": {},
            "code_quality": {}
        } 