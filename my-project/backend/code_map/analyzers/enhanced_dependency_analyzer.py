"""
增强依赖分析器

分析代码中的依赖关系，包括函数调用、类继承、接口实现等
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
import networkx as nx

logger = logging.getLogger(__name__)

class EnhancedDependencyAnalyzer:
    """增强依赖分析器"""
    
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.function_calls = {}
        self.class_inheritance = {}
        self.interface_implementations = {}
        self.import_dependencies = {}
    
    def analyze_file(self, file_path: str, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析文件的依赖关系
        
        Args:
            file_path: 文件路径
            parsed_content: 解析后的内容
            
        Returns:
            依赖分析结果
        """
        try:
            result = {
                "file_path": file_path,
                "function_calls": self._analyze_function_calls(parsed_content),
                "class_dependencies": self._analyze_class_dependencies(parsed_content),
                "import_dependencies": self._analyze_import_dependencies(parsed_content),
                "circular_dependencies": self._detect_circular_dependencies(),
                "dependency_metrics": self._calculate_dependency_metrics(),
                "coupling_analysis": self._analyze_coupling(parsed_content),
                "cohesion_analysis": self._analyze_cohesion(parsed_content)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析文件依赖异常: {file_path}, 错误: {str(e)}")
            return self._create_error_result(file_path, str(e))
    
    def _analyze_function_calls(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析函数调用关系"""
        function_calls = {
            "internal_calls": [],
            "external_calls": [],
            "recursive_calls": [],
            "call_graph": {}
        }
        
        # 获取所有函数
        functions = parsed_content.get("functions", [])
        function_names = [func["name"] for func in functions]
        
        # 分析函数调用（简化实现）
        for func in functions:
            func_name = func["name"]
            calls = self._extract_function_calls_from_content(parsed_content.get("content", ""), func_name)
            
            function_calls["call_graph"][func_name] = calls
            
            for call in calls:
                if call in function_names:
                    function_calls["internal_calls"].append({
                        "caller": func_name,
                        "callee": call,
                        "line_number": func.get("line_number", 0)
                    })
                else:
                    function_calls["external_calls"].append({
                        "caller": func_name,
                        "callee": call,
                        "line_number": func.get("line_number", 0)
                    })
        
        return function_calls
    
    def _analyze_class_dependencies(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析类依赖关系"""
        class_dependencies = {
            "inheritance": [],
            "composition": [],
            "association": [],
            "interface_implementations": [],
            "dependency_graph": {}
        }
        
        # 分析类继承关系
        classes = parsed_content.get("classes", [])
        for cls in classes:
            class_name = cls["name"]
            base_classes = cls.get("base_classes", [])
            
            for base_class in base_classes:
                class_dependencies["inheritance"].append({
                    "derived": class_name,
                    "base": base_class,
                    "line_number": cls.get("line_number", 0)
                })
        
        # 分析接口实现
        interfaces = parsed_content.get("interfaces", [])
        for interface in interfaces:
            interface_name = interface["name"]
            base_interfaces = interface.get("base_interfaces", [])
            
            for base_interface in base_interfaces:
                class_dependencies["interface_implementations"].append({
                    "implementer": interface_name,
                    "interface": base_interface,
                    "line_number": interface.get("line_number", 0)
                })
        
        return class_dependencies
    
    def _analyze_import_dependencies(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析导入依赖"""
        import_dependencies = {
            "system_imports": [],
            "local_imports": [],
            "third_party_imports": [],
            "import_graph": {}
        }
        
        # 分析导入语句
        imports = parsed_content.get("imports", [])
        for import_info in imports:
            import_path = import_info.get("import", "")
            import_type = import_info.get("type", "unknown")
            
            if import_type == "system":
                import_dependencies["system_imports"].append(import_path)
            elif import_type == "local":
                import_dependencies["local_imports"].append(import_path)
            else:
                import_dependencies["third_party_imports"].append(import_path)
        
        return import_dependencies
    
    def _detect_circular_dependencies(self) -> List[Dict[str, Any]]:
        """检测循环依赖"""
        circular_dependencies = []
        
        try:
            # 使用NetworkX检测循环
            cycles = list(nx.simple_cycles(self.dependency_graph))
            
            for cycle in cycles:
                circular_dependencies.append({
                    "cycle": cycle,
                    "length": len(cycle),
                    "severity": "high" if len(cycle) <= 3 else "medium"
                })
        
        except Exception as e:
            logger.error(f"检测循环依赖异常: {str(e)}")
        
        return circular_dependencies
    
    def _calculate_dependency_metrics(self) -> Dict[str, Any]:
        """计算依赖指标"""
        metrics = {
            "total_dependencies": len(self.dependency_graph.edges()),
            "total_nodes": len(self.dependency_graph.nodes()),
            "average_dependencies_per_node": 0,
            "max_dependencies": 0,
            "min_dependencies": 0,
            "dependency_density": 0
        }
        
        if metrics["total_nodes"] > 0:
            metrics["average_dependencies_per_node"] = metrics["total_dependencies"] / metrics["total_nodes"]
            metrics["dependency_density"] = metrics["total_dependencies"] / (metrics["total_nodes"] * (metrics["total_nodes"] - 1))
            
            # 计算最大和最小依赖数
            in_degrees = dict(self.dependency_graph.in_degree())
            if in_degrees:
                metrics["max_dependencies"] = max(in_degrees.values())
                metrics["min_dependencies"] = min(in_degrees.values())
        
        return metrics
    
    def _analyze_coupling(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析耦合度"""
        coupling = {
            "afferent_coupling": {},  # 传入耦合
            "efferent_coupling": {},  # 传出耦合
            "instability": {},
            "abstractness": {}
        }
        
        # 计算传入耦合（有多少其他模块依赖此模块）
        for node in self.dependency_graph.nodes():
            coupling["afferent_coupling"][node] = self.dependency_graph.in_degree(node)
        
        # 计算传出耦合（此模块依赖多少其他模块）
        for node in self.dependency_graph.nodes():
            coupling["efferent_coupling"][node] = self.dependency_graph.out_degree(node)
        
        # 计算不稳定性
        for node in self.dependency_graph.nodes():
            efferent = coupling["efferent_coupling"][node]
            afferent = coupling["afferent_coupling"][node]
            total = efferent + afferent
            
            if total > 0:
                coupling["instability"][node] = efferent / total
            else:
                coupling["instability"][node] = 0
        
        return coupling
    
    def _analyze_cohesion(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """分析内聚度"""
        cohesion = {
            "method_cohesion": {},
            "class_cohesion": {},
            "module_cohesion": {}
        }
        
        # 分析类内聚度
        classes = parsed_content.get("classes", [])
        for cls in classes:
            class_name = cls["name"]
            methods = cls.get("methods", [])
            fields = cls.get("fields", [])
            
            # 计算类内聚度（简化实现）
            total_elements = len(methods) + len(fields)
            if total_elements > 0:
                cohesion["class_cohesion"][class_name] = len(methods) / total_elements
            else:
                cohesion["class_cohesion"][class_name] = 0
        
        return cohesion
    
    def _extract_function_calls_from_content(self, content: str, function_name: str) -> List[str]:
        """从内容中提取函数调用"""
        calls = []
        
        # 简化的函数调用提取（实际项目中需要更复杂的AST分析）
        # 这里只是示例实现
        import re
        
        # 查找函数调用模式
        call_pattern = r'(\w+)\s*\('
        
        for match in re.finditer(call_pattern, content):
            call_name = match.group(1)
            if call_name != function_name and call_name not in ['if', 'for', 'while', 'switch', 'catch']:
                calls.append(call_name)
        
        return list(set(calls))  # 去重
    
    def add_dependency(self, from_node: str, to_node: str, dependency_type: str = "calls"):
        """添加依赖关系"""
        self.dependency_graph.add_edge(from_node, to_node, type=dependency_type)
    
    def remove_dependency(self, from_node: str, to_node: str):
        """移除依赖关系"""
        if self.dependency_graph.has_edge(from_node, to_node):
            self.dependency_graph.remove_edge(from_node, to_node)
    
    def get_dependency_path(self, from_node: str, to_node: str) -> List[str]:
        """获取依赖路径"""
        try:
            path = nx.shortest_path(self.dependency_graph, from_node, to_node)
            return path
        except nx.NetworkXNoPath:
            return []
    
    def get_dependent_modules(self, module: str) -> List[str]:
        """获取依赖指定模块的所有模块"""
        dependents = []
        for node in self.dependency_graph.nodes():
            if nx.has_path(self.dependency_graph, node, module):
                dependents.append(node)
        return dependents
    
    def get_dependency_tree(self, root: str, max_depth: int = 3) -> Dict[str, Any]:
        """获取依赖树"""
        tree = {
            "node": root,
            "children": [],
            "depth": 0
        }
        
        if max_depth > 0:
            successors = list(self.dependency_graph.successors(root))
            for successor in successors:
                child_tree = self.get_dependency_tree(successor, max_depth - 1)
                child_tree["depth"] = tree["depth"] + 1
                tree["children"].append(child_tree)
        
        return tree
    
    def export_dependency_graph(self, format: str = "json") -> str:
        """导出依赖图"""
        if format == "json":
            import json
            return json.dumps(nx.node_link_data(self.dependency_graph), indent=2)
        elif format == "dot":
            return nx.drawing.nx_pydot.to_pydot(self.dependency_graph).to_string()
        else:
            return str(self.dependency_graph)
    
    def _create_error_result(self, file_path: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            "file_path": file_path,
            "error": error,
            "function_calls": {},
            "class_dependencies": {},
            "import_dependencies": {},
            "circular_dependencies": [],
            "dependency_metrics": {},
            "coupling_analysis": {},
            "cohesion_analysis": {}
        } 