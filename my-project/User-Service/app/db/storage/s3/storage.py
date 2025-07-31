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
    
    def __init__(self, endpoint_url: str = None, region: str = None, access_key_id: str = None,
                 secret_access_key: str = None, use_ssl: bool = True):
        """
        初始化S3存储
        
        Args:
            bucket_name: 存储桶名称（可选，使用时动态指定）
            region: 区域
            access_key_id: 访问密钥ID
            secret_access_key: 秘密访问密钥
            endpoint_url: 端点URL
            use_ssl: 是否使用SSL
        """
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.endpoint_url = endpoint_url
        self.use_ssl = use_ssl
        
        # 初始化S3客户端
        client_kwargs = {
            'region_name': region,
            'aws_access_key_id': access_key_id,
            'aws_secret_access_key': secret_access_key,
            'endpoint_url': endpoint_url,
            'use_ssl': use_ssl
        }
        
        self.client = boto3.client('s3', **client_kwargs)
        
        logger.info(f"S3存储初始化完成: {endpoint_url}")
    
    def _ensure_bucket_exists(self, bucket_name: str):
        """确保存储桶存在"""
        try:
            self.client.head_bucket(Bucket=bucket_name)
            logger.debug(f"S3存储桶已存在: {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # 存储桶不存在，创建它
                self.client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
                logger.info(f"创建S3存储桶: {bucket_name}")
            else:
                raise
    
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, 
                   bucket_name: str = "default", metadata: Optional[Dict[str, Any]] = None) -> str:
        """上传文件到S3"""
        try:
            # 确保bucket存在
            self._ensure_bucket_exists(bucket_name)
            
            # 生成唯一文件ID作为对象键
            file_id = str(uuid.uuid4())
            object_key = file_id  # 直接使用file_id作为对象键
            
            # 准备metadata，包含原始文件名
            s3_metadata = {
                'original-filename': file_name
            }
            if metadata:
                s3_metadata.update(metadata)

            # 上传文件到S3
            self.client.upload_fileobj(
                file_data,
                bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': s3_metadata
                }
            )
            
            logger.info(f"文件上传成功: {bucket_name}/{object_key}")
            return file_id
            
        except Exception as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def download_file(self, file_id: str, bucket_name: str = "default") -> Optional[BinaryIO]:
        """从S3下载文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 获取文件
            response = self.client.get_object(
                Bucket=bucket_name,
                Key=object_key
            )
            
            return response['Body']
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"文件不存在: {bucket_name}/{file_id}")
                return None
            else:
                logger.error(f"下载文件失败: {e}")
                raise
    
    def delete_file(self, file_id: str, bucket_name: str = "default") -> bool:
        """删除S3文件"""
        try:
            # 构造对象键
            object_key = file_id
            
            self.client.delete_object(
                Bucket=bucket_name,
                Key=object_key
            )
            
            logger.info(f"文件删除成功: {bucket_name}/{file_id}")
            return True
            
        except ClientError as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    def get_file_url(self, file_id: str, bucket_name: str = "default", expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL"""
        try:
            # 构造对象键
            object_key = file_id
            
            # 生成预签名URL
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expires_in or 3600  # 默认1小时
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
            
            self.client.head_object(Bucket=bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"检查文件存在失败: {e}")
                return False
    
    def get_file_metadata(self, file_id: str, bucket_name: str = "default") -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        try:
            # 构造对象键
            object_key = file_id
            
            response = self.client.head_object(Bucket=bucket_name, Key=object_key)
            
            # 获取自定义metadata
            custom_metadata = response.get('Metadata', {})
            
            return {
                'file_id': file_id,
                'bucket_name': bucket_name,
                'file_size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response['ContentType'],
                'original_filename': custom_metadata.get('original-filename', ''),
                'metadata': custom_metadata
            }
        except Exception as e:
            logger.error(f"获取文件元数据失败: {e}")
            return None 