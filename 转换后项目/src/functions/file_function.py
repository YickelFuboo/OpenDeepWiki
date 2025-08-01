import json
import os
import aiofiles
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from semantic_kernel import kernel_function
from loguru import logger

from src.infrastructure.documents_helper import DocumentsHelper, PathInfo
from src.infrastructure.document_context import DocumentContext
from src.core.config import settings


@dataclass
class ReadFileItemInput:
    """读取文件项输入"""
    file_path: str
    offset: int = 0
    limit: int = 200


class FileFunction:
    """文件操作函数类
    
    该类提供AI内核与本地文件系统交互的功能，包括文件读取、文件信息获取、目录结构扫描等
    主要用于AI模型访问和分析代码仓库中的文件内容
    """
    
    def __init__(self, git_path: str):
        """
        初始化文件函数
        
        Args:
            git_path: Git仓库的本地路径，用于定位和访问仓库中的文件
        """
        self.git_path = git_path
    
    def get_tree(self) -> str:
        """
        获取当前仓库的压缩目录结构
        
        该方法扫描整个仓库目录，构建文件树结构，并返回压缩后的字符串表示
        主要用于AI模型了解项目的整体文件结构
        
        Returns:
            压缩后的目录结构字符串，包含所有文件和目录的层级关系
        """
        try:
            # 步骤1：获取忽略文件列表
            # 获取.gitignore等文件中定义的忽略规则，避免扫描不必要的文件
            ignore_files = DocumentsHelper.get_ignore_files(self.git_path)
            path_infos = []
            
            # 步骤2：递归扫描目录
            # 递归扫描仓库根目录下的所有文件和目录，构建路径信息列表
            DocumentsHelper.scan_directory(self.git_path, path_infos, ignore_files)
            
            # 步骤3：构建文件树
            # 将路径信息列表转换为树形结构
            file_tree = self._build_tree(path_infos, self.git_path)
            
            # 步骤4：转换为压缩字符串
            # 将文件树转换为紧凑的字符串格式，便于AI模型处理
            return self._to_compact_string(file_tree)
            
        except Exception as e:
            logger.error(f"获取目录结构失败: {e}")
            return f"Error getting tree: {str(e)}"
    
    @kernel_function(
        name="FileInfo",
        description="Before accessing or reading any file content, always use this method to retrieve the basic information for all specified files. Batch as many file paths as possible into a single call to maximize efficiency. Provide file paths as an array. The function returns a JSON object where each key is the file path and each value contains the file's name, size, extension, creation time, last write time, and last access time. Ensure this information is obtained and reviewed before proceeding to any file content operations."
    )
    def get_file_info_async(self, file_paths: List[str]) -> str:
        """
        获取文件基本信息
        
        该方法用于批量获取多个文件的基本信息，包括文件名、大小、扩展名、行数等
        建议在读取文件内容之前先调用此方法获取文件信息，以提高效率
        
        Args:
            file_paths: 要获取信息的文件路径数组，支持批量处理以提高效率
            
        Returns:
            JSON格式的文件信息，键为文件路径，值为包含文件详细信息的JSON对象
        """
        try:
            # 步骤1：初始化结果字典
            # 创建用于存储文件信息的字典，键为文件路径，值为文件信息JSON字符串
            result_dict = {}
            
            # 步骤2：去重处理
            # 移除重复的文件路径，避免重复处理同一文件
            file_paths = list(set(file_paths))
            
            # 步骤3：记录文件访问
            # 如果启用了文档上下文存储，将访问的文件路径添加到文档存储中
            if hasattr(DocumentContext, 'document_store') and DocumentContext.document_store:
                DocumentContext.document_store.files.extend(file_paths)
            
            # 步骤4：批量处理文件信息
            # 遍历所有文件路径，获取每个文件的基本信息
            for file_path in file_paths:
                # 构建完整的文件路径
                full_path = os.path.join(self.git_path, file_path.lstrip('/'))
                
                # 步骤4.1：检查文件是否存在
                if not os.path.exists(full_path):
                    result_dict[file_path] = "File not found"
                    continue
                
                # 步骤4.2：获取文件信息
                logger.info(f"Getting file info: {full_path}")
                
                try:
                    stat = os.stat(full_path)
                    file_name = os.path.basename(full_path)
                    file_ext = os.path.splitext(file_name)[1]
                    
                    # 获取文件行数
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines = len(f.readlines())
                    
                    # 获取文件信息并序列化为JSON格式
                    file_info = {
                        "name": file_name,
                        "length": stat.st_size,
                        "extension": file_ext,
                        "total_line": total_lines,
                        "created_time": stat.st_ctime,
                        "modified_time": stat.st_mtime,
                        "access_time": stat.st_atime
                    }
                    
                    result_dict[file_path] = json.dumps(file_info, ensure_ascii=False)
                    
                except Exception as e:
                    result_dict[file_path] = f"Error reading file: {str(e)}"
            
            # 步骤5：返回结果
            # 将所有文件信息序列化为JSON格式返回
            return json.dumps(result_dict, ensure_ascii=False)
            
        except Exception as e:
            # 异常处理
            # 记录错误信息，便于调试和问题排查
            logger.error(f"Error getting file info: {e}")
            return f"Error getting file info: {str(e)}"
    
    @kernel_function(
        name="ReadFiles",
        description="File Path array. Always batch multiple file paths to reduce the number of function calls."
    )
    async def read_files_async(self, file_paths: List[str]) -> str:
        """
        批量读取文件内容
        
        该方法用于批量读取多个文件的内容，支持大文件处理（超过100KB的文件会提示使用行读取）
        建议批量处理多个文件以提高效率，减少函数调用次数
        
        Args:
            file_paths: 要读取的文件路径数组，支持批量处理以提高效率
            
        Returns:
            JSON格式的文件内容，键为文件路径，值为文件内容或提示信息
        """
        try:
            # 步骤1：去重处理
            # 移除重复的文件路径，避免重复读取同一文件
            file_paths = list(set(file_paths))
            
            # 步骤2：记录文件访问
            # 如果启用了文档上下文存储，将访问的文件路径添加到文档存储中
            if hasattr(DocumentContext, 'document_store') and DocumentContext.document_store:
                DocumentContext.document_store.files.extend(file_paths)
            
            # 步骤3：批量读取文件内容
            result_dict = {}
            
            for file_path in file_paths:
                # 构建完整的文件路径
                full_path = os.path.join(self.git_path, file_path.lstrip('/'))
                
                # 步骤3.1：检查文件是否存在
                if not os.path.exists(full_path):
                    continue
                
                logger.info(f"Reading file: {full_path}")
                
                try:
                    stat = os.stat(full_path)
                    
                    # 步骤3.2：大文件处理
                    # 如果文件大小超过100KB，提示使用行读取方法
                    if stat.st_size > 1024 * 100:
                        result_dict[file_path] = "If the file exceeds 100KB, you should use ReadFileFromLineAsync to read the file content line by line"
                    else:
                        # 步骤3.3：读取文件内容
                        # 读取整个文件内容
                        async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = await f.read()
                        
                        # 步骤3.4：代码压缩处理（简化实现）
                        # 如果启用代码压缩且是代码文件，则应用压缩算法
                        if hasattr(settings, 'enable_code_compression') and settings.enable_code_compression:
                            if self._is_code_file(file_path):
                                content = self._compress_code(content, file_path)
                        
                        result_dict[file_path] = content
                        
                except Exception as e:
                    result_dict[file_path] = f"Error reading file: {str(e)}"
            
            # 步骤4：返回结果
            # 将所有文件内容序列化为JSON格式返回
            return json.dumps(result_dict, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error reading files: {e}")
            return f"Error reading files: {str(e)}"
    
    @kernel_function(
        name="ReadFile",
        description="Read a single file from the local filesystem"
    )
    async def read_file_async(self, file_path: str) -> str:
        """
        读取单个文件内容
        
        Args:
            file_path: 要读取的文件路径
            
        Returns:
            文件内容字符串
        """
        try:
            full_path = os.path.join(self.git_path, file_path.lstrip('/'))
            
            if not os.path.exists(full_path):
                return "File not found"
            
            async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            return content
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return f"Error reading file: {str(e)}"
    
    @kernel_function(
        name="File",
        description="Reads a file from the local filesystem. You can access any file directly by using this tool."
    )
    async def read_file_from_line_async(self, items: List[ReadFileItemInput]) -> str:
        """
        从指定行读取文件内容
        
        Args:
            items: 读取文件项输入列表
            
        Returns:
            文件内容字符串
        """
        try:
            result_lines = []
            
            for item in items:
                full_path = os.path.join(self.git_path, item.file_path.lstrip('/'))
                
                if not os.path.exists(full_path):
                    result_lines.append(f"File not found: {item.file_path}")
                    continue
                
                try:
                    async with aiofiles.open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = await f.readlines()
                    
                    # 计算起始和结束行
                    start_line = max(0, item.offset)
                    end_line = min(len(lines), start_line + item.limit)
                    
                    # 添加行号格式的内容
                    for i in range(start_line, end_line):
                        line_num = i + 1
                        result_lines.append(f"{line_num:6d}  {lines[i].rstrip()}")
                        
                except Exception as e:
                    result_lines.append(f"Error reading file {item.file_path}: {str(e)}")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"Error reading files from line: {e}")
            return f"Error reading files from line: {str(e)}"
    
    def _build_tree(self, path_infos: List[PathInfo], root_path: str) -> Dict[str, Any]:
        """构建文件树"""
        tree = {}
        
        for path_info in path_infos:
            relative_path = os.path.relpath(path_info.path, root_path)
            parts = relative_path.split(os.sep)
            
            current = tree
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            if parts:
                current[parts[-1]] = {
                    "type": path_info.type,
                    "name": path_info.name
                }
        
        return tree
    
    def _to_compact_string(self, tree: Dict[str, Any], indent: int = 0) -> str:
        """将文件树转换为紧凑字符串"""
        lines = []
        indent_str = "  " * indent
        
        for name, content in sorted(tree.items()):
            if isinstance(content, dict) and "type" in content:
                # 文件
                lines.append(f"{indent_str}{name} ({content['type']})")
            else:
                # 目录
                lines.append(f"{indent_str}{name}/")
                lines.append(self._to_compact_string(content, indent + 1))
        
        return "\n".join(lines)
    
    def _is_code_file(self, file_path: str) -> bool:
        """判断是否为代码文件"""
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt'}
        return os.path.splitext(file_path)[1].lower() in code_extensions
    
    def _compress_code(self, content: str, file_path: str) -> str:
        """压缩代码内容（简化实现）"""
        # 这里可以实现代码压缩逻辑
        # 目前返回原内容
        return content 