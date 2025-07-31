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
from ...database.models import UserFileRecord

logger = logging.getLogger(__name__)

class MinIOStorage(StorageInterface):
    """MinIO存储实现"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, 
                 bucket_name: str, secure: bool = True, db: Session = None):
        """
        初始化MinIO存储
        
        Args:
            endpoint: MinIO服务端点
            access_key: 访问密钥
            secret_key: 秘密密钥
            bucket_name: 存储桶名称
            secure: 是否使用HTTPS
            db: 数据库会话
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self.db = db
        
        # 初始化MinIO客户端
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建MinIO存储桶: {self.bucket_name}")
        except Exception as e:
            logger.error(f"确保存储桶存在失败: {e}")
            raise
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """上传文件到MinIO"""
        try:
            # 生成唯一文件ID
            file_id = str(uuid.uuid4())
            object_name = f"{file_id}/{file_name}"
            
            # 上传文件到MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=-1,  # 自动计算长度
                content_type=content_type
            )
            
            # 保存文件记录到数据库
            user_id = metadata.get('user_id') if metadata else None
            file_type = metadata.get('file_type', 'avatar') if metadata else 'avatar'
            
            file_record = UserFileRecord(
                id=file_id,
                user_id=user_id,
                file_name=file_name,
                original_name=file_name,
                content_type=content_type,
                file_size=str(file_data.seek(0, 2)),  # 获取文件大小
                storage_type="minio",
                storage_path=object_name,
                file_type=file_type,
                metadata=json.dumps(metadata) if metadata else None
            )
            
            if self.db:
                self.db.add(file_record)
                self.db.commit()
                self.db.refresh(file_record)
            
            logger.info(f"文件上传成功: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str) -> Optional[BinaryIO]:
        """从MinIO下载文件"""
        try:
            # 从数据库获取文件记录
            if self.db:
                file_record = self.db.query(UserFileRecord).filter(
                    UserFileRecord.id == file_id,
                    UserFileRecord.is_active == True
                ).first()
                
                if not file_record:
                    return None
                
                object_name = file_record.storage_path
            else:
                # 如果没有数据库，使用默认路径
                object_name = f"{file_id}/file"
            
            # 从MinIO下载文件
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            return response
            
        except S3Error as e:
            logger.error(f"文件下载失败: {e}")
            return None
        except Exception as e:
            logger.error(f"文件下载失败: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """从MinIO删除文件"""
        try:
            # 从数据库获取文件记录
            if self.db:
                file_record = self.db.query(UserFileRecord).filter(
                    UserFileRecord.id == file_id
                ).first()
                
                if not file_record:
                    return False
                
                object_name = file_record.storage_path
                
                # 标记为删除
                file_record.is_active = False
                self.db.commit()
            else:
                object_name = f"{file_id}/file"
            
            # 从MinIO删除文件
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            logger.info(f"文件删除成功: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL"""
        try:
            # 从数据库获取文件记录
            if self.db:
                file_record = self.db.query(UserFileRecord).filter(
                    UserFileRecord.id == file_id,
                    UserFileRecord.is_active == True
                ).first()
                
                if not file_record:
                    return None
                
                object_name = file_record.storage_path
            else:
                object_name = f"{file_id}/file"
            
            # 生成预签名URL
            if expires_in is None:
                expires_in = 3600  # 默认1小时
            
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires_in)
            )
            
            return url
            
        except Exception as e:
            logger.error(f"获取文件URL失败: {e}")
            return None
    
    def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        try:
            if self.db:
                file_record = self.db.query(UserFileRecord).filter(
                    UserFileRecord.id == file_id,
                    UserFileRecord.is_active == True
                ).first()
                
                if not file_record:
                    return False
                
                object_name = file_record.storage_path
            else:
                object_name = f"{file_id}/file"
            
            # 检查MinIO中是否存在
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            
            return True
            
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"检查文件存在失败: {e}")
            return False
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            if self.db:
                file_record = self.db.query(UserFileRecord).filter(
                    UserFileRecord.id == file_id,
                    UserFileRecord.is_active == True
                ).first()
                
                if not file_record:
                    return None
                
                metadata = {
                    "id": file_record.id,
                    "file_name": file_record.file_name,
                    "original_name": file_record.original_name,
                    "content_type": file_record.content_type,
                    "file_size": file_record.file_size,
                    "storage_type": file_record.storage_type,
                    "storage_path": file_record.storage_path,
                    "created_at": file_record.created_at.isoformat() if file_record.created_at else None,
                    "updated_at": file_record.updated_at.isoformat() if file_record.updated_at else None
                }
                
                if file_record.metadata:
                    metadata.update(json.loads(file_record.metadata))
                
                return metadata
            
            return None
            
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None 