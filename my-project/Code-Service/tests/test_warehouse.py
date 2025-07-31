import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from warehouse.services.warehouse_service import WarehouseService
from schemas.warehouse import CreateRepositoryDto, UpdateRepositoryDto
from models.warehouse import Warehouse, WarehouseStatus, WarehouseType
from models.user import User
from models.role import UserInRole, WarehouseInRole

class TestWarehouseService:
    """仓库服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def warehouse_service(self, mock_db):
        """创建仓库服务实例"""
        return WarehouseService(mock_db)
    
    @pytest.fixture
    def sample_warehouse(self):
        """示例仓库数据"""
        return Warehouse(
            id="test-warehouse-id",
            name="test-repo",
            organization_name="test-org",
            address="https://github.com/test-org/test-repo.git",
            description="Test repository",
            type=WarehouseType.GIT,
            status=WarehouseStatus.COMPLETED,
            branch="main",
            creator_id="test-user-id",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
    
    def test_check_warehouse_access_admin(self, warehouse_service):
        """测试管理员访问权限"""
        result = warehouse_service.check_warehouse_access(
            warehouse_id="test-id",
            current_user_id="user-id",
            is_admin=True
        )
        assert result == True
    
    def test_check_warehouse_access_public(self, warehouse_service, mock_db):
        """测试公共仓库访问权限"""
        # 模拟没有权限分配的仓库（公共仓库）
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = warehouse_service.check_warehouse_access(
            warehouse_id="test-id",
            current_user_id="user-id",
            is_admin=False
        )
        assert result == True
    
    def test_check_warehouse_access_unauthorized(self, warehouse_service, mock_db):
        """测试未授权访问"""
        # 模拟有权限分配但用户无权限
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = warehouse_service.check_warehouse_access(
            warehouse_id="test-id",
            current_user_id="user-id",
            is_admin=False
        )
        assert result == False
    
    @patch('warehouse.services.warehouse_service.process_warehouse_task')
    def test_create_warehouse_success(self, mock_task, warehouse_service, mock_db):
        """测试成功创建仓库"""
        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        create_dto = CreateRepositoryDto(
            organization="test-org",
            repository_name="test-repo",
            address="https://github.com/test-org/test-repo.git",
            branch="main"
        )
        
        result = warehouse_service.create_warehouse(
            create_dto=create_dto,
            current_user_id="test-user-id"
        )
        
        assert result.id is not None
        assert result.name == "test-repo"
        assert result.organization_name == "test-org"
        mock_task.delay.assert_called_once()
    
    def test_create_warehouse_already_exists(self, warehouse_service, mock_db, sample_warehouse):
        """测试创建已存在的仓库"""
        # 模拟仓库已存在
        sample_warehouse.status = WarehouseStatus.COMPLETED
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        create_dto = CreateRepositoryDto(
            organization="test-org",
            repository_name="test-repo",
            address="https://github.com/test-org/test-repo.git",
            branch="main"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            warehouse_service.create_warehouse(
                create_dto=create_dto,
                current_user_id="test-user-id"
            )
        
        assert exc_info.value.status_code == 400
        assert "该名称渠道已存在且处于完成状态" in str(exc_info.value.detail)
    
    def test_update_warehouse_success(self, warehouse_service, mock_db, sample_warehouse):
        """测试成功更新仓库"""
        # 模拟权限检查
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        update_dto = UpdateRepositoryDto(
            description="Updated description",
            is_recommended=True
        )
        
        result = warehouse_service.update_warehouse(
            warehouse_id="test-warehouse-id",
            update_dto=update_dto,
            current_user_id="test-user-id",
            is_admin=True
        )
        
        assert result.description == "Updated description"
        assert result.is_recommended == True
    
    def test_update_warehouse_not_found(self, warehouse_service, mock_db):
        """测试更新不存在的仓库"""
        # 模拟权限检查
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # 模拟仓库不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        update_dto = UpdateRepositoryDto(description="Updated description")
        
        with pytest.raises(HTTPException) as exc_info:
            warehouse_service.update_warehouse(
                warehouse_id="non-existent-id",
                update_dto=update_dto,
                current_user_id="test-user-id",
                is_admin=True
            )
        
        assert exc_info.value.status_code == 404
        assert "仓库不存在" in str(exc_info.value.detail)
    
    @patch('warehouse.services.warehouse_service.reset_warehouse_task')
    def test_reset_warehouse_success(self, mock_task, warehouse_service, mock_db, sample_warehouse):
        """测试成功重置仓库"""
        # 模拟权限检查
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        result = warehouse_service.reset_warehouse(
            warehouse_id="test-warehouse-id",
            current_user_id="test-user-id",
            is_admin=True
        )
        
        assert result == True
        mock_task.delay.assert_called_once_with("test-warehouse-id")
    
    def test_delete_warehouse_success(self, warehouse_service, mock_db, sample_warehouse):
        """测试成功删除仓库"""
        # 模拟权限检查
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        result = warehouse_service.delete_warehouse(
            warehouse_id="test-warehouse-id",
            current_user_id="test-user-id",
            is_admin=True
        )
        
        assert result == True
    
    def test_get_last_warehouse_success(self, warehouse_service, mock_db, sample_warehouse):
        """测试成功获取最后仓库"""
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        result = warehouse_service.get_last_warehouse(
            address="https://github.com/test-org/test-repo.git"
        )
        
        assert result["name"] == "test-repo"
        assert result["address"] == "https://github.com/test-org/test-repo.git"
    
    def test_get_last_warehouse_not_found(self, warehouse_service, mock_db):
        """测试获取不存在的最后仓库"""
        # 模拟仓库不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            warehouse_service.get_last_warehouse(
                address="https://github.com/test-org/non-existent.git"
            )
        
        assert exc_info.value.status_code == 404
        assert "仓库不存在" in str(exc_info.value.detail) 