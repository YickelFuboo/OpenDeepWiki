import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from services.document_catalog_service import DocumentCatalogService
from models.document import DocumentCatalog, DocumentFileItem, DocumentFileItemSource
from models.warehouse import Warehouse, WarehouseStatus
from models.document import Document
from schemas.document import UpdateCatalogRequest, UpdateDocumentContentRequest

class TestDocumentCatalogService:
    """文档目录服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def catalog_service(self, mock_db):
        """创建文档目录服务实例"""
        return DocumentCatalogService(mock_db)

    @pytest.fixture
    def sample_warehouse(self):
        """示例仓库数据"""
        return Warehouse(
            id="warehouse-123",
            name="test-repo",
            organization_name="test-org",
            address="https://github.com/test-org/test-repo.git",
            branch="main",
            status=WarehouseStatus.COMPLETED,
            type="git",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_document(self):
        """示例文档数据"""
        return Document(
            id="document-123",
            warehouse_id="warehouse-123",
            title="测试文档",
            description="测试文档描述",
            status="completed",
            last_update=datetime.utcnow(),
            like_count=10,
            comment_count=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_catalogs(self):
        """示例目录数据"""
        return [
            DocumentCatalog(
                id="catalog-1",
                warehouse_id="warehouse-123",
                parent_id=None,
                title="根目录",
                name="根目录",
                url="/",
                description="根目录描述",
                prompt="根目录提示",
                order_index=0,
                is_completed=True,
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            DocumentCatalog(
                id="catalog-2",
                warehouse_id="warehouse-123",
                parent_id="catalog-1",
                title="子目录",
                name="子目录",
                url="/sub",
                description="子目录描述",
                prompt="子目录提示",
                order_index=1,
                is_completed=False,
                is_deleted=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]

    def test_get_document_catalogs_by_warehouse_success(self, catalog_service, mock_db, sample_warehouse, sample_document, sample_catalogs):
        """测试成功获取文档目录"""
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        # 模拟文档查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_document
        
        # 模拟目录查询
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = sample_catalogs
        
        # 模拟分支查询
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [("main",)]

        result = catalog_service.get_document_catalogs_by_warehouse("test-org", "test-repo", "main")

        assert "items" in result
        assert "last_update" in result
        assert "description" in result
        assert "progress" in result
        assert "git" in result
        assert "branches" in result
        assert len(result["items"]) == 1  # 根目录

    def test_get_document_catalogs_by_warehouse_warehouse_not_found(self, catalog_service, mock_db):
        """测试获取不存在的仓库文档目录"""
        # 模拟仓库不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            catalog_service.get_document_catalogs_by_warehouse("test-org", "non-existent", "main")

        assert exc_info.value.status_code == 404
        assert "仓库不存在" in str(exc_info.value.detail)

    def test_get_document_by_path_success(self, catalog_service, mock_db, sample_warehouse):
        """测试成功获取文档内容"""
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        # 模拟目录查询
        catalog = DocumentCatalog(
            id="catalog-123",
            warehouse_id="warehouse-123",
            url="/test-path",
            name="测试目录",
            is_deleted=False
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog
        
        # 模拟文件项查询
        file_item = DocumentFileItem(
            id="file-123",
            document_catalog_id="catalog-123",
            title="测试文档",
            content="# 测试内容",
            created_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = file_item
        
        # 模拟文件源查询
        file_sources = [
            DocumentFileItemSource(
                id="source-123",
                document_file_item_id="file-123",
                name="test.md",
                address="/test.md",
                created_at=datetime.utcnow()
            )
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = file_sources

        result = catalog_service.get_document_by_path("test-org", "test-repo", "/test-path", "main")

        assert "content" in result
        assert "title" in result
        assert "file_sources" in result
        assert result["content"] == "# 测试内容"
        assert result["title"] == "测试文档"

    def test_get_document_by_path_warehouse_not_found(self, catalog_service, mock_db):
        """测试获取不存在的仓库文档"""
        # 模拟仓库不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            catalog_service.get_document_by_path("test-org", "non-existent", "/test-path", "main")

        assert exc_info.value.status_code == 404
        assert "仓库不存在" in str(exc_info.value.detail)

    def test_get_document_by_path_catalog_not_found(self, catalog_service, mock_db, sample_warehouse):
        """测试获取不存在的目录文档"""
        # 模拟仓库查询
        mock_db.query.return_value.filter.return_value.first.return_value = sample_warehouse
        
        # 模拟目录不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            catalog_service.get_document_by_path("test-org", "test-repo", "/non-existent", "main")

        assert exc_info.value.status_code == 404
        assert "文档目录不存在" in str(exc_info.value.detail)

    def test_update_catalog_success(self, catalog_service, mock_db):
        """测试成功更新目录"""
        # 模拟目录查询
        catalog = DocumentCatalog(
            id="catalog-123",
            name="旧名称",
            prompt="旧提示",
            updated_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog

        request = UpdateCatalogRequest(
            id="catalog-123",
            name="新名称",
            prompt="新提示"
        )

        result = catalog_service.update_catalog(request)

        assert result == True

    def test_update_catalog_not_found(self, catalog_service, mock_db):
        """测试更新不存在的目录"""
        # 模拟目录不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        request = UpdateCatalogRequest(
            id="non-existent",
            name="新名称",
            prompt="新提示"
        )

        result = catalog_service.update_catalog(request)

        assert result == False

    def test_update_document_content_success(self, catalog_service, mock_db):
        """测试成功更新文档内容"""
        # 模拟文件项查询
        file_item = DocumentFileItem(
            id="file-123",
            document_catalog_id="catalog-123",
            content="旧内容",
            updated_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = file_item

        request = UpdateDocumentContentRequest(
            id="catalog-123",
            content="新内容"
        )

        result = catalog_service.update_document_content(request)

        assert result == True

    def test_update_document_content_not_found(self, catalog_service, mock_db):
        """测试更新不存在的文档内容"""
        # 模拟文件项不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        request = UpdateDocumentContentRequest(
            id="non-existent",
            content="新内容"
        )

        result = catalog_service.update_document_content(request)

        assert result == False

    def test_build_document_tree_success(self, catalog_service):
        """测试成功构建文档树"""
        catalogs = [
            DocumentCatalog(
                id="root",
                parent_id=None,
                name="根目录",
                url="/",
                description="根目录描述",
                order_index=0,
                is_completed=True,
                created_at=datetime.utcnow()
            ),
            DocumentCatalog(
                id="child",
                parent_id="root",
                name="子目录",
                url="/child",
                description="子目录描述",
                order_index=1,
                is_completed=False,
                created_at=datetime.utcnow()
            )
        ]

        result = catalog_service._build_document_tree(catalogs)

        assert len(result) == 1  # 根目录
        assert result[0]["label"] == "根目录"
        assert result[0]["key"] == "root"
        assert len(result[0]["children"]) == 1  # 子目录
        assert result[0]["children"][0]["label"] == "子目录"
        assert result[0]["children"][0]["key"] == "child"

    def test_get_children_success(self, catalog_service):
        """测试成功获取子目录"""
        catalogs = [
            DocumentCatalog(
                id="parent",
                parent_id=None,
                name="父目录",
                order_index=0,
                created_at=datetime.utcnow()
            ),
            DocumentCatalog(
                id="child1",
                parent_id="parent",
                name="子目录1",
                order_index=0,
                created_at=datetime.utcnow()
            ),
            DocumentCatalog(
                id="child2",
                parent_id="parent",
                name="子目录2",
                order_index=1,
                created_at=datetime.utcnow()
            )
        ]

        result = catalog_service._get_children("parent", catalogs)

        assert len(result) == 2
        assert result[0]["label"] == "子目录1"
        assert result[1]["label"] == "子目录2"

    def test_get_catalog_by_id_success(self, catalog_service, mock_db):
        """测试成功根据ID获取目录"""
        catalog = DocumentCatalog(
            id="catalog-123",
            name="测试目录",
            created_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog

        result = catalog_service.get_catalog_by_id("catalog-123")

        assert result is not None
        assert result.id == "catalog-123"
        assert result.name == "测试目录"

    def test_get_catalog_by_id_not_found(self, catalog_service, mock_db):
        """测试根据ID获取不存在的目录"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = catalog_service.get_catalog_by_id("non-existent")

        assert result is None

    def test_get_catalog_by_url_success(self, catalog_service, mock_db):
        """测试成功根据URL获取目录"""
        catalog = DocumentCatalog(
            id="catalog-123",
            warehouse_id="warehouse-123",
            url="/test-path",
            name="测试目录",
            is_deleted=False,
            created_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog

        result = catalog_service.get_catalog_by_url("warehouse-123", "/test-path")

        assert result is not None
        assert result.id == "catalog-123"
        assert result.url == "/test-path"

    def test_get_catalog_by_url_not_found(self, catalog_service, mock_db):
        """测试根据URL获取不存在的目录"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = catalog_service.get_catalog_by_url("warehouse-123", "/non-existent")

        assert result is None

    def test_create_catalog_success(self, catalog_service, mock_db):
        """测试成功创建目录"""
        catalog_data = {
            "id": "new-catalog",
            "warehouse_id": "warehouse-123",
            "title": "新目录",
            "name": "新目录",
            "url": "/new",
            "description": "新目录描述",
            "prompt": "新目录提示",
            "order_index": 0,
            "is_completed": False
        }

        result = catalog_service.create_catalog(catalog_data)

        assert result is not None
        assert result.id == "new-catalog"
        assert result.name == "新目录"
        assert result.url == "/new"

    def test_update_catalog_status_success(self, catalog_service, mock_db):
        """测试成功更新目录状态"""
        catalog = DocumentCatalog(
            id="catalog-123",
            is_completed=False,
            updated_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog

        result = catalog_service.update_catalog_status("catalog-123", True)

        assert result == True

    def test_update_catalog_status_not_found(self, catalog_service, mock_db):
        """测试更新不存在的目录状态"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = catalog_service.update_catalog_status("non-existent", True)

        assert result == False

    def test_delete_catalog_success(self, catalog_service, mock_db):
        """测试成功删除目录"""
        catalog = DocumentCatalog(
            id="catalog-123",
            is_deleted=False,
            updated_at=datetime.utcnow()
        )
        mock_db.query.return_value.filter.return_value.first.return_value = catalog

        result = catalog_service.delete_catalog("catalog-123")

        assert result == True

    def test_delete_catalog_not_found(self, catalog_service, mock_db):
        """测试删除不存在的目录"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = catalog_service.delete_catalog("non-existent")

        assert result == False

    def test_get_catalog_progress_success(self, catalog_service, mock_db):
        """测试成功获取目录进度"""
        catalogs = [
            DocumentCatalog(is_completed=True),
            DocumentCatalog(is_completed=False),
            DocumentCatalog(is_completed=True),
            DocumentCatalog(is_completed=False)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = catalogs

        result = catalog_service.get_catalog_progress("warehouse-123")

        assert result["total"] == 4
        assert result["completed"] == 2
        assert result["pending"] == 2
        assert result["progress"] == 50

    def test_get_catalog_statistics_success(self, catalog_service, mock_db):
        """测试成功获取目录统计"""
        catalogs = [
            DocumentCatalog(type="directory", is_completed=True),
            DocumentCatalog(type="file", is_completed=False),
            DocumentCatalog(type="directory", is_completed=True)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = catalogs

        result = catalog_service.get_catalog_statistics("warehouse-123")

        assert result["total_catalogs"] == 3
        assert "directory" in result["type_statistics"]
        assert "file" in result["type_statistics"]
        assert result["status_statistics"]["completed"] == 2
        assert result["status_statistics"]["pending"] == 1 