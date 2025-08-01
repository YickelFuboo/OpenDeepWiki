from typing import Dict, List, Optional
import os


class FileTreeNode:
    """文件树节点，用于构建节省tokens的树形结构"""
    
    def __init__(self, name: str = "", node_type: str = ""):
        self.name = name
        self.type = node_type  # F=文件，D=目录
        self.children: Dict[str, 'FileTreeNode'] = {}
    
    @property
    def is_file(self) -> bool:
        """是否为叶子节点（文件）"""
        return self.type == "F"
    
    @property
    def is_directory(self) -> bool:
        """是否为目录节点"""
        return self.type == "D"


class FileTreeBuilder:
    """文件树构建器"""
    
    @staticmethod
    def build_tree(path_infos: List['PathInfo'], base_path: str) -> FileTreeNode:
        """从路径信息列表构建文件树"""
        root = FileTreeNode(name="/", node_type="D")
        
        for path_info in path_infos:
            # 计算相对路径
            relative_path = path_info.path.replace(base_path, "").lstrip('\\/')
            
            # 过滤.开头的文件
            if relative_path.startswith("."):
                continue
            
            # 分割路径
            parts = [part for part in relative_path.replace('\\', '/').split('/') if part]
            
            # 从根节点开始构建路径
            current_node = root
            
            for i, part in enumerate(parts):
                is_last_part = i == len(parts) - 1
                
                if part not in current_node.children:
                    current_node.children[part] = FileTreeNode(
                        name=part,
                        node_type="F" if (is_last_part and path_info.type == "File") else "D"
                    )
                
                current_node = current_node.children[part]
        
        return root
    
    @staticmethod
    def to_compact_string(node: FileTreeNode, indent: int = 0) -> str:
        """将文件树转换为紧凑的字符串表示"""
        result = []
        indent_str = "  " * indent
        
        if indent == 0:
            result.append("/")
        
        # 按名称排序子节点
        sorted_children = sorted(node.children.items(), key=lambda x: x[0])
        
        for i, (child_name, child_node) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            
            if child_node.is_directory:
                result.append(f"{indent_str}{child_name}/")
                result.append(FileTreeBuilder.to_compact_string(child_node, indent + 1))
            else:
                result.append(f"{indent_str}{child_name}")
        
        return "\n".join(result)
    
    @staticmethod
    def to_compact_json(node: FileTreeNode) -> str:
        """将文件树转换为紧凑的JSON格式"""
        import json
        
        def serialize_node_compact(node: FileTreeNode) -> dict:
            result = {
                "name": node.name,
                "type": node.type
            }
            
            if node.children:
                result["children"] = {
                    name: serialize_node_compact(child)
                    for name, child in sorted(node.children.items())
                }
            
            return result
        
        return json.dumps(serialize_node_compact(node), ensure_ascii=False, indent=2)
    
    @staticmethod
    def to_path_list(node: FileTreeNode, current_path: str = "") -> List[str]:
        """将文件树转换为路径列表"""
        paths = []
        
        if node.name != "/":
            current_path = os.path.join(current_path, node.name) if current_path else node.name
        
        if node.is_file:
            paths.append(current_path)
        
        for child_name, child_node in sorted(node.children.items()):
            paths.extend(FileTreeBuilder.to_path_list(child_node, current_path))
        
        return paths
    
    @staticmethod
    def to_unix_tree(node: FileTreeNode, prefix: str = "", is_last: bool = True) -> str:
        """将文件树转换为Unix树形格式"""
        result = []
        
        if node.name == "/":
            result.append("/")
        else:
            result.append(f"{prefix}{'└── ' if is_last else '├── '}{node.name}")
            if node.is_directory:
                result.append(f"{prefix}{'    ' if is_last else '│   '}")
        
        # 按名称排序子节点
        sorted_children = sorted(node.children.items(), key=lambda x: x[0])
        
        for i, (child_name, child_node) in enumerate(sorted_children):
            child_is_last = i == len(sorted_children) - 1
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            result.append(FileTreeBuilder._to_unix_tree(
                child_node, child_prefix, child_is_last, child_name
            ))
        
        return "\n".join(result)
    
    @staticmethod
    def _to_unix_tree(
        node: FileTreeNode, 
        prefix: str, 
        is_last: bool, 
        node_name: str
    ) -> str:
        """Unix树形格式的辅助方法"""
        result = []
        
        if node.is_directory:
            result.append(f"{prefix}{'└── ' if is_last else '├── '}{node_name}/")
        else:
            result.append(f"{prefix}{'└── ' if is_last else '├── '}{node_name}")
        
        # 按名称排序子节点
        sorted_children = sorted(node.children.items(), key=lambda x: x[0])
        
        for i, (child_name, child_node) in enumerate(sorted_children):
            child_is_last = i == len(sorted_children) - 1
            child_prefix = prefix + ("    " if is_last else "│   ")
            
            result.append(FileTreeBuilder._to_unix_tree(
                child_node, child_prefix, child_is_last, child_name
            ))
        
        return "\n".join(result)


# 为了兼容性，添加PathInfo类的引用
try:
    from src.koala_warehouse.path_info import PathInfo
except ImportError:
    # 如果PathInfo不存在，创建一个简单的占位符
    class PathInfo:
        def __init__(self, path: str = "", path_type: str = ""):
            self.path = path
            self.type = path_type 