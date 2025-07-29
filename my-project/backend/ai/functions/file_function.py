import os
import json
import logging
from typing import List, Dict, Any, Optional
from semantic_kernel import KernelFunction
from semantic_kernel.plugins import KernelPlugin

logger = logging.getLogger(__name__)


class FileFunction:
    """文件操作函数类，提供AI内核与本地文件系统交互的功能"""
    
    def __init__(self, git_path: str):
        """
        初始化文件操作函数
        
        Args:
            git_path: Git仓库的本地路径
        """
        self.git_path = git_path
        self._code_compression_service = None  # 代码压缩服务
    
    def get_tree(self) -> str:
        """
        获取当前仓库的压缩目录结构
        
        Returns:
            压缩后的目录结构字符串
        """
        try:
            tree = self._scan_directory_tree(self.git_path)
            return json.dumps(tree, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"获取目录结构失败: {e}")
            return f"获取目录结构失败: {str(e)}"
    
    def get_file_info(self, file_paths: List[str]) -> str:
        """
        批量获取多个文件的基本信息
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件信息JSON字符串
        """
        try:
            file_infos = []
            for file_path in file_paths:
                full_path = os.path.join(self.git_path, file_path)
                if os.path.exists(full_path):
                    stat = os.stat(full_path)
                    file_infos.append({
                        "path": file_path,
                        "name": os.path.basename(file_path),
                        "size": stat.st_size,
                        "extension": os.path.splitext(file_path)[1],
                        "is_file": os.path.isfile(full_path),
                        "is_directory": os.path.isdir(full_path)
                    })
            return json.dumps(file_infos, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return f"获取文件信息失败: {str(e)}"
    
    def read_files(self, file_paths: List[str], max_size: int = 1024 * 1024) -> str:
        """
        批量读取多个文件的内容
        
        Args:
            file_paths: 文件路径列表
            max_size: 最大文件大小限制
            
        Returns:
            文件内容JSON字符串
        """
        try:
            file_contents = []
            for file_path in file_paths:
                full_path = os.path.join(self.git_path, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    file_size = os.path.getsize(full_path)
                    if file_size > max_size:
                        content = f"文件过大 ({file_size} bytes)，最大支持 {max_size} bytes"
                    else:
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            content = "文件编码不支持"
                    file_contents.append({
                        "path": file_path,
                        "content": content,
                        "size": file_size
                    })
            return json.dumps(file_contents, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return f"读取文件失败: {str(e)}"
    
    def read_file(self, file_path: str, max_size: int = 1024 * 1024) -> str:
        """
        读取单个文件的内容
        
        Args:
            file_path: 文件路径
            max_size: 最大文件大小限制
            
        Returns:
            文件内容字符串
        """
        try:
            full_path = os.path.join(self.git_path, file_path)
            if not os.path.exists(full_path):
                return "文件不存在"
            
            if not os.path.isfile(full_path):
                return "不是文件"
            
            file_size = os.path.getsize(full_path)
            if file_size > max_size:
                return f"文件过大 ({file_size} bytes)，最大支持 {max_size} bytes"
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            return "文件编码不支持"
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return f"读取文件失败: {str(e)}"
    
    def read_file_lines(self, file_path: str, start_line: int = 1, line_count: int = 100) -> str:
        """
        按行读取文件内容
        
        Args:
            file_path: 文件路径
            start_line: 起始行号
            line_count: 读取行数
            
        Returns:
            文件行内容字符串
        """
        try:
            full_path = os.path.join(self.git_path, file_path)
            if not os.path.exists(full_path):
                return "文件不存在"
            
            if not os.path.isfile(full_path):
                return "不是文件"
            
            lines = []
            with open(full_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    if i >= start_line and i < start_line + line_count:
                        lines.append(line.rstrip())
                    elif i >= start_line + line_count:
                        break
            
            return '\n'.join(lines)
        except UnicodeDecodeError:
            return "文件编码不支持"
        except Exception as e:
            logger.error(f"读取文件行失败: {e}")
            return f"读取文件行失败: {str(e)}"
    
    def _scan_directory_tree(self, path: str, relative_path: str = "") -> Dict[str, Any]:
        """
        扫描目录树结构
        
        Args:
            path: 目录路径
            relative_path: 相对路径
            
        Returns:
            目录树结构字典
        """
        ignore_patterns = ['.git', '__pycache__', '.DS_Store', 'node_modules', '.vscode']
        
        def should_ignore(path_name: str) -> bool:
            """检查是否应该忽略"""
            for pattern in ignore_patterns:
                if pattern in path_name:
                    return True
            return False
        
        tree = {"type": "directory", "name": os.path.basename(path), "path": relative_path, "children": []}
        
        try:
            for item in os.listdir(path):
                if should_ignore(item):
                    continue
                
                item_path = os.path.join(path, item)
                item_relative_path = os.path.join(relative_path, item).replace("\\", "/")
                
                if os.path.isdir(item_path):
                    tree["children"].append(self._scan_directory_tree(item_path, item_relative_path))
                else:
                    tree["children"].append({
                        "type": "file",
                        "name": item,
                        "path": item_relative_path
                    })
        except PermissionError:
            tree["error"] = "权限不足"
        except Exception as e:
            tree["error"] = str(e)
        
        return tree 