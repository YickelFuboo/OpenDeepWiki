# OpenDeepWiki API 文档

## 概述

OpenDeepWiki 提供完整的 RESTful API，支持 AI 驱动的代码知识库管理。所有 API 都遵循 REST 设计原则，使用 JSON 格式进行数据交换。

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON

## 认证

### 获取访问令牌

```http
POST /v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 1800,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 刷新令牌

```http
POST /v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 用户管理

### 获取用户列表

```http
GET /v1/users/
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `size`: 每页数量 (默认: 10)
- `search`: 搜索关键词

### 创建用户

```http
POST /v1/users/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "New User",
  "role": "user"
}
```

### 更新用户

```http
PUT /v1/users/{user_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "full_name": "Updated Name",
  "email": "updated@example.com"
}
```

## 仓库管理

### 获取仓库列表

```http
GET /v1/repositories/
Authorization: Bearer {access_token}
```

**查询参数**:
- `page`: 页码
- `size`: 每页数量
- `status`: 仓库状态 (pending, processing, completed, failed)
- `search`: 搜索关键词

### 创建仓库

```http
POST /v1/repositories/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "my-repo",
  "url": "https://github.com/user/repo.git",
  "description": "My repository description",
  "branch": "main",
  "is_public": true
}
```

### 更新仓库

```http
PUT /v1/repositories/{warehouse_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "updated-repo-name",
  "description": "Updated description"
}
```

### 删除仓库

```http
DELETE /v1/repositories/{warehouse_id}
Authorization: Bearer {access_token}
```

## 文档管理

### 获取文档列表

```http
GET /v1/documents/
Authorization: Bearer {access_token}
```

**查询参数**:
- `warehouse_id`: 仓库ID
- `page`: 页码
- `size`: 每页数量

### 获取文档目录

```http
GET /v1/document-catalogs/{warehouse_id}
Authorization: Bearer {access_token}
```

### 获取文档内容

```http
GET /v1/documents/content/{catalog_id}
Authorization: Bearer {access_token}
```

## 角色权限管理

### 获取角色列表

```http
GET /v1/roles/
Authorization: Bearer {access_token}
```

### 创建角色

```http
POST /v1/roles/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "developer",
  "description": "Developer role",
  "permissions": ["read", "write"]
}
```

### 设置角色权限

```http
POST /v1/permissions/role-permissions
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "role_id": "role-uuid",
  "permissions": ["read", "write", "delete"]
}
```

### 分配用户角色

```http
POST /v1/permissions/user-roles
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "user_id": "user-uuid",
  "role_id": "role-uuid"
}
```

## AI 功能

### 代码分析

```http
POST /v1/ai/analyze
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "warehouse_id": "warehouse-uuid",
  "file_path": "src/main.py",
  "analysis_type": "complexity"
}
```

### 生成文档

```http
POST /v1/ai/generate-docs
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "warehouse_id": "warehouse-uuid",
  "doc_type": "api",
  "template": "default"
}
```

### AI 对话

```http
POST /v1/ai/chat
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": "Explain this code",
  "context": "code context",
  "model": "gpt-4"
}
```



## 应用配置管理 🆕

### 获取应用配置列表

```http
GET /v1/app-config/
Authorization: Bearer {access_token}
```

### 创建应用配置

```http
POST /v1/app-config/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "app_id": "my-app",
  "name": "My Application",
  "organization_name": "My Org",
  "repository_name": "my-repo",
  "description": "Application description",
  "prompt": "Custom prompt for the app",
  "introduction": "App introduction",
  "model": "gpt-4",
  "allowed_domains": ["example.com", "test.com"],
  "enable_domain_validation": true
}
```

### 更新应用配置

```http
PUT /v1/app-config/{app_id}
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Updated App Name",
  "description": "Updated description",
  "prompt": "Updated prompt"
}
```

### 域名验证

```http
POST /v1/app-config/validatedomain
Content-Type: application/json

{
  "domain": "example.com",
  "app_id": "my-app"
}
```

### 获取公开应用配置

```http
GET /v1/app-config/public/{app_id}
```

**注意**: 此接口不需要认证，用于第三方脚本集成。

## 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 响应数据
  },
  "message": "操作成功"
}
```

### 分页响应

```json
{
  "success": true,
  "data": {
    "items": [
      // 数据项列表
    ],
    "total": 100,
    "page": 1,
    "size": 10,
    "pages": 10
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "验证失败",
    "details": {
      "field": "错误字段",
      "message": "具体错误信息"
    }
  }
}
```

## 状态码

- `200 OK`: 请求成功
- `201 Created`: 创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 数据验证失败
- `500 Internal Server Error`: 服务器内部错误

## 错误代码

- `AUTHENTICATION_FAILED`: 认证失败
- `PERMISSION_DENIED`: 权限不足
- `RESOURCE_NOT_FOUND`: 资源不存在
- `VALIDATION_ERROR`: 数据验证错误
- `WAREHOUSE_PROCESSING`: 仓库处理中
- `TASK_FAILED`: 任务执行失败

## 限流

API 请求限制：
- 认证接口: 每分钟 5 次
- 其他接口: 每分钟 100 次
- 文件上传: 每分钟 10 次

## WebSocket 支持

### 实时任务状态

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Task status:', data);
};
```

## SDK 支持

### Python SDK

```python
from opendeepwiki import OpenDeepWiki

client = OpenDeepWiki(
    base_url="http://localhost:8000",
    api_key="your-api-key"
)

# 获取仓库列表
repositories = client.repositories.list()

# 创建仓库
repo = client.repositories.create({
    "name": "my-repo",
    "url": "https://github.com/user/repo.git"
})
```

### JavaScript SDK

```javascript
import { OpenDeepWiki } from '@opendeepwiki/sdk';

const client = new OpenDeepWiki({
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key'
});

// 获取仓库列表
const repositories = await client.repositories.list();

// 创建仓库
const repo = await client.repositories.create({
  name: 'my-repo',
  url: 'https://github.com/user/repo.git'
});
```

## 更新日志

### v1.0.0 (2024-07-29)
- ✅ 基础认证和用户管理
- ✅ 仓库管理功能
- ✅ 文档管理功能
- ✅ 角色权限管理
- ✅ AI 功能集成

- ✅ 应用配置管理 🆕
- ✅ 响应服务功能 🆕

---

**注意**: 本文档会随着 API 的更新而持续更新。建议定期查看最新版本。 