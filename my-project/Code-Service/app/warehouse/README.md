# 仓库管理模块

## 概述

仓库管理模块是OpenDeepWiki项目的核心组件之一，负责处理Git仓库的克隆、分析、文档生成和权限管理。

## 功能特性

### 1. 仓库管理
- **仓库创建**: 支持Git仓库的添加和配置
- **仓库更新**: 修改仓库信息和设置
- **仓库删除**: 安全删除仓库及相关资源
- **状态管理**: 跟踪仓库处理状态（待处理、处理中、完成、失败）

### 2. 权限控制
- **访问权限**: 基于角色的仓库访问控制
- **管理权限**: 区分读取、写入、删除权限
- **公共仓库**: 支持无权限分配的公共仓库

### 3. 后台处理
- **异步处理**: 使用Celery进行后台任务处理
- **仓库克隆**: 自动克隆Git仓库到本地
- **结构分析**: 分析仓库文件结构和依赖关系
- **文档生成**: 自动生成项目文档和知识图谱

## 目录结构

```
warehouse/
├── __init__.py                 # 模块初始化
├── README.md                   # 本文档
├── api/                        # API路由
│   ├── __init__.py
│   └── warehouse_routes.py     # 仓库API路由
├── services/                   # 业务逻辑服务
│   ├── __init__.py
│   ├── warehouse_service.py    # 仓库服务
│   └── warehouse_processor.py  # 仓库处理器
└── tasks/                      # 后台任务
    ├── __init__.py
    └── warehouse_tasks.py      # Celery任务
```

## API接口

### 仓库管理接口

#### 获取仓库列表
```http
GET /api/v1/warehouses/
```

**查询参数:**
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 20)
- `keyword`: 搜索关键词

**响应示例:**
```json
{
  "items": [
    {
      "id": "warehouse-id",
      "name": "repo-name",
      "organization_name": "org-name",
      "address": "https://github.com/org/repo.git",
      "description": "Repository description",
      "status": "completed",
      "type": "git",
      "branch": "main",
      "is_recommended": false,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 创建仓库
```http
POST /api/v1/warehouses/
```

**请求体:**
```json
{
  "organization": "org-name",
  "repository_name": "repo-name",
  "address": "https://github.com/org/repo.git",
  "branch": "main",
  "git_user_name": "username",
  "git_password": "password",
  "email": "user@example.com"
}
```

#### 更新仓库
```http
PUT /api/v1/warehouses/{warehouse_id}
```

**请求体:**
```json
{
  "description": "Updated description",
  "is_recommended": true,
  "prompt": "Custom prompt"
}
```

#### 删除仓库
```http
DELETE /api/v1/warehouses/{warehouse_id}
```

#### 重置仓库
```http
POST /api/v1/warehouses/{warehouse_id}/reset
```

### 权限管理接口

#### 分配角色权限
```http
POST /api/v1/warehouses/{warehouse_id}/roles
```

**请求体:**
```json
{
  "role_id": "role-id",
  "is_read": true,
  "is_write": false,
  "is_delete": false
}
```

#### 更新角色权限
```http
PUT /api/v1/warehouses/{warehouse_id}/roles/{role_id}
```

#### 删除角色权限
```http
DELETE /api/v1/warehouses/{warehouse_id}/roles/{role_id}
```

## 后台任务

### 仓库处理任务

仓库创建后会自动提交后台处理任务，包括：

1. **仓库克隆**: 克隆Git仓库到本地
2. **结构分析**: 分析仓库文件结构
3. **文档生成**: 生成项目文档
4. **知识图谱**: 生成项目知识图谱

### 任务状态

- `PENDING`: 待处理
- `PROCESSING`: 处理中
- `COMPLETED`: 处理完成
- `FAILED`: 处理失败

### 定时任务

- **仓库处理**: 每5分钟检查并处理待处理的仓库
- **清理任务**: 每小时清理失败的仓库

## 配置

### 环境变量

```env
# Git仓库存储路径
GIT_REPOSITORY_PATH=/path/to/repositories

# Redis配置（用于Celery）
REDIS_URL=redis://localhost:6379/0

# 仓库处理配置
ENABLE_WAREHOUSE_COMMIT=true
```

### Celery配置

```python
# Celery配置
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# 定时任务配置
CELERY_BEAT_SCHEDULE = {
    'process-pending-warehouses': {
        'task': 'warehouse.tasks.warehouse_tasks.schedule_warehouse_processing',
        'schedule': 300.0,  # 每5分钟
    },
    'cleanup-failed-warehouses': {
        'task': 'warehouse.tasks.warehouse_tasks.cleanup_failed_warehouses_task',
        'schedule': 3600.0,  # 每小时
    },
}
```

## 使用示例

### 创建仓库

```python
from warehouse.services.warehouse_service import WarehouseService
from schemas.warehouse import CreateRepositoryDto

# 创建仓库服务
warehouse_service = WarehouseService(db)

# 创建仓库DTO
create_dto = CreateRepositoryDto(
    organization="microsoft",
    repository_name="vscode",
    address="https://github.com/microsoft/vscode.git",
    branch="main"
)

# 创建仓库
warehouse_dto = warehouse_service.create_warehouse(
    create_dto=create_dto,
    current_user_id="user-id"
)
```

### 处理仓库

```python
from warehouse.services.warehouse_processor import WarehouseProcessor

# 创建仓库处理器
processor = WarehouseProcessor(db)

# 处理仓库
result = await processor.process_warehouse("warehouse-id")
```

### 提交后台任务

```python
from warehouse.tasks.warehouse_tasks import process_warehouse_task

# 提交处理任务
task = process_warehouse_task.delay("warehouse-id")
```

## 测试

运行仓库模块测试：

```bash
# 运行所有测试
pytest tests/test_warehouse.py

# 运行特定测试
pytest tests/test_warehouse.py::TestWarehouseService::test_create_warehouse_success
```

## 注意事项

1. **权限检查**: 所有仓库操作都会进行权限检查
2. **异步处理**: 仓库处理是异步的，不会阻塞API响应
3. **错误处理**: 处理失败时会自动更新仓库状态
4. **资源清理**: 定期清理失败的仓库和临时文件
5. **并发控制**: 使用Redis锁控制并发处理

## 扩展

### 添加新的仓库类型

1. 在 `WarehouseType` 枚举中添加新类型
2. 在 `WarehouseProcessor` 中添加相应的处理逻辑
3. 更新API接口以支持新类型

### 自定义处理流程

1. 继承 `WarehouseProcessor` 类
2. 重写相应的处理方法
3. 在服务中注册自定义处理器

## 故障排除

### 常见问题

1. **仓库克隆失败**
   - 检查网络连接
   - 验证Git凭据
   - 确认仓库地址正确

2. **权限错误**
   - 检查用户角色分配
   - 验证仓库权限设置
   - 确认用户登录状态

3. **处理超时**
   - 检查Celery工作进程状态
   - 验证Redis连接
   - 查看任务日志

### 日志查看

```bash
# 查看Celery工作进程日志
celery -A warehouse.tasks.warehouse_tasks worker --loglevel=info

# 查看定时任务日志
celery -A warehouse.tasks.warehouse_tasks beat --loglevel=info
``` 