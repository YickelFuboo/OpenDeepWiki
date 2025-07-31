# OpenDeepWiki 前端项目

## 项目概述

这是 OpenDeepWiki 项目的 Vue 3 前端实现，采用现代化的技术栈和组件库，提供完整的用户界面和交互体验。

## 🏗️ 技术栈

- **框架**: Vue 3 + TypeScript
- **路由**: Vue Router 4
- **状态管理**: Pinia
- **UI组件库**: Element Plus
- **构建工具**: Vite
- **HTTP客户端**: Axios
- **国际化**: Vue I18n
- **图表**: ECharts
- **Markdown**: Marked + Highlight.js
- **流程图**: Mermaid

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── api/               # API接口封装
│   │   └── index.ts       # 所有后台接口定义
│   ├── assets/            # 资源文件
│   ├── components/        # 公共组件
│   ├── layout/            # 布局组件
│   │   └── Layout.vue     # 主布局
│   ├── router/            # 路由配置
│   │   └── index.ts       # 路由定义
│   ├── stores/            # 状态管理
│   │   └── user.ts        # 用户状态
│   ├── views/             # 页面组件
│   │   ├── Login.vue      # 登录页面
│   │   ├── Dashboard.vue  # 仪表板
│   │   ├── Repositories.vue # 仓库管理
│   │   ├── Documents.vue  # 文档管理
│   │   ├── Users.vue      # 用户管理
│   │   ├── Roles.vue      # 角色管理

│   │   ├── AppConfig.vue  # 应用配置
│   │   ├── Chat.vue       # AI对话
│   │   └── Settings.vue   # 设置页面
│   ├── i18n/              # 国际化
│   │   └── index.ts       # 语言配置
│   ├── utils/             # 工具函数
│   ├── App.vue            # 根组件
│   ├── main.ts            # 入口文件
│   └── style.css          # 全局样式
├── index.html             # HTML模板
├── package.json           # 依赖配置
├── tsconfig.json          # TypeScript配置
├── vite.config.ts         # Vite配置
└── README.md              # 项目文档
```

## 🚀 快速开始

### 环境要求

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd my-project/frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 📚 API接口

所有后台接口都封装在 `src/api/index.ts` 文件中，包括：

### 认证相关
- `authApi.login()` - 用户登录
- `authApi.register()` - 用户注册
- `authApi.refresh()` - 刷新令牌
- `authApi.getCurrentUser()` - 获取当前用户信息

### 用户管理
- `userApi.getUsers()` - 获取用户列表
- `userApi.createUser()` - 创建用户
- `userApi.updateUser()` - 更新用户
- `userApi.deleteUser()` - 删除用户

### 仓库管理
- `repositoryApi.getRepositories()` - 获取仓库列表
- `repositoryApi.createRepository()` - 创建仓库
- `repositoryApi.updateRepository()` - 更新仓库
- `repositoryApi.deleteRepository()` - 删除仓库

### 文档管理
- `documentApi.getDocuments()` - 获取文档列表
- `documentApi.getDocumentCatalogs()` - 获取文档目录
- `documentApi.getDocumentContent()` - 获取文档内容

### 角色权限
- `roleApi.getRoles()` - 获取角色列表
- `roleApi.createRole()` - 创建角色
- `roleApi.setRolePermissions()` - 设置角色权限

### AI功能
- `aiApi.analyzeCode()` - 代码分析
- `aiApi.generateDocs()` - 生成文档
- `aiApi.chat()` - AI对话



### 应用配置
- `appConfigApi.getAppConfigs()` - 获取应用配置
- `appConfigApi.createAppConfig()` - 创建应用配置
- `appConfigApi.validateDomain()` - 域名验证

## 🎨 组件库

项目使用 Element Plus 作为主要UI组件库，并进行了以下定制：

### 主题定制
- 自定义颜色变量
- 统一的组件样式
- 响应式设计

### 常用组件
- 表格组件 (el-table)
- 表单组件 (el-form)
- 对话框组件 (el-dialog)
- 消息提示 (el-message)
- 加载状态 (el-loading)

## 🌐 国际化

支持中文和英文两种语言：

```typescript
// 使用示例
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const message = t('common.login')
```

## 📊 状态管理

使用 Pinia 进行状态管理：

### 用户状态 (stores/user.ts)
- 用户信息管理
- 登录状态管理
- 令牌管理

### 使用示例
```typescript
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
await userStore.login(username, password)
```

## 🛣️ 路由配置

路由配置在 `src/router/index.ts` 中定义：

### 路由结构
- `/login` - 登录页面
- `/register` - 注册页面
- `/` - 仪表板
- `/repositories` - 仓库管理
- `/documents` - 文档管理
- `/users` - 用户管理
- `/roles` - 角色管理

- `/app-config` - 应用配置
- `/chat` - AI对话
- `/settings` - 设置

### 路由守卫
- 自动检查登录状态
- 未登录自动跳转到登录页
- 已登录访问登录页自动跳转到首页

## 🎯 主要功能

### 1. 用户认证
- 登录/注册
- JWT令牌管理
- 自动刷新令牌
- 用户信息管理

### 2. 仓库管理
- 仓库列表展示
- 添加/编辑/删除仓库
- 仓库状态监控
- 仓库详情查看

### 3. 文档管理
- 文档列表展示
- 文档目录树
- 文档内容查看
- 文档生成

### 4. 用户管理
- 用户列表
- 用户CRUD操作
- 角色分配
- 权限管理

### 5. AI功能
- AI对话界面
- 代码分析
- 文档生成


### 6. 系统管理
- 角色权限管理
- 应用配置管理
- 系统设置

## 🔧 开发指南

### 添加新页面
1. 在 `src/views/` 创建页面组件
2. 在 `src/router/index.ts` 添加路由配置
3. 在侧边栏菜单中添加导航项

### 添加新API
1. 在 `src/api/index.ts` 添加API方法
2. 在页面组件中调用API
3. 处理响应和错误

### 添加新组件
1. 在 `src/components/` 创建组件
2. 使用TypeScript定义props和emits
3. 添加必要的样式

### 代码规范
- 使用TypeScript进行类型检查
- 遵循Vue 3 Composition API
- 使用ESLint进行代码检查
- 使用Prettier进行代码格式化

## 🚀 部署

### 构建
```bash
npm run build
```

### Docker部署
```dockerfile
FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx配置
```nginx
server {
    listen 80;
    server_name localhost;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 更新日志

### v1.0.0 (2024-07-29)
- ✅ Vue 3 + TypeScript 项目初始化
- ✅ Element Plus UI组件库集成
- ✅ Vue Router 路由配置
- ✅ Pinia 状态管理
- ✅ Axios API封装
- ✅ 国际化支持
- ✅ 响应式布局
- ✅ 用户认证系统
- ✅ 仓库管理界面
- ✅ 文档管理界面
- ✅ 用户管理界面
- ✅ 角色权限管理
- ✅ AI对话界面

- ✅ 应用配置管理

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

**注意**: 这是一个现代化的Vue 3前端项目，提供了完整的用户界面和交互体验，与Python后端完美配合。 