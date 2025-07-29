import os
import shutil
import zipfile
import tempfile
from typing import List, Dict, Any
import mimetypes
import logging

logger = logging.getLogger(__name__)


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            if not os.path.exists(file_path):
                return {"error": "文件不存在"}
            
            stat = os.stat(file_path)
            return {
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "extension": os.path.splitext(file_path)[1],
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "is_file": os.path.isfile(file_path),
                "is_directory": os.path.isdir(file_path)
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, 错误: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def read_file_content(file_path: str, max_size: int = 1024 * 1024) -> str:
        """读取文件内容"""
        try:
            if not os.path.exists(file_path):
                return "文件不存在"
            
            if not os.path.isfile(file_path):
                return "不是文件"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > max_size:
                return f"文件过大 ({file_size} bytes)，最大支持 {max_size} bytes"
            
            # 检查文件类型
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith('text/'):
                return f"不支持的文件类型: {mime_type}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except UnicodeDecodeError:
            return "文件编码不支持"
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
            return f"读取文件失败: {str(e)}"
    
    @staticmethod
    def scan_directory(directory_path: str, ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
        """扫描目录"""
        if ignore_patterns is None:
            ignore_patterns = ['.git', '__pycache__', '.DS_Store', 'node_modules']
        
        files = []
        
        def should_ignore(path: str) -> bool:
            """检查是否应该忽略"""
            for pattern in ignore_patterns:
                if pattern in path:
                    return True
            return False
        
        def scan_recursive(current_path: str, relative_path: str = ""):
            try:
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    item_relative_path = os.path.join(relative_path, item).replace("\\", "/")
                    
                    if should_ignore(item_relative_path):
                        continue
                    
                    if os.path.isdir(item_path):
                        files.append({
                            "path": item_relative_path,
                            "type": "directory",
                            "name": item
                        })
                        scan_recursive(item_path, item_relative_path)
                    else:
                        files.append({
                            "path": item_relative_path,
                            "type": "file",
                            "name": item,
                            "size": os.path.getsize(item_path)
                        })
            except PermissionError:
                # 跳过无权限的目录
                pass
        
        scan_recursive(directory_path)
        return files
    
    @staticmethod
    def create_zip_file(source_path: str, output_path: str) -> bool:
        """创建ZIP文件"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(source_path):
                    zipf.write(source_path, os.path.basename(source_path))
                else:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, source_path)
                            zipf.write(file_path, arcname)
            return True
        except Exception as e:
            logger.error(f"创建ZIP文件失败: {output_path}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def extract_zip_file(zip_path: str, extract_path: str) -> bool:
        """解压ZIP文件"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_path)
            return True
        except Exception as e:
            logger.error(f"解压ZIP文件失败: {zip_path}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """生成安全的文件名"""
        # 移除或替换不安全的字符
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        return filename
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """确保目录存在"""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"创建目录失败: {path}, 错误: {str(e)}")
            return False
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(file_path)[1].lower()
    
    @staticmethod
    def is_text_file(file_path: str) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
            '.java', '.c', '.cpp', '.h', '.cs', '.php', '.rb', '.go', '.rs',
            '.sql', '.sh', '.bat', '.ps1', '.yml', '.yaml', '.toml', '.ini',
            '.cfg', '.conf', '.log', '.csv', '.tsv'
        }
        return FileUtils.get_file_extension(file_path) in text_extensions 