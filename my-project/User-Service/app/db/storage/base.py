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
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """上传文件"""
        pass
    
    @abstractmethod
    def download_file(self, file_id: str) -> Optional[BinaryIO]:
        """下载文件"""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    def get_file_url(self, file_id: str, expires_in: Optional[int] = None) -> Optional[str]:
        """获取文件访问URL"""
        pass
    
    @abstractmethod
    def file_exists(self, file_id: str) -> bool:
        """检查文件是否存在"""
        pass
    
    @abstractmethod
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """获取文件元数据"""
        pass 