"""
存储工厂 - 支持多种存储类型
"""

import logging
from typing import Optional
from config.settings import get_settings
from .base import StorageInterface
from .s3.storage import S3Storage
from .minio.storage import MinIOStorage
from .local.storage import LocalStorage

logger = logging.getLogger(__name__)

# 全局存储实例
_storage_instance: Optional[StorageInterface] = None


def init_storage():
    """初始化存储实例"""
    global _storage_instance
    
    settings = get_settings()
    
    try:
        storage_type = settings.storage.storage_type
        
        if storage_type == "s3":
            if not settings.storage.s3.endpoint_url:
                raise ValueError("S3存储必须配置S3_ENDPOINT_URL")
            _storage_instance = S3Storage(
                bucket_name=settings.storage.s3.bucket_name,
                region=settings.storage.s3.region,
                access_key_id=settings.storage.s3.access_key_id,
                secret_access_key=settings.storage.s3.secret_access_key,
                endpoint_url=settings.storage.s3.endpoint_url,
                use_ssl=settings.storage.s3.use_ssl
            )
        elif storage_type == "minio":
            _storage_instance = MinIOStorage(
                endpoint=settings.storage.minio.endpoint,
                access_key=settings.storage.minio.access_key,
                secret_key=settings.storage.minio.secret_key,
                bucket_name=settings.storage.minio.bucket_name,
                secure=settings.storage.minio.secure
            )
        elif storage_type == "local":
            _storage_instance = LocalStorage(
                upload_dir=settings.storage.local.upload_dir
            )
        else:
            raise ValueError(f"不支持的存储类型: {storage_type}")
        
        logger.info(f"存储实例初始化成功: {storage_type}")
        
    except Exception as e:
        logger.error(f"初始化存储实例失败: {e}")
        raise


def get_storage() -> StorageInterface:
    """
    获取存储实例
    
    Returns:
        StorageInterface: 存储实例
    """
    global _storage_instance
    
    if _storage_instance is None:
        try:
            init_storage()
        except Exception as e:
            logger.error(f"存储初始化失败: {e}")
            raise RuntimeError("存储服务不可用")
    
    return _storage_instance


def close_storage():
    """关闭存储连接"""
    global _storage_instance
    if _storage_instance:
        try:
            # 如果存储实例有close方法，调用它
            if hasattr(_storage_instance, 'close'):
                _storage_instance.close()
            _storage_instance = None
            logger.info("存储连接已关闭")
        except Exception as e:
            logger.error(f"关闭存储连接失败: {e}") 