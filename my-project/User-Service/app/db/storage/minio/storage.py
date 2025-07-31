"""
MinIO存储实现
"""

import logging
import uuid
import json
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from minio import Minio
from minio.error import S3Error

from ..base import StorageInterface

logger = logging.getLogger(__name__)

class MinIOStorage(StorageInterface):
    """MinIO存储实现"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = True):
        """
        初始化MinIO存储
        
        Args:
            endpoint: MinIO服务端点
            access_key: 访问密钥
            secret_key: 秘密密钥
            secure: 是否使用HTTPS
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        
        # 初始化MinIO客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        logger.info(f"MinIO存储初始化完成: {self.endpoint}")
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"创建MinIO存储桶: {bucket_name}")
            else:
                logger.debug(f"MinIO存储桶已存在: {bucket_name}")
        except Exception as e:
            logger.error(f"MinIO存储桶操作失败: {e}")
            raise
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, 
                   bucket_name: str = "default", metadata: Optional[Dict[str, Any]] = None) -> str:
        """上传文件到MinIO"""
        try:
            # 确保bucket存在
            self._ensure_bucket_exists(bucket_name)
            
            # 生成唯一文件ID作为对象键
            file_id = str(uuid.uuid4())
            object_key = file_id  # 直接使用file_id作为对象键
            
            # 准备metadata，包含原始文件名
            minio_metadata = {
                'original-filename': file_name
            }
            if metadata:
                minio_metadata.update(metadata)
            
            # 上传文件到MinIO
            self.client.put_object(
                bucket_name,
                object_key,
                file_data,
                length=-1,  # 自动计算长度
                content_type=content_type,
                metadata=minio_metadata
            )
            
            logger.info(f"文件上传成功: {bucket_name}/{object_key}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str, bucket_name: str = "default") -> Optional[BinaryIO]:
        """从MinIO下载文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 获取文件
            response = self.client.get_object(bucket_name, object_key)
            return response
            
        except Exception as e:
            logger.error(f"下载文件失败: {e}")
            return None
    
    def delete_file(self, file_id: str, bucket_name: str = "default") -> bool:
        """删除MinIO文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            self.client.remove_object(bucket_name, object_key)
            logger.info(f"文件删除成功: {bucket_name}/{file_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, bucket_name: str = "default", expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 生成预签名URL
            url = self.client.presigned_get_object(
                bucket_name,
                object_key,
                expires=timedelta(seconds=expires_in or 3600)  # 默认1小时
            )
            return url
            
        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return None
    
    def file_exists(self, file_id: str, bucket_name: str = "default") -> bool:
        """检查文件是否存在"""
        try:
            # 构造对象键
            object_key = file_id
            
            self.client.stat_object(bucket_name, object_key)
            return True
        except Exception:
            return False
    
    def get_file_metadata(self, file_id: str, bucket_name: str = "default") -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            # 构造对象键
            object_key = file_id
            
            stat = self.client.stat_object(bucket_name, object_key)
            
            return {
                'file_id': file_id,
                'bucket_name': bucket_name,
                'file_size': stat.size,
                'last_modified': stat.last_modified,
                'content_type': stat.content_type,
                'original_filename': stat.metadata.get('original-filename', ''),
                'metadata': stat.metadata
            }
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None 