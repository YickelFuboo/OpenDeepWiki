# Pando 后端服务架构

## 📁 目录结构

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

## 🏗️ 架构设计原则

### 1. 分层架构
- **API层**：处理HTTP请求和响应
- **Service层**：实现业务逻辑
- **DataStore层**：数据访问抽象

### 2. 模块化设计
- 每个模块职责单一
- 模块间低耦合
- 支持独立开发和测试

### 3. 可扩展性
- 工厂模式支持多种数据库
- 插件化AI服务
- 配置驱动的行为控制

### 4. 异步任务管理
- 统一的任务框架
- 支持任务重试和监控
- 分布式任务处理

## 🔧 技术栈

- **Web框架**: FastAPI
- **数据库**: PostgreSQL (主), MySQL (可选)
- **任务队列**: Celery + Redis
- **AI服务**: OpenAI, Anthropic, 本地模型
- **存储**: 本地文件系统, S3 (未来)
- **监控**: 内置日志和指标

## 🚀 快速开始

1. 安装依赖
2. 配置环境变量
3. 启动服务
4. 访问API文档

详细说明请参考各模块的README文件。 