"""
本地文件存储实现
"""

import os
import shutil
import logging
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid

from ..base import StorageInterface

logger = logging.getLogger(__name__)


class LocalStorage(StorageInterface):
    """本地文件存储实现"""
    
    def __init__(self, upload_dir: str):
        """
        初始化本地存储
        
        Args:
            upload_dir: 上传目录路径
        """
        self.upload_dir = Path(upload_dir)
        
        # 确保上传目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"本地存储初始化完成: {self.upload_dir}")
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str) -> str:
        """上传文件到本地存储"""
        try:
            # 生成唯一文件ID
            file_id = str(uuid.uuid4())
            
            # 创建文件目录
            file_dir = self.upload_dir / file_id
            file_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件路径
            file_path = file_dir / file_name
            
            # 保存文件
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            logger.info(f"文件上传成功: {file_path}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str) -> Optional[BinaryIO]:
        """下载文件"""
        try:
            file_dir = self.upload_dir / file_id
            if not file_dir.exists():
                return None
            
            # 查找文件
            for file_path in file_dir.iterdir():
                if file_path.is_file():
                    return open(file_path, 'rb')
            
            return None
            
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        try:
            file_dir = self.upload_dir / file_id
            if file_dir.exists():
                shutil.rmtree(file_dir)
                logger.info(f"文件删除成功: {file_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL - 本地存储返回文件路径"""
        try:
            file_dir = self.upload_dir / file_id
            if not file_dir.exists():
                return None
            
            # 查找文件
            for file_path in file_dir.iterdir():
                if file_path.is_file():
                    # 返回相对路径
                    return str(file_path.relative_to(self.upload_dir.parent))
            
            return None
            
        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return None
    
    def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        try:
            file_dir = self.upload_dir / file_id
            return file_dir.exists() and any(file_dir.iterdir())
        except Exception as e:
            logger.error(f"检查文件存在失败: {e}")
            return False
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            file_dir = self.upload_dir / file_id
            if not file_dir.exists():
                return None
            
            # 查找文件
            for file_path in file_dir.iterdir():
                if file_path.is_file():
                    stat = file_path.stat()
                    return {
                        'file_id': file_id,
                        'file_name': file_path.name,
                        'file_size': stat.st_size,
                        'created_at': datetime.fromtimestamp(stat.st_ctime),
                        'modified_at': datetime.fromtimestamp(stat.st_mtime),
                        'content_type': self._guess_content_type(file_path)
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None
    
    def _guess_content_type(self, file_path: Path) -> str:
        """猜测文件内容类型"""
        suffix = file_path.suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        return content_types.get(suffix, 'application/octet-stream')
    
    def close(self):
        """关闭存储连接（本地存储无需特殊处理）"""
        logger.info("本地存储连接关闭") 