# KoalaWiki Python Backend

这是KoalaWiki项目的Python后端服务，使用FastAPI和Uvicorn构建。

## 功能特性

- **用户管理**: 用户注册、登录、权限管理
- **仓库管理**: Git仓库集成和管理
- **知识仓库**: 知识库创建和管理
- **文档管理**: 文档的创建、编辑、查看
- **统计分析**: 用户行为和数据统计
- **AI智能分析**: Semantic Kernel集成，代码分析，文档生成
- **提示词管理**: 动态提示词加载和执行
- **文件分析**: 文件内容分析、目录结构分析
- **后台任务**: 自动化任务处理

## 技术栈

- **FastAPI**: Web框架
- **Uvicorn**: ASGI服务器
- **SQLAlchemy**: ORM数据库操作
- **Pydantic**: 数据验证
- **JWT**: 身份认证
- **Loguru**: 日志记录
- **Semantic Kernel**: AI框架
- **OpenAI/Anthropic**: AI模型服务
- **Python 3.8+**: 编程语言

## 安装和运行

### 1. 克隆项目

```bash
git clone <repository-url>
cd 转换后项目
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，配置必要的环境变量：

- 数据库连接
- JWT密钥
- OpenAI API密钥
- GitHub/Gitee API密钥

### 5. 运行应用

```bash
python main.py
```

或者使用uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API文档

启动应用后，可以访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
转换后项目/
├── main.py                 # 应用入口
├── requirements.txt        # 依赖包
├── env.example           # 环境变量示例
├── README.md             # 项目说明
└── src/
    ├── core/             # 核心模块
    │   ├── config.py     # 配置管理
    │   ├── database.py   # 数据库配置
    │   ├── auth.py       # 认证模块
    │   ├── cache.py      # 缓存模块
    │   └── middleware.py # 中间件
    ├── api/              # API路由
    │   ├── __init__.py
    │   ├── auth.py       # 认证API
    │   ├── user.py       # 用户API
    │   ├── repository.py # 仓库API
    │   ├── warehouse.py  # 知识仓库API
    │   └── statistics.py # 统计API
    ├── services/         # 业务服务
    │   ├── __init__.py
    │   ├── user_service.py
    │   ├── auth_service.py
    │   ├── repository_service.py
    │   ├── warehouse_service.py
    │   ├── statistics_service.py
    │   ├── document_service.py
    │   └── background_services.py
    ├── models/           # 数据模型
    │   ├── __init__.py
    │   ├── user.py
    │   ├── repository.py
    │   ├── warehouse.py
    │   ├── document.py
    │   ├── role.py
    │   └── statistics.py
    └── dto/              # 数据传输对象
        ├── __init__.py
        ├── user_dto.py
        ├── auth_dto.py
        ├── repository_dto.py
        ├── warehouse_dto.py
        └── statistics_dto.py
```

## 主要功能模块

### 认证模块
- JWT令牌认证
- 用户登录/注册
- 权限控制

### 用户管理
- 用户CRUD操作
- 角色权限管理
- 用户资料管理

### 仓库管理
- Git仓库集成
- 仓库状态管理
- 仓库处理任务

### 知识仓库
- 知识库创建
- 文档管理
- 内容索引

### 统计分析
- 页面访问统计
- API调用统计
- 用户活动统计

### 后台任务
- 统计数据处理
- 仓库同步任务
- 数据清理任务

## 开发指南

### 添加新的API端点

1. 在 `src/api/` 目录下创建新的路由文件
2. 在 `src/services/` 目录下创建对应的服务
3. 在 `src/dto/` 目录下创建数据传输对象
4. 在 `src/models/` 目录下创建数据模型（如需要）

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 初始化迁移
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

### 测试

运行测试：

```bash
pytest
```

## 部署

### Docker部署

创建Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t koalawiki-backend .
docker run -p 8000:8000 koalawiki-backend
```

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进项目。 