# Pando 项目

AI驱动的代码知识库系统，基于Vue 3 + FastAPI构建。

## 🚀 快速开始

### 方式一：使用Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd my-project

# 一键启动所有服务
./run.sh start

# 查看服务状态
./run.sh logs

# 停止服务
./run.sh stop
```

### 方式二：本地开发

#### 启动后端服务

```bash
cd backend
chmod +x run.sh
./run.sh
```

#### 启动前端服务

```bash
cd frontend
chmod +x run.sh
./run.sh
```

## 📁 项目结构

```
my-project/
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/                # 应用代码
│   ├── alembic/            # 数据库迁移
│   ├── requirements.txt    # Python依赖
│   ├── Dockerfile         # Docker配置
│   └── run.sh             # 启动脚本
├── frontend/               # 前端服务 (Vue 3)
│   ├── src/               # 源代码
│   ├── package.json       # Node.js依赖
│   ├── Dockerfile         # Docker配置
│   └── run.sh             # 启动脚本
├── nginx/                  # Nginx配置
│   ├── nginx.conf         # 主配置
│   └── conf.d/            # 站点配置
├── database/               # 数据库相关
│   └── init/              # 初始化脚本
├── docker-compose.yml      # Docker Compose配置
└── run.sh                  # 项目启动脚本
```

## 🔧 服务说明

### 核心服务

- **Frontend**: Vue 3 + Element Plus (端口: 3000)
- **Backend**: FastAPI + SQLAlchemy (端口: 8000)
- **Database**: PostgreSQL 15 (端口: 5432)
- **Cache**: Redis 7 (端口: 6379)
- **Proxy**: Nginx (端口: 80/443)

### 可选服务

- **Celery Worker**: 异步任务处理
- **Celery Beat**: 定时任务调度

## 🌐 访问地址

启动成功后，可以通过以下地址访问：

- **前端应用**: http://localhost
- **后端API**: http://localhost/api
- **API文档**: http://localhost/api/docs
- **数据库**: localhost:5432
- **Redis**: localhost:6379

## ⚙️ 环境配置

### 环境变量

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
POSTGRES_DB=opendeepwiki
POSTGRES_USER=opendeepwiki
POSTGRES_PASSWORD=opendeepwiki123

# Redis配置
REDIS_URL=redis://redis:6379

# API密钥（请替换为真实的API密钥）
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🛠️ 开发指南

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn main:app --reload
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 📋 可用命令

### 项目级命令

```bash
./run.sh start      # 启动所有服务
./run.sh stop       # 停止所有服务
./run.sh restart    # 重启所有服务
./run.sh logs       # 查看服务日志
./run.sh clean      # 清理所有服务
./run.sh build      # 构建Docker镜像
./run.sh help       # 显示帮助信息
```

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建
docker-compose build
```

## 🔍 故障排除

### 常见问题

1. **端口冲突**
   - 检查端口是否被占用：`netstat -tulpn | grep :80`
   - 修改 `docker-compose.yml` 中的端口映射

2. **数据库连接失败**
   - 检查数据库服务是否启动：`docker-compose ps`
   - 查看数据库日志：`docker-compose logs postgres`

3. **前端无法访问后端API**
   - 检查后端服务状态：`docker-compose logs backend`
   - 确认API地址配置正确

4. **权限问题**
   - 确保脚本有执行权限：`chmod +x run.sh`

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

## 📚 技术栈

### 后端
- **FastAPI**: 现代Python Web框架
- **SQLAlchemy**: ORM数据库操作
- **Alembic**: 数据库迁移
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话存储
- **Celery**: 异步任务处理

### 前端
- **Vue 3**: 渐进式JavaScript框架
- **TypeScript**: 类型安全的JavaScript
- **Element Plus**: Vue 3 UI组件库
- **Vite**: 现代构建工具
- **Pinia**: 状态管理
- **Vue Router**: 路由管理

### 部署
- **Docker**: 容器化部署
- **Docker Compose**: 多服务编排
- **Nginx**: 反向代理和静态文件服务

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目主页: [GitHub Repository]
- 问题反馈: [Issues]
- 邮箱: [your-email@example.com]

---

**OpenDeepWiki Team** - 让代码知识管理更简单 