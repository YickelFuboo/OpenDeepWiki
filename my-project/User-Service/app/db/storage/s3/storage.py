"""
S3存储实现
"""

import logging
import uuid
import json
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..base import StorageInterface

logger = logging.getLogger(__name__)

class S3Storage(StorageInterface):
    """S3存储实现"""
    
    def __init__(self, bucket_name: str, region: str, access_key_id: str, 
                 secret_access_key: str, endpoint_url: str, use_ssl: bool = True):
        """
        初始化S3存储
        
        Args:
            bucket_name: S3存储桶名称
            region: 存储区域
            access_key_id: 访问密钥ID
            secret_access_key: 秘密访问密钥
            endpoint_url: S3兼容服务的端点URL（必需）
            use_ssl: 是否使用SSL连接
        """
        if not endpoint_url:
            raise ValueError("S3存储必须指定endpoint_url")
            
        self.bucket_name = bucket_name
        self.region = region
        
        # 初始化S3客户端
        client_kwargs = {
            'region_name': region,
            'aws_access_key_id': access_key_id,
            'aws_secret_access_key': secret_access_key,
            'endpoint_url': endpoint_url,
            'use_ssl': use_ssl
        }
        
        self.client = boto3.client('s3', **client_kwargs)
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保存储桶存在"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3存储桶已存在: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # 存储桶不存在，创建它
                self.client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
                logger.info(f"创建S3存储桶: {self.bucket_name}")
            else:
                raise
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str) -> str:
        """上传文件到S3"""
        try:
            # 生成唯一文件ID
            file_id = str(uuid.uuid4())
            object_key = f"{file_id}/{file_name}"
            
            # 准备元数据
            s3_metadata = {
                'Content-Type': content_type,
                'original-filename': file_name
            }
            
            # 上传文件到S3
            self.client.upload_fileobj(
                file_data,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    'Metadata': s3_metadata,
                    'ContentType': content_type
                }
            )
            
            logger.info(f"文件上传成功: {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str) -> Optional[BinaryIO]:
        """从S3下载文件"""
        try:
            # 构造对象键（假设格式为 file_id/filename）
            # 这里需要根据实际存储路径调整
            object_key = f"{file_id}/"
            
            # 获取文件
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return response['Body']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"文件不存在: {file_id}")
                return None
            else:
                logger.error(f"下载文件失败: {e}")
                raise
    
    def delete_file(self, file_id: str) -> bool:
        """删除S3文件"""
        try:
            # 构造对象键
            object_key = f"{file_id}/"
            
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info(f"文件删除成功: {file_id}")
            return True
            
        except ClientError as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL"""
        try:
            # 构造对象键
            object_key = f"{file_id}/"
            
            # 生成预签名URL
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in or 3600  # 默认1小时
            )
            
            return url
            
        except Exception as e:
            logger.error(f"生成文件URL失败: {e}")
            return None
    
    def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        try:
            # 构造对象键
            object_key = f"{file_id}/"
            
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"检查文件存在性失败: {e}")
                return False
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            # 构造对象键
            object_key = f"{file_id}/"
            
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                logger.error(f"获取文件元数据失败: {e}")
                return None 