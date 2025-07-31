"""
存储功能测试
"""

import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import Mock, patch

from app.db.storage.factory import get_storage
from app.db.storage.local.storage import LocalStorage


class TestLocalStorage:
    """本地存储测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalStorage(self.temp_dir)
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_upload_file(self):
        """测试文件上传"""
        # 准备测试数据
        file_data = BytesIO(b"test file content")
        file_name = "test.txt"
        content_type = "text/plain"
        
        # 执行上传
        file_id = self.storage.upload_file(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            bucket_name="test"
        )
        
        # 验证结果
        assert file_id is not None
        assert self.storage.file_exists(file_id, bucket_name="test")
        
        # 验证元数据
        metadata = self.storage.get_file_metadata(file_id, bucket_name="test")
        assert metadata is not None
        assert metadata['original_filename'] == file_name
        assert metadata['content_type'] == content_type
    
    def test_download_file(self):
        """测试文件下载"""
        # 上传文件
        file_data = BytesIO(b"test content")
        file_id = self.storage.upload_file(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
            bucket_name="test"
        )
        
        # 下载文件
        downloaded_data = self.storage.download_file(file_id, bucket_name="test")
        
        # 验证结果
        assert downloaded_data is not None
        assert downloaded_data.read() == b"test content"
    
    def test_delete_file(self):
        """测试文件删除"""
        # 上传文件
        file_data = BytesIO(b"test content")
        file_id = self.storage.upload_file(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
            bucket_name="test"
        )
        
        # 验证文件存在
        assert self.storage.file_exists(file_id, bucket_name="test")
        
        # 删除文件
        success = self.storage.delete_file(file_id, bucket_name="test")
        
        # 验证结果
        assert success
        assert not self.storage.file_exists(file_id, bucket_name="test")
    
    def test_get_file_url(self):
        """测试获取文件URL"""
        # 上传文件
        file_data = BytesIO(b"test content")
        file_id = self.storage.upload_file(
            file_data=file_data,
            file_name="test.txt",
            content_type="text/plain",
            bucket_name="test"
        )
        
        # 获取URL
        url = self.storage.get_file_url(file_id, bucket_name="test")
        
        # 验证结果
        assert url is not None
        assert "test" in url
        assert file_id in url


class TestStorageFactory:
    """存储工厂测试"""
    
    @patch('app.db.storage.factory.get_settings')
    def test_get_storage_local(self, mock_get_settings):
        """测试获取本地存储"""
        # 模拟配置
        mock_settings = Mock()
        mock_settings.STORAGE_TYPE = "local"
        mock_settings.LOCAL_UPLOAD_DIR = "/tmp/test"
        mock_get_settings.return_value = mock_settings
        
        # 获取存储实例
        storage = get_storage()
        
        # 验证结果
        assert storage is not None
        assert hasattr(storage, 'upload_file')
        assert hasattr(storage, 'download_file')
    
    @patch('app.db.storage.factory.get_settings')
    def test_get_storage_s3(self, mock_get_settings):
        """测试获取S3存储"""
        # 模拟配置
        mock_settings = Mock()
        mock_settings.STORAGE_TYPE = "s3"
        mock_settings.S3_ENDPOINT_URL = "http://localhost:9000"
        mock_settings.S3_ACCESS_KEY_ID = "test"
        mock_settings.S3_SECRET_ACCESS_KEY = "test"
        mock_settings.S3_REGION = "us-east-1"
        mock_get_settings.return_value = mock_settings
        
        # 获取存储实例
        storage = get_storage()
        
        # 验证结果
        assert storage is not None
        assert hasattr(storage, 'upload_file')
        assert hasattr(storage, 'download_file') 