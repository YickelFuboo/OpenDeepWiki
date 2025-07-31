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
import json

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
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, 
                   bucket_name: str = "default", metadata: Optional[Dict[str, Any]] = None) -> str:
        """上传文件到本地存储"""
        try:
            # 生成唯一文件ID作为对象键
            file_id = str(uuid.uuid4())
            object_key = file_id
            
            # 创建bucket目录（如果不存在）
            bucket_dir = self.upload_dir / bucket_name
            bucket_dir.mkdir(parents=True, exist_ok=True)
            
            # 文件路径（直接使用file_id作为文件名）
            file_path = bucket_dir / object_key
            
            # 保存文件
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(file_data, f)
            
            # 保存元数据到单独的文件（可选，用于保持一致性）
            metadata_file = bucket_dir / f"{object_key}.meta"
            file_metadata = {
                'original-filename': file_name,
                'content-type': content_type,
                'upload-time': datetime.now().isoformat()
            }
            
            # 合并自定义元数据
            if metadata:
                file_metadata.update(metadata)
            
            # 保存元数据文件
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(file_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"文件上传成功: {bucket_name}/{object_key}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str, bucket_name: str = "default") -> Optional[BinaryIO]:
        """下载文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 构造文件路径
            bucket_dir = self.upload_dir / bucket_name
            file_path = bucket_dir / object_key
            
            if file_path.exists() and file_path.is_file():
                return open(file_path, 'rb')
            
            return None
            
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return None
    
    def delete_file(self, file_id: str, bucket_name: str = "default") -> bool:
        """删除文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 构造文件路径
            bucket_dir = self.upload_dir / bucket_name
            file_path = bucket_dir / object_key
            metadata_file = bucket_dir / f"{object_key}.meta"
            
            # 删除主文件
            if file_path.exists():
                file_path.unlink()
                logger.info(f"文件删除成功: {bucket_name}/{file_id}")
            
            # 删除元数据文件（如果存在）
            if metadata_file.exists():
                metadata_file.unlink()
                logger.debug(f"元数据文件删除成功: {bucket_name}/{object_key}.meta")
            
            return True
            
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, bucket_name: str = "default", expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL - 本地存储返回文件路径"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 构造文件路径
            bucket_dir = self.upload_dir / bucket_name
            file_path = bucket_dir / object_key
            
            if file_path.exists() and file_path.is_file():
                # 返回相对路径
                return str(file_path.relative_to(self.upload_dir.parent))
            
            return None
            
        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return None
    
    def file_exists(self, file_id: str, bucket_name: str = "default") -> bool:
        """检查文件是否存在"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 构造文件路径
            bucket_dir = self.upload_dir / bucket_name
            file_path = bucket_dir / object_key
            
            return file_path.exists() and file_path.is_file()
        except Exception as e:
            logger.error(f"检查文件存在失败: {e}")
            return False
    
    def get_file_metadata(self, file_id: str, bucket_name: str = "default") -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 构造文件路径
            bucket_dir = self.upload_dir / bucket_name
            file_path = bucket_dir / object_key
            metadata_file = bucket_dir / f"{object_key}.meta"
            
            if not file_path.exists():
                return None
            
            # 读取文件统计信息
            stat = file_path.stat()
            
            # 尝试读取保存的元数据
            saved_metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        saved_metadata = json.load(f)
                except Exception as e:
                    logger.warning(f"读取元数据文件失败: {e}")
            
            return {
                'file_id': file_id,
                'bucket_name': bucket_name,
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime),
                'content_type': saved_metadata.get('content-type', self._guess_content_type(file_path)),
                'original_filename': saved_metadata.get('original-filename', ''),
                'metadata': saved_metadata
            }
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