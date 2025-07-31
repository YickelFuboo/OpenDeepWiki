# Pando 架构迁移指南

## 📋 迁移概述

本指南将帮助您将现有的代码迁移到新的模块化架构中。

## 🏗️ 新架构结构

```
app/
├── API/                    # 接口相关
│   ├── schemes/           # 接口相关结构定义
│   ├── warehouse.py       # 仓库相关接口
│   ├── user.py           # 用户相关接口
│   └── document.py       # 文档相关接口
│
├── DataStore/             # 数据存储适配层
│   ├── DB/               # 数据库相关操作
│   │   ├── models/       # 数据库结构定义
│   │   ├── mysql.py      # MySQL操作
│   │   ├── postgresql.py # PostgreSQL操作
│   │   └── factory.py    # 数据库工厂模式
│   ├── RAG/              # RAG数据库（未来扩展）
│   ├── Graph/            # 图数据库（未来扩展）
│   └── S3/               # S3存储（未来扩展）
│
├── Service/               # 业务服务层
│   ├── user_mgmt/        # 用户管理服务
│   │   ├── auth.py       # 认证服务
│   │   ├── user.py       # 用户服务
│   │   └── role.py       # 角色服务
│   ├── repo_analysis/    # 代码仓库分析服务
│   │   ├── git_service.py    # Git操作
│   │   ├── file_service.py   # 文件操作
│   │   └── analysis_service.py # 仓库分析
│   └── ai_service/       # AI服务
│       ├── model_factory.py   # 模型工厂
│       ├── prompt_manager.py  # Prompt管理
│       └── ai_caller.py       # AI调用
│
├── Conf/                  # 配置文件解析
│   ├── settings.py       # 配置管理
│   └── env.py           # 环境变量
│
├── logger/               # 日志相关
│   ├── log_config.py    # 日志配置
│   └── log_utils.py     # 日志工具
│
├── integration/          # 三方集成
│   ├── external/        # 外部服务集成
│   └── webhook/         # Webhook服务
│
└── tasks/               # 异步任务管理
    ├── base.py          # 任务基类
    ├── warehouse_tasks.py # 仓库任务
    └── ai_tasks.py      # AI任务
```

## 🔄 迁移步骤

### 步骤1: 迁移数据库模型

**从**: `app/db/models/` 或 `app/models/`
**到**: `app/DataStore/DB/models/`

```bash
# 移动数据库模型
mv app/db/models/* app/DataStore/DB/models/
mv app/models/* app/DataStore/DB/models/
```

### 步骤2: 迁移API接口

**从**: `app/api/` 或 `app/routers/`
**到**: `app/API/`

```bash
# 移动API接口
mv app/api/* app/API/
mv app/routers/* app/API/
```

### 步骤3: 迁移业务服务

**从**: `app/warehouse/services/`, `app/auth/`, `app/ai/services/`
**到**: `app/Service/`

```bash
# 移动仓库服务
mv app/warehouse/services/* app/Service/repo_analysis/

# 移动认证服务
mv app/auth/* app/Service/user_mgmt/

# 移动AI服务
mv app/ai/services/* app/Service/ai_service/
```

### 步骤4: 迁移任务

**从**: `app/warehouse/tasks/`, `app/tasks/`
**到**: `app/tasks/`

```bash
# 移动任务文件
mv app/warehouse/tasks/* app/tasks/
mv app/tasks/* app/tasks/
```

### 步骤5: 迁移配置

**从**: `app/config/`
**到**: `app/Conf/`

```bash
# 移动配置文件
mv app/config/* app/Conf/
```

## 📝 代码更新

### 1. 更新导入路径

#### 数据库相关
```python
# 旧导入
from app.db.connection import get_db
from app.models.warehouse import Warehouse

# 新导入
from app.DataStore.DB.factory import get_database_session
from app.DataStore.DB.models.warehouse import Warehouse
```

#### 配置相关
```python
# 旧导入
from app.config.settings import get_settings

# 新导入
from app.Conf.settings import get_settings
```

#### 任务相关
```python
# 旧导入
from app.warehouse.tasks.warehouse_tasks import process_warehouse_task

# 新导入
from app.tasks.warehouse_tasks import process_warehouse_task
```

### 2. 更新服务调用

#### 数据库连接
```python
# 旧方式
db = next(get_db())

# 新方式
from app.DataStore.DB.factory import get_database_session
db = get_database_session()
```

#### AI模型调用
```python
# 旧方式
from app.ai.services.openai_service import OpenAIService
service = OpenAIService()

# 新方式
from app.Service.ai_service.model_factory import get_ai_model
model = get_ai_model("openai")
```

### 3. 更新配置文件

#### 环境变量
```bash
# .env 文件更新
DATABASE_TYPE=postgresql
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_DATABASE=pando

# AI配置
DEFAULT_AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Celery配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🧪 测试迁移

### 1. 单元测试
```bash
# 运行单元测试
python -m pytest tests/ -v
```

### 2. 集成测试
```bash
# 启动服务
python main.py

# 测试API接口
curl http://localhost:8000/docs
```

### 3. 功能测试
```bash
# 测试数据库连接
python -c "from app.DataStore.DB.factory import init_database; init_database('postgresql', {}); print('Database connected')"

# 测试AI模型
python -c "from app.Service.ai_service.model_factory import get_ai_model; model = get_ai_model(); print('AI model ready')"
```

## 🚨 注意事项

### 1. 依赖更新
确保安装了新的依赖：
```bash
pip install httpx anthropic
```

### 2. 环境变量
更新所有环境变量以匹配新的配置结构。

### 3. 数据库迁移
如果使用Alembic，需要更新迁移脚本中的导入路径。

### 4. 日志配置
更新日志配置以使用新的日志模块。

## 🔧 故障排除

### 常见问题

1. **导入错误**
   - 检查所有导入路径是否已更新
   - 确保新目录结构已创建

2. **数据库连接失败**
   - 检查数据库配置
   - 确保数据库服务正在运行

3. **AI模型初始化失败**
   - 检查API密钥配置
   - 确保网络连接正常

4. **任务执行失败**
   - 检查Celery配置
   - 确保Redis服务正在运行

## 📊 迁移检查清单

- [ ] 数据库模型已迁移
- [ ] API接口已迁移
- [ ] 业务服务已迁移
- [ ] 任务已迁移
- [ ] 配置已迁移
- [ ] 导入路径已更新
- [ ] 环境变量已更新
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 功能测试已通过

## 🎯 迁移完成

完成迁移后，您将拥有一个更加模块化、可扩展和可维护的代码架构！ 