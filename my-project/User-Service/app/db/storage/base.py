"""
存储抽象基类
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime

class StorageInterface(ABC):
    """存储接口抽象基类"""
    
    @abstractmethod
    def upload_file(self, file_data: BinaryIO, file_name: str, content_type: str, 
                   bucket_name: str = "default", metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        上传文件
        
        Args:
            file_data: 文件数据
            file_name: 文件名
            content_type: 内容类型
            bucket_name: 存储桶名称
            metadata: 元数据
        
        Returns:
            str: 文件ID
        """
        pass
    
    @abstractmethod
    def download_file(self, file_id: str, bucket_name: str = "default") -> Optional[BinaryIO]:
        """
        下载文件
        
        Args:
            file_id: 文件ID
            bucket_name: 存储桶名称
        
        Returns:
            Optional[BinaryIO]: 文件数据
        """
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str, bucket_name: str = "default") -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            bucket_name: 存储桶名称
        
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    def get_file_url(self, file_id: str, bucket_name: str = "default", expires_in: Optional[int] = None) -> Optional[str]:
        """
        获取文件访问URL
        
        Args:
            file_id: 文件ID
            bucket_name: 存储桶名称
            expires_in: 过期时间（秒）
        
        Returns:
            Optional[str]: 文件URL
        """
        pass
    
    @abstractmethod
    def file_exists(self, file_id: str, bucket_name: str = "default") -> bool:
        """
        检查文件是否存在
        
        Args:
            file_id: 文件ID
            bucket_name: 存储桶名称
        
        Returns:
            bool: 文件是否存在
        """
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_id: str, bucket_name: str = "default") -> Optional[Dict[str, Any]]:
        """
        获取文件元数据
        
        Args:
            file_id: 文件ID
            bucket_name: 存储桶名称
        
        Returns:
            Optional[Dict[str, Any]]: 文件元数据
        """
        pass 