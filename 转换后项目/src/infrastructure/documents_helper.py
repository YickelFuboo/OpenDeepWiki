import os
import re
from typing import List, Optional
from loguru import logger

from src.models.document_catalog import DocumentCatalog
from src.models.warehouse import Warehouse
from src.models.document import Document


class DocumentResultCatalogueItem:
    """文档结果目录项"""
    def __init__(self, title: str = "", name: str = "", prompt: str = "", children: Optional[List['DocumentResultCatalogueItem']] = None):
        self.title = title
        self.name = name
        self.prompt = prompt
        self.children = children or []


class PathInfo:
    """路径信息"""
    def __init__(self, path: str = "", name: str = "", is_directory: bool = False, size: int = 0):
        self.path = path
        self.name = name
        self.is_directory = is_directory
        self.size = size


class DocumentsHelper:
    """文档辅助工具类"""
    
    @staticmethod
    def process_catalogue_items(items: List[DocumentResultCatalogueItem], parent_id: Optional[str],
                              warehouse: Warehouse, document: Document, documents: List[DocumentCatalog]):
        """处理目录项，递归生成文档目录"""
        order = 0  # 创建排序计数器
        for item in items:
            item.title = item.title.replace(" ", "")
            document_item = DocumentCatalog(
                warehouse_id=warehouse.id,
                description=item.title,
                id=f"{warehouse.id}_{item.title}",  # 简化ID生成
                name=item.name,
                url=item.title,
                document_id=document.id,
                parent_id=parent_id,
                prompt=item.prompt,
                order=order
            )
            order += 1
            
            documents.append(document_item)
            
            if item.children:
                DocumentsHelper.process_catalogue_items(item.children, document_item.id, warehouse, document, documents)
    
    @staticmethod
    async def read_me_file(path: str) -> str:
        """读取仓库的ReadMe文件"""
        readme_extensions = ["README.md", "README.rst", "README.txt", "README"]
        
        for ext in readme_extensions:
            readme_path = os.path.join(path, ext)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"读取README文件失败 {readme_path}: {e}")
        
        return ""
    
    @staticmethod
    def get_max_tokens(model: str) -> Optional[int]:
        """获取模型的最大tokens数量"""
        if model.lower().startswith("kimi-k2"):
            return 65535
        
        if model.lower().startswith("deepseek-r1"):
            return 32768
        
        if model.lower().startswith("o"):
            return 128000
        
        if model.lower().startswith("gpt-4"):
            return 8192
        
        if model.lower().startswith("gpt-3.5"):
            return 4096
        
        if model.lower().startswith("claude"):
            return 100000
        
        if model.lower().startswith("gemini"):
            return 32768
        
        return None
    
    @staticmethod
    def get_ignore_files(path: str) -> List[str]:
        """获取忽略文件列表"""
        ignore_files = []
        
        # 常见的忽略文件
        common_ignores = [
            ".git", ".svn", ".hg", ".bzr",
            "node_modules", "vendor", "target", "build", "dist",
            "__pycache__", ".pytest_cache", ".mypy_cache",
            ".DS_Store", "Thumbs.db",
            "*.log", "*.tmp", "*.temp",
            "*.exe", "*.dll", "*.so", "*.dylib",
            "*.pyc", "*.pyo", "*.pyd",
            "*.class", "*.jar", "*.war",
            "*.min.js", "*.min.css",
            "*.map", "*.sourcemap"
        ]
        
        ignore_files.extend(common_ignores)
        
        # 读取.gitignore文件
        gitignore_path = os.path.join(path, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ignore_files.append(line)
            except Exception as e:
                logger.error(f"读取.gitignore文件失败: {e}")
        
        return ignore_files
    
    @staticmethod
    def get_catalogue_files(path: str) -> List[PathInfo]:
        """获取目录文件列表"""
        info_list = []
        ignore_files = DocumentsHelper.get_ignore_files(path)
        DocumentsHelper.scan_directory(path, info_list, ignore_files)
        return info_list
    
    @staticmethod
    def get_catalogue(path: str) -> str:
        """获取目录结构"""
        info_list = DocumentsHelper.get_catalogue_files(path)
        
        catalogue_lines = []
        for info in info_list:
            prefix = "📁 " if info.is_directory else "📄 "
            relative_path = os.path.relpath(info.path, path)
            catalogue_lines.append(f"{prefix}{relative_path}")
        
        return "\n".join(catalogue_lines)
    
    @staticmethod
    def get_catalogue_optimized(path: str, format: str = "compact") -> str:
        """获取优化的目录结构"""
        info_list = DocumentsHelper.get_catalogue_files(path)
        
        if format == "compact":
            # 紧凑格式
            catalogue_lines = []
            for info in info_list:
                relative_path = os.path.relpath(info.path, path)
                if info.is_directory:
                    catalogue_lines.append(f"📁 {relative_path}/")
                else:
                    # 只显示文件名
                    filename = os.path.basename(info.path)
                    catalogue_lines.append(f"📄 {filename}")
            
            return "\n".join(catalogue_lines)
        else:
            # 详细格式
            return DocumentsHelper.get_catalogue(path)
    
    @staticmethod
    def scan_directory(directory_path: str, info_list: List[PathInfo], ignore_files: List[str]):
        """扫描目录"""
        try:
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                
                # 检查是否应该忽略
                should_ignore = False
                for ignore_pattern in ignore_files:
                    if DocumentsHelper._matches_pattern(item_path, ignore_pattern):
                        should_ignore = True
                        break
                
                if should_ignore:
                    continue
                
                if os.path.isdir(item_path):
                    # 目录
                    info_list.append(PathInfo(
                        path=item_path,
                        name=item,
                        is_directory=True,
                        size=0
                    ))
                    # 递归扫描子目录
                    DocumentsHelper.scan_directory(item_path, info_list, ignore_files)
                else:
                    # 文件
                    try:
                        size = os.path.getsize(item_path)
                        info_list.append(PathInfo(
                            path=item_path,
                            name=item,
                            is_directory=False,
                            size=size
                        ))
                    except OSError:
                        # 无法获取文件大小，跳过
                        continue
                        
        except PermissionError:
            # 没有权限访问目录
            logger.warning(f"没有权限访问目录: {directory_path}")
        except Exception as e:
            logger.error(f"扫描目录失败 {directory_path}: {e}")
    
    @staticmethod
    def _matches_pattern(path: str, pattern: str) -> bool:
        """检查路径是否匹配模式"""
        try:
            # 简单的通配符匹配
            if pattern.startswith("*"):
                suffix = pattern[1:]
                return path.endswith(suffix)
            elif pattern.endswith("*"):
                prefix = pattern[:-1]
                return path.startswith(prefix)
            else:
                return pattern in path
        except Exception:
            return False 