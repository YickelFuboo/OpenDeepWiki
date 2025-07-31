# User-Service

用户管理微服务，负责用户注册、登录、权限管理等核心功能。

## 📁 目录结构

```
User-Service/
├── app/                    # 应用代码
│   ├── API/               # 接口相关
│   │   ├── schemes/       # 接口相关结构定义
│   │   ├── users.py       # 用户相关接口
│   │   ├── auth.py        # 认证相关接口
│   │   └── permissions.py # 权限相关接口
│   │
│   ├── DataStore/         # 数据存储适配层
│   │   └── DB/           # 数据库相关操作
│   │       ├── models/   # 数据库结构定义
│   │       ├── factory.py # 数据库工厂模式
│   │       └── connection.py # 数据库连接
│   │
│   ├── Service/           # 业务服务层
│   │   ├── user_mgmt/    # 用户管理服务
│   │   │   ├── user_service.py    # 用户服务
│   │   │   ├── profile_service.py # 用户资料服务
│   │   │   └── registration_service.py # 注册服务
│   │   ├── auth_mgmt/    # 认证管理服务
│   │   │   ├── auth_service.py    # 认证服务
│   │   │   ├── jwt_service.py     # JWT服务
│   │   │   └── session_service.py # 会话服务
│   │   └── permission_mgmt/ # 权限管理服务
│   │       ├── permission_service.py # 权限服务
│   │       ├── role_service.py      # 角色服务
│   │       └── menu_service.py      # 菜单服务
│   │
│   ├── Conf/              # 配置文件解析
│   │   ├── settings.py   # 配置管理
│   │   └── jwt.py        # JWT配置
│   │
│   └── logger/            # 日志相关
│       ├── log_config.py # 日志配置
│       └── log_utils.py  # 日志工具
│
├── tests/                # 测试代码
├── docs/                 # 文档
├── scripts/              # 脚本文件
├── requirements.txt      # Python依赖
└── Dockerfile           # Docker配置
```

## 🏗️ 架构设计

### 1. 微服务架构
- **独立部署**: 用户服务可以独立部署和扩展
- **服务发现**: 通过API网关进行服务发现
- **数据隔离**: 用户数据独立存储，提高安全性

### 2. 核心功能
- **用户管理**: 注册、登录、资料管理
- **认证授权**: JWT认证、会话管理
- **权限控制**: 角色管理、权限分配
- **安全防护**: 密码加密、防暴力破解

### 3. 技术栈
- **Web框架**: FastAPI
- **数据库**: PostgreSQL (主), MySQL (可选)
- **认证**: JWT
- **监控**: 内置日志和指标

## 🚀 快速开始

### 1. 环境准备
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# .env 文件
DATABASE_TYPE=postgresql
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=your_password
POSTGRESQL_DATABASE=user_service



JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

SERVICE_PORT=8001
SERVICE_HOST=0.0.0.0
```

### 3. 启动服务
```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8001
```

### 4. 访问服务
- **API文档**: http://localhost:8001/docs
- **健康检查**: http://localhost:8001/health

## 🔧 API接口

### 用户管理
- `POST /api/v1/users/register` - 用户注册
- `POST /api/v1/users/login` - 用户登录
- `GET /api/v1/users/profile` - 获取用户资料
- `PUT /api/v1/users/profile` - 更新用户资料
- `DELETE /api/v1/users/{user_id}` - 删除用户

### 认证管理
- `POST /api/v1/auth/refresh` - 刷新Token
- `POST /api/v1/auth/logout` - 用户登出
- `POST /api/v1/auth/verify` - 验证Token

### 权限管理
- `GET /api/v1/permissions` - 获取权限列表
- `GET /api/v1/roles` - 获取角色列表
- `POST /api/v1/roles` - 创建角色
- `PUT /api/v1/roles/{role_id}` - 更新角色
- `DELETE /api/v1/roles/{role_id}` - 删除角色

## 🔒 安全特性

### 1. 密码安全
- 使用bcrypt进行密码加密
- 密码强度验证
- 防暴力破解机制

### 2. JWT认证
- 访问令牌和刷新令牌分离
- 令牌自动过期
- 令牌黑名单机制

### 3. 权限控制
- 基于角色的访问控制(RBAC)
- 细粒度权限管理
- 动态权限验证

## 📊 监控和日志

### 1. 日志记录
- 用户操作日志
- 认证失败日志
- 系统错误日志

### 2. 性能监控
- API响应时间
- 数据库查询性能
- 用户操作统计

### 3. 健康检查
- 数据库连接状态
- 服务可用性

## 🔄 部署

### Docker部署
```bash
# 构建镜像
docker build -t user-service .

# 运行容器
docker run -d -p 8001:8001 --name user-service user-service
```

### 微服务部署
```bash
# 构建镜像
docker build -t user-service .

# 运行容器
docker run -d -p 8001:8001 --name user-service user-service

# 查看日志
docker logs -f user-service
```

## 🧪 测试

### 单元测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_user_service.py
```

### 集成测试
```bash
# 运行集成测试
python -m pytest tests/integration/
```

## 📚 文档

详细文档请参考 `docs/` 目录：
- API文档
- 部署指南
- 开发指南
- 故障排除

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 📄 许可证

本项目采用MIT许可证。 