# 文档目录模块

## 概述

文档目录模块负责管理仓库的文档目录结构，提供文档目录的树形构建、内容获取、目录管理和进度跟踪等功能。该模块是文档知识库系统的核心组件之一。

## 功能特性

### 🎯 核心功能

- **文档目录树构建**: 根据仓库结构构建完整的文档目录树
- **文档内容获取**: 根据路径获取具体的文档内容
- **目录管理**: 支持目录的增删改查操作
- **进度跟踪**: 实时跟踪文档目录的处理进度
- **状态管理**: 管理目录的完成状态和删除状态
- **搜索功能**: 支持目录内容的全文搜索
- **数据导出**: 支持目录数据的JSON和CSV格式导出

### 🔍 目录结构管理

- **树形结构**: 支持多级目录的树形结构
- **排序管理**: 支持目录的排序和层级管理
- **父子关系**: 维护目录的父子关系
- **URL映射**: 目录与URL路径的映射关系

### 📊 进度和统计

- **处理进度**: 实时显示文档目录的处理进度
- **统计信息**: 提供目录的类型和状态统计
- **完成状态**: 跟踪每个目录的完成状态

## 目录结构

```
document_catalog/
├── README.md                           # 模块文档
├── services/
│   └── document_catalog_service.py    # 文档目录服务
├── api/
│   └── document_catalog_routes.py     # 文档目录API路由
└── tests/
    └── test_document_catalog.py       # 文档目录测试
```

## API接口

### 1. 获取文档目录列表

**接口**: `GET /v1/document-catalogs/catalogs`

**描述**: 根据仓库信息获取文档目录列表

**请求参数**:
- `organization_name` (string, 必需): 组织名称
- `name` (string, 必需): 仓库名称
- `branch` (string, 可选): 分支名称

**响应示例**:
```json
{
  "data": {
    "items": [
      {
        "label": "根目录",
        "url": "/",
        "description": "根目录描述",
        "key": "catalog-1",
        "last_update": "2023-01-01T00:00:00Z",
        "disabled": false,
        "children": [
          {
            "label": "子目录",
            "url": "/sub",
            "description": "子目录描述",
            "key": "catalog-2",
            "last_update": "2023-01-01T00:00:00Z",
            "disabled": true
          }
        ]
      }
    ],
    "last_update": "2023-01-01T00:00:00Z",
    "description": "文档描述",
    "progress": 50,
    "git": "https://github.com/test-org/test-repo.git",
    "branches": ["main", "develop"],
    "warehouse_id": "warehouse-123",
    "like_count": 10,
    "status": "completed",
    "comment_count": 5
  }
}
```

### 2. 获取文档内容

**接口**: `GET /v1/document-catalogs/document`

**描述**: 根据路径获取文档内容

**请求参数**:
- `owner` (string, 必需): 组织名称
- `name` (string, 必需): 仓库名称
- `path` (string, 必需): 文档路径
- `branch` (string, 可选): 分支名称

**响应示例**:
```json
{
  "data": {
    "content": "# 文档标题\n\n这是文档内容...",
    "title": "文档标题",
    "file_sources": [
      {
        "id": "source-123",
        "name": "README.md",
        "address": "/README.md",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      }
    ],
    "address": "https://github.com/test-org/test-repo",
    "branch": "main",
    "last_update": "2023-01-01T00:00:00Z",
    "document_catalog_id": "catalog-123"
  }
}
```

### 3. 更新目录信息

**接口**: `PUT /v1/document-catalogs/catalog/update`

**描述**: 更新目录的名称和提示词

**请求体**:
```json
{
  "id": "catalog-123",
  "name": "新目录名称",
  "prompt": "新的提示词"
}
```

**响应示例**:
```json
{
  "message": "目录更新成功"
}
```

### 4. 更新文档内容

**接口**: `PUT /v1/document-catalogs/content/update`

**描述**: 更新文档的内容

**请求体**:
```json
{
  "id": "catalog-123",
  "content": "# 新的文档内容\n\n更新后的内容..."
}
```

**响应示例**:
```json
{
  "message": "文档内容更新成功"
}
```

### 5. 获取目录信息

**接口**: `GET /v1/document-catalogs/catalog/{catalog_id}`

**描述**: 根据ID获取目录详细信息

**响应示例**:
```json
{
  "data": {
    "id": "catalog-123",
    "warehouse_id": "warehouse-123",
    "parent_id": null,
    "title": "目录标题",
    "name": "目录名称",
    "url": "/path",
    "description": "目录描述",
    "prompt": "提示词",
    "order_index": 0,
    "is_completed": true,
    "is_deleted": false,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

### 6. 根据URL获取目录

**接口**: `GET /v1/document-catalogs/catalog/url/{warehouse_id}`

**描述**: 根据URL获取目录信息

**请求参数**:
- `url` (string, 必需): 目录URL

**响应示例**: 同上面的目录信息响应

### 7. 创建目录

**接口**: `POST /v1/document-catalogs/catalog/create`

**描述**: 创建新的目录

**请求体**:
```json
{
  "id": "new-catalog",
  "warehouse_id": "warehouse-123",
  "parent_id": "parent-catalog",
  "title": "新目录",
  "name": "新目录",
  "url": "/new",
  "description": "新目录描述",
  "prompt": "新目录提示",
  "order_index": 0,
  "is_completed": false
}
```

**响应示例**:
```json
{
  "message": "目录创建成功",
  "data": {
    "id": "new-catalog",
    "warehouse_id": "warehouse-123",
    "parent_id": "parent-catalog",
    "title": "新目录",
    "name": "新目录",
    "url": "/new",
    "description": "新目录描述",
    "prompt": "新目录提示",
    "order_index": 0,
    "is_completed": false,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

### 8. 更新目录状态

**接口**: `PUT /v1/document-catalogs/catalog/{catalog_id}/status`

**描述**: 更新目录的完成状态

**请求参数**:
- `is_completed` (boolean, 必需): 是否完成

**响应示例**:
```json
{
  "message": "目录状态更新成功"
}
```

### 9. 删除目录

**接口**: `DELETE /v1/document-catalogs/catalog/{catalog_id}`

**描述**: 删除目录（软删除）

**响应示例**:
```json
{
  "message": "目录删除成功"
}
```

### 10. 获取目录进度

**接口**: `GET /v1/document-catalogs/progress/{warehouse_id}`

**描述**: 获取目录处理进度

**响应示例**:
```json
{
  "data": {
    "total": 100,
    "completed": 75,
    "pending": 25,
    "progress": 75
  }
}
```

### 11. 获取目录统计

**接口**: `GET /v1/document-catalogs/statistics/{warehouse_id}`

**描述**: 获取目录统计信息

**响应示例**:
```json
{
  "data": {
    "total_catalogs": 100,
    "type_statistics": {
      "directory": 30,
      "file": 70
    },
    "status_statistics": {
      "completed": 75,
      "pending": 25
    },
    "last_updated": "2023-01-01T00:00:00Z"
  }
}
```

### 12. 获取文档目录树

**接口**: `GET /v1/document-catalogs/tree/{warehouse_id}`

**描述**: 获取完整的文档目录树

**响应示例**:
```json
{
  "data": {
    "items": [...],
    "last_update": "2023-01-01T00:00:00Z",
    "description": "文档描述",
    "progress": 75,
    "git": "https://github.com/test-org/test-repo.git",
    "branches": ["main", "develop"],
    "warehouse_id": "warehouse-123",
    "like_count": 10,
    "status": "completed",
    "comment_count": 5
  }
}
```

### 13. 搜索目录

**接口**: `GET /v1/document-catalogs/search`

**描述**: 搜索目录内容

**请求参数**:
- `warehouse_id` (string, 必需): 仓库ID
- `keyword` (string, 必需): 搜索关键词

**响应示例**:
```json
{
  "data": {
    "keyword": "API",
    "total": 5,
    "results": [
      {
        "id": "catalog-123",
        "name": "API文档",
        "title": "API文档",
        "description": "API接口文档",
        "url": "/api",
        "is_completed": true,
        "created_at": "2023-01-01T00:00:00Z"
      }
    ]
  }
}
```

### 14. 导出目录数据

**接口**: `GET /v1/document-catalogs/export/{warehouse_id}`

**描述**: 导出目录数据

**请求参数**:
- `format` (string, 可选): 导出格式 (json, csv)，默认为json

**响应示例**:
```json
{
  "message": "目录导出成功",
  "data": {
    "format": "json",
    "content": [...],
    "filename": "catalogs_warehouse-123.json"
  }
}
```

## 数据模型

### DocumentCatalog (文档目录)

```python
class DocumentCatalog(Base, TimestampMixin):
    """文档目录模型"""
    __tablename__ = "document_catalogs"
    
    id = Column(String(50), primary_key=True)
    warehouse_id = Column(String(50), nullable=False)
    parent_id = Column(String(50))
    title = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text)
    prompt = Column(Text)
    type = Column(Enum(DocumentType), default=DocumentType.DIRECTORY)
    order_index = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_time = Column(DateTime)
```

### DocumentFileItem (文档文件项)

```python
class DocumentFileItem(Base, TimestampMixin):
    """文档文件项模型"""
    __tablename__ = "document_file_items"
    
    id = Column(String(50), primary_key=True)
    document_catalog_id = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    file_path = Column(String(500))
    file_size = Column(Integer)
    mime_type = Column(String(100))
```

### DocumentFileItemSource (文档文件源)

```python
class DocumentFileItemSource(Base, TimestampMixin):
    """文档文件源模型"""
    __tablename__ = "document_file_item_sources"
    
    id = Column(String(50), primary_key=True)
    document_file_item_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
```

## 使用示例

### 前端集成

```typescript
// 获取文档目录
const getDocumentCatalogs = async (org: string, repo: string, branch?: string) => {
  const params = new URLSearchParams({
    organization_name: org,
    name: repo
  });
  if (branch) params.append('branch', branch);
  
  const response = await fetch(`/v1/document-catalogs/catalogs?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data;
};

// 获取文档内容
const getDocumentContent = async (owner: string, name: string, path: string, branch?: string) => {
  const params = new URLSearchParams({
    owner,
    name,
    path
  });
  if (branch) params.append('branch', branch);
  
  const response = await fetch(`/v1/document-catalogs/document?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data;
};

// 更新目录信息
const updateCatalog = async (catalogId: string, name: string, prompt: string) => {
  const response = await fetch('/v1/document-catalogs/catalog/update', {
    method: 'PUT',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      id: catalogId,
      name,
      prompt
    })
  });
  return response.json();
};

// 获取目录进度
const getCatalogProgress = async (warehouseId: string) => {
  const response = await fetch(`/v1/document-catalogs/progress/${warehouseId}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data;
};
```

### 目录树渲染

```typescript
// React组件示例
const DocumentTree = ({ catalogs }) => {
  const renderTreeNode = (node) => {
    return (
      <TreeNode key={node.key} title={node.label}>
        {node.children && node.children.map(renderTreeNode)}
      </TreeNode>
    );
  };

  return (
    <Tree>
      {catalogs.map(renderTreeNode)}
    </Tree>
  );
};
```

## 配置说明

### 环境变量

文档目录模块不需要特殊的环境变量配置，但依赖于以下模块：

- 数据库连接配置
- 仓库管理模块
- 文档管理模块

### 数据库依赖

文档目录模块依赖以下数据表：

- `document_catalogs` - 文档目录表
- `document_file_items` - 文档文件项表
- `document_file_item_sources` - 文档文件源表
- `warehouses` - 仓库表
- `documents` - 文档表

## 测试

### 运行测试

```bash
# 运行文档目录模块测试
pytest tests/test_document_catalog.py -v

# 运行所有测试
pytest tests/ -v

# 生成测试覆盖率报告
pytest tests/test_document_catalog.py --cov=services.document_catalog_service --cov-report=html
```

### 测试覆盖

测试覆盖以下功能：

- ✅ 文档目录获取
- ✅ 文档内容获取
- ✅ 目录信息更新
- ✅ 文档内容更新
- ✅ 目录树构建
- ✅ 目录状态管理
- ✅ 进度跟踪
- ✅ 统计信息

## 注意事项

### 性能考虑

1. **目录缓存**: 建议在前端缓存目录树结构，减少API调用
2. **分页加载**: 对于大型目录树，考虑分页加载
3. **数据库索引**: 确保在常用查询字段上建立索引

### 安全考虑

1. **权限验证**: 所有目录访问都需要验证用户权限
2. **路径验证**: 检查用户对特定路径的访问权限
3. **内容过滤**: 对文档内容进行安全过滤

### 扩展性

1. **动态目录**: 支持从Git仓库动态加载目录结构
2. **自定义目录**: 允许用户自定义目录结构
3. **多格式支持**: 支持多种文档格式的目录

## 故障排除

### 常见问题

1. **目录不显示**
   - 检查仓库状态是否为已完成
   - 验证目录是否被软删除
   - 确认用户权限

2. **文档内容获取失败**
   - 检查目录是否存在
   - 验证文件项是否关联
   - 确认路径映射正确

3. **进度不更新**
   - 检查目录完成状态
   - 验证统计计算逻辑
   - 确认数据库事务

### 调试方法

1. **启用日志**: 查看文档目录服务的详细日志
2. **检查权限**: 使用权限检查API验证用户权限
3. **测试目录**: 使用测试用例验证目录功能

## 扩展

### 添加新功能

1. 在 `DocumentCatalogService` 中添加新方法
2. 在API路由中添加新的端点
3. 更新数据模型（如需要）
4. 添加相应的测试用例

### 自定义目录逻辑

1. 继承 `DocumentCatalogService` 类
2. 重写相关方法
3. 注册自定义服务
4. 更新API路由

---

**注意**: 文档目录模块是文档知识库系统的核心组件，请确保正确配置数据库和权限。 