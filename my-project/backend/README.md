# OpenDeepWiki 后端项目

## 项目概述

这是 OpenDeepWiki 项目的 Python + FastAPI 后端实现，从原始的 .NET 项目转换而来。项目提供了完整的 AI 驱动代码知识库管理功能。

## 🏗️ 项目架构

### 技术栈

- **框架**: FastAPI + Uvicorn
- **数据库**: SQLAlchemy + Alembic (支持 PostgreSQL/SQLite)
- **认证**: JWT (python-jose)
- **密码**: bcrypt (passlib)
- **异步任务**: Celery + Redis
- **AI/ML**: Semantic Kernel (Python)
- **Git操作**: libgit2
- **文件处理**: aiofiles

### 目录结构

```
backend/
├── ai/                          # AI模块
│   ├── core/                    # AI核心组件
│   │   └── kernel_factory.py   # AI内核工厂
│   ├── functions/               # AI函数插件
│   │   ├── file_function.py    # 文件操作函数
│   │   ├── code_analyze_function.py  # 代码分析函数
│   │   └── rag_function.py     # RAG函数
│   └── services/               # AI服务
│       ├── ai_service.py       # AI主服务
│       ├── document_service.py # 文档生成服务
│       ├── minimap_service.py  # 知识图谱服务
│       └── overview_service.py # 项目概述服务
├── warehouse/                   # 仓库管理模块
│   ├── api/                    # 仓库API
│   │   └── warehouse_routes.py # 仓库路由
│   ├── services/               # 仓库服务
│   │   ├── warehouse_service.py    # 仓库服务
│   │   └── warehouse_processor.py  # 仓库处理器
│   └── tasks/                  # 后台任务
│       └── warehouse_tasks.py  # Celery任务
├── api/                        # API路由
│   └── v1/                     # API版本1
│       ├── auth.py             # 认证API
│       ├── users.py            # 用户API
│       ├── roles.py            # 角色API
│       ├── documents.py        # 文档API
│       ├── permissions.py      # 权限API
│       └── ai.py               # AI API
├── models/                     # 数据模型
│   ├── user.py                 # 用户模型
│   ├── role.py                 # 角色模型
│   ├── warehouse.py            # 仓库模型
│   └── document.py             # 文档模型
├── schemas/                    # Pydantic模型
│   ├── user.py                 # 用户模式
│   ├── role.py                 # 角色模式
│   ├── warehouse.py            # 仓库模式
│   ├── document.py             # 文档模式
│   └── common.py               # 通用模式
├── services/                   # 业务服务
│   ├── user_service.py         # 用户服务
│   ├── role_service.py         # 角色服务
│   ├── document_service.py     # 文档服务
│   └── permission_service.py   # 权限服务
├── utils/                      # 工具类
│   ├── auth.py                 # 认证工具
│   ├── password.py             # 密码工具
│   ├── git_utils.py            # Git工具
│   └── file_utils.py           # 文件工具
├── tests/                      # 测试
│   └── test_warehouse.py       # 仓库测试
├── main.py                     # 应用入口
├── config.py                   # 配置管理
├── database.py                 # 数据库配置
└── requirements.txt            # 依赖包
```

## 🔧 已完成的模块转换

### ✅ 1. 认证模块 (Authentication)
- **功能**: 用户登录、注册、JWT令牌管理
- **文件**: `api/v1/auth.py`, `services/user_service.py`, `utils/auth.py`
- **状态**: ✅ 完成

### ✅ 2. 用户管理模块 (User Management)
- **功能**: 用户CRUD、密码管理、头像上传
- **文件**: `api/v1/users.py`, `services/user_service.py`, `models/user.py`
- **状态**: ✅ 完成

### ✅ 3. 仓库管理模块 (Warehouse Management)
- **功能**: 仓库CRUD、权限控制、后台处理
- **文件**: `warehouse/`, `models/warehouse.py`, `schemas/warehouse.py`
- **状态**: ✅ 完成

### ✅ 4. AI辅助模块 (AI Assistant)
- **功能**: 代码分析、文档生成、知识图谱
- **文件**: `ai/`, `services/ai_service.py`
- **状态**: ✅ 完成

### ✅ 5. 文档管理模块 (Document Management)
- **功能**: 文档CRUD、目录管理、内容处理
- **文件**: `api/v1/documents.py`, `services/document_service.py`
- **状态**: ✅ 完成

### ✅ 6. 角色权限模块 (Role & Permission)
- **功能**: 角色管理、权限分配、权限检查
- **文件**: `api/v1/roles.py`, `api/v1/permissions.py`, `services/role_service.py`
- **状态**: ✅ 完成

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Redis (用于Celery)
- PostgreSQL (推荐) 或 SQLite

### 安装依赖

```bash
cd my-project/backend
pip install -r requirements.txt
```

### 环境配置

复制环境变量文件并配置：

```bash
cp env.example .env
```

编辑 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/opendeepwiki
# 或使用SQLite
# DATABASE_URL=sqlite:///./opendeepwiki.db

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
AZURE_OPENAI_API_KEY=your-azure-api-key

# Redis配置
REDIS_URL=redis://localhost:6379/0

# Git配置
GIT_REPOSITORY_PATH=/path/to/repositories
```

### 数据库迁移

```bash
# 初始化数据库
alembic upgrade head
```

### 启动服务

```bash
# 启动主服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery工作进程
celery -A warehouse.tasks.warehouse_tasks worker --loglevel=info

# 启动Celery定时任务
celery -A warehouse.tasks.warehouse_tasks beat --loglevel=info
```

## 📚 API文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

#### 认证相关
- `POST /v1/auth/login` - 用户登录
- `POST /v1/auth/register` - 用户注册
- `POST /v1/auth/refresh` - 刷新令牌

#### 用户管理
- `GET /v1/users/` - 获取用户列表
- `POST /v1/users/` - 创建用户
- `PUT /v1/users/{user_id}` - 更新用户
- `DELETE /v1/users/{user_id}` - 删除用户

#### 仓库管理
- `GET /v1/warehouses/` - 获取仓库列表
- `POST /v1/warehouses/` - 创建仓库
- `PUT /v1/warehouses/{warehouse_id}` - 更新仓库
- `DELETE /v1/warehouses/{warehouse_id}` - 删除仓库

#### 文档管理
- `GET /v1/documents/` - 获取文档列表
- `GET /v1/documents/catalogs/{warehouse_id}` - 获取文档目录
- `GET /v1/documents/content/{catalog_id}` - 获取文档内容

#### 角色权限
- `GET /v1/roles/` - 获取角色列表
- `POST /v1/roles/` - 创建角色
- `POST /v1/permissions/role-permissions` - 设置角色权限
- `POST /v1/permissions/user-roles` - 分配用户角色

#### AI功能
- `POST /v1/ai/analyze` - 代码分析
- `POST /v1/ai/generate-docs` - 生成文档
- `POST /v1/ai/chat` - AI对话

## 🔄 后台任务

### Celery任务

项目使用Celery处理后台任务：

1. **仓库处理任务**: 克隆、分析、生成文档
2. **定时任务**: 定期处理待处理仓库
3. **清理任务**: 清理失败的仓库

### 任务状态

- `PENDING`: 待处理
- `PROCESSING`: 处理中
- `COMPLETED`: 完成
- `FAILED`: 失败

## 🧪 测试

运行测试：

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_warehouse.py

# 运行测试并生成覆盖率报告
pytest --cov=.
```

## 📝 开发指南

### 添加新模块

1. 创建数据模型 (`models/`)
2. 创建Pydantic模式 (`schemas/`)
3. 创建业务服务 (`services/`)
4. 创建API路由 (`api/v1/`)
5. 添加测试 (`tests/`)

### 代码规范

- 使用 Black 进行代码格式化
- 使用 isort 进行导入排序
- 使用 flake8 进行代码检查

```bash
# 格式化代码
black .
isort .

# 代码检查
flake8 .
```

## 🚧 待完成模块

### ⏳ 菜单管理模块 (Menu Management)
- **功能**: 用户菜单构建、权限检查
- **状态**: ⏳ 待完成

### ⏳ 文档目录模块 (Document Catalog)
- **功能**: 目录树构建、文档内容获取
- **状态**: ⏳ 待完成

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如果您遇到问题或有建议，请：

1. 查看 [Issues](../../issues)
2. 创建新的 Issue
3. 联系开发团队

---

**注意**: 这是一个从 .NET 项目转换而来的 Python 实现，保持了原有的功能特性，同时利用了 Python 生态系统的优势。 