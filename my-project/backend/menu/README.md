# 菜单管理模块

## 概述

菜单管理模块负责处理系统中的菜单构建、权限控制和用户界面导航。该模块提供了基于角色的菜单过滤、权限检查和面包屑导航等功能。

## 功能特性

### 🎯 核心功能

- **用户菜单构建**: 根据用户角色动态构建个性化菜单
- **权限控制**: 基于角色的菜单访问控制
- **路径权限检查**: 检查用户对特定路径的访问权限
- **面包屑导航**: 生成当前页面的面包屑路径
- **菜单激活状态**: 判断菜单项的激活状态
- **菜单扁平化**: 将树形菜单结构扁平化处理

### 🔐 权限管理

- **角色基础权限**: 基于用户角色的菜单访问控制
- **动态权限检查**: 实时检查用户对路径的访问权限
- **管理员权限**: 管理员可访问所有菜单项
- **公共菜单**: 无需权限的公共菜单项

## 目录结构

```
menu/
├── README.md                    # 模块文档
├── services/
│   └── menu_service.py         # 菜单服务
├── api/
│   └── menu_routes.py          # 菜单API路由
└── tests/
    └── test_menu.py            # 菜单测试
```

## API接口

### 1. 获取用户菜单

**接口**: `GET /v1/menus/user-menu`

**描述**: 获取当前用户的个性化菜单

**请求参数**: 无

**响应示例**:
```json
{
  "user": {
    "id": "user-123",
    "username": "testuser",
    "email": "test@example.com",
    "role": "admin,user"
  },
  "menus": [
    {
      "id": "dashboard",
      "name": "首页",
      "path": "/",
      "icon": "dashboard",
      "order": 1,
      "required_roles": [],
      "children": []
    },
    {
      "id": "repositories",
      "name": "仓库管理",
      "path": "/repositories",
      "icon": "repository",
      "order": 2,
      "required_roles": [],
      "children": [
        {
          "id": "repository-list",
          "name": "仓库列表",
          "path": "/repositories",
          "order": 1,
          "required_roles": [],
          "children": []
        }
      ]
    }
  ]
}
```

### 2. 获取系统菜单

**接口**: `GET /v1/menus/system-menus`

**描述**: 获取完整的系统菜单结构（需要管理员权限）

**请求参数**: 无

**权限要求**: `admin`

**响应示例**:
```json
[
  {
    "id": "dashboard",
    "name": "首页",
    "path": "/",
    "icon": "dashboard",
    "order": 1,
    "required_roles": [],
    "children": []
  },
  {
    "id": "admin",
    "name": "系统管理",
    "path": "/admin",
    "icon": "admin",
    "order": 1,
    "required_roles": ["admin"],
    "children": [
      {
        "id": "admin-users",
        "name": "用户管理",
        "path": "/admin/users",
        "icon": "user",
        "order": 1,
        "required_roles": ["admin"],
        "children": []
      }
    ]
  }
]
```

### 3. 检查路径权限

**接口**: `GET /v1/menus/check-permission`

**描述**: 检查用户是否有访问指定路径的权限

**请求参数**:
- `path` (string, 必需): 要检查的路径
- `user_id` (string, 可选): 用户ID，默认为当前用户

**响应示例**:
```json
{
  "data": {
    "has_permission": true,
    "path": "/admin/users",
    "user_id": "user-123"
  }
}
```

### 4. 获取面包屑

**接口**: `GET /v1/menus/breadcrumb`

**描述**: 获取当前路径的面包屑导航

**请求参数**:
- `current_path` (string, 必需): 当前路径

**响应示例**:
```json
{
  "data": [
    {
      "id": "admin",
      "name": "系统管理",
      "path": "/admin",
      "icon": "admin",
      "order": 1,
      "required_roles": ["admin"],
      "children": []
    },
    {
      "id": "admin-users",
      "name": "用户管理",
      "path": "/admin/users",
      "icon": "user",
      "order": 1,
      "required_roles": ["admin"],
      "children": []
    }
  ]
}
```

### 5. 获取管理员菜单列表

**接口**: `GET /v1/menus/admin-menu-list`

**描述**: 获取管理员专用的菜单列表

**权限要求**: `admin`

**响应示例**:
```json
[
  {
    "id": "admin",
    "name": "系统管理",
    "path": "/admin",
    "icon": "admin",
    "order": 1,
    "required_roles": ["admin"],
    "children": [
      {
        "id": "admin-users",
        "name": "用户管理",
        "path": "/admin/users",
        "icon": "user",
        "order": 1,
        "required_roles": ["admin"],
        "children": []
      }
    ]
  }
]
```

### 6. 获取扁平化菜单

**接口**: `GET /v1/menus/flatten-menus`

**描述**: 获取扁平化的菜单列表

**响应示例**:
```json
{
  "data": [
    {
      "id": "dashboard",
      "name": "首页",
      "path": "/",
      "icon": "dashboard",
      "order": 1,
      "required_roles": [],
      "children": []
    },
    {
      "id": "repository-list",
      "name": "仓库列表",
      "path": "/repositories",
      "icon": "repository",
      "order": 1,
      "required_roles": [],
      "children": []
    }
  ]
}
```

### 7. 获取菜单信息

**接口**: `GET /v1/menus/menu-info`

**描述**: 获取指定路径的菜单详细信息

**请求参数**:
- `path` (string, 必需): 菜单路径

**响应示例**:
```json
{
  "data": {
    "menu_item": {
      "id": "admin-users",
      "name": "用户管理",
      "path": "/admin/users",
      "icon": "user",
      "order": 1,
      "required_roles": ["admin"],
      "children": []
    },
    "has_permission": true,
    "is_active": true
  }
}
```

### 8. 获取用户角色

**接口**: `GET /v1/menus/user-roles`

**描述**: 获取当前用户的角色信息

**响应示例**:
```json
{
  "data": {
    "user_id": "user-123",
    "username": "testuser",
    "roles": [
      {
        "id": "role-1",
        "name": "admin",
        "description": "管理员",
        "is_active": true,
        "is_system_role": true
      }
    ]
  }
}
```

### 9. 获取菜单统计

**接口**: `GET /v1/menus/menu-stats`

**描述**: 获取菜单统计信息

**响应示例**:
```json
{
  "data": {
    "total_user_menus": 15,
    "total_system_menus": 20,
    "accessible_percentage": 75.0,
    "top_level_menus": 8,
    "has_admin_access": true
  }
}
```

## 菜单结构

### 系统菜单定义

系统包含以下主要菜单项：

1. **首页** (`/`)
   - 权限: 所有用户
   - 图标: dashboard

2. **仓库管理** (`/repositories`)
   - 权限: 所有用户
   - 子菜单:
     - 仓库列表 (`/repositories`)
     - 创建仓库 (`/repositories/create`) - 需要admin权限

3. **用户管理** (`/admin/users`)
   - 权限: admin
   - 图标: user

4. **角色管理** (`/admin/roles`)
   - 权限: admin
   - 图标: role

5. **权限管理** (`/admin/permissions`)
   - 权限: admin
   - 图标: permission
   - 子菜单:
     - 角色权限 (`/admin/permissions/roles`)
     - 用户角色 (`/admin/permissions/users`)

6. **系统设置** (`/admin/settings`)
   - 权限: admin
   - 图标: setting
   - 子菜单:
     - 基本设置 (`/admin/settings/general`)
     - 系统信息 (`/admin/settings/system`)

7. **微调管理** (`/admin/finetune`)
   - 权限: admin
   - 图标: finetune

8. **统计分析** (`/admin/statistics`)
   - 权限: admin
   - 图标: statistics

9. **个人设置** (`/settings`)
   - 权限: 所有用户
   - 图标: profile

## 使用示例

### 前端集成

```typescript
// 获取用户菜单
const getUserMenu = async () => {
  const response = await fetch('/v1/menus/user-menu', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data;
};

// 检查路径权限
const checkPermission = async (path: string) => {
  const response = await fetch(`/v1/menus/check-permission?path=${path}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data.has_permission;
};

// 获取面包屑
const getBreadcrumb = async (currentPath: string) => {
  const response = await fetch(`/v1/menus/breadcrumb?current_path=${currentPath}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await response.json();
  return data.data;
};
```

### 菜单渲染

```typescript
// React组件示例
const MenuComponent = ({ menus }) => {
  const renderMenuItem = (item) => {
    return (
      <MenuItem key={item.id}>
        <Link href={item.path}>
          {item.icon && <Icon name={item.icon} />}
          {item.name}
        </Link>
        {item.children && item.children.length > 0 && (
          <SubMenu>
            {item.children.map(renderMenuItem)}
          </SubMenu>
        )}
      </MenuItem>
    );
  };

  return (
    <Menu>
      {menus.map(renderMenuItem)}
    </Menu>
  );
};
```

## 配置说明

### 环境变量

菜单模块不需要特殊的环境变量配置，但依赖于以下模块：

- 用户认证模块
- 角色权限模块
- 数据库连接

### 数据库依赖

菜单模块依赖以下数据表：

- `users` - 用户信息
- `roles` - 角色信息
- `user_in_roles` - 用户角色关联

## 测试

### 运行测试

```bash
# 运行菜单模块测试
pytest tests/test_menu.py -v

# 运行所有测试
pytest tests/ -v

# 生成测试覆盖率报告
pytest tests/test_menu.py --cov=services.menu_service --cov-report=html
```

### 测试覆盖

测试覆盖以下功能：

- ✅ 用户菜单获取
- ✅ 系统菜单获取
- ✅ 路径权限检查
- ✅ 菜单过滤
- ✅ 面包屑生成
- ✅ 菜单激活状态
- ✅ 菜单扁平化

## 注意事项

### 性能考虑

1. **菜单缓存**: 建议在前端缓存用户菜单，减少API调用
2. **权限缓存**: 可以缓存用户权限信息，提高响应速度
3. **数据库查询优化**: 使用适当的索引优化角色查询

### 安全考虑

1. **权限验证**: 所有菜单访问都需要验证用户权限
2. **路径验证**: 检查用户对特定路径的访问权限
3. **角色验证**: 确保用户角色信息的准确性

### 扩展性

1. **动态菜单**: 支持从数据库动态加载菜单配置
2. **自定义菜单**: 允许用户自定义菜单项
3. **多语言支持**: 支持菜单项的多语言显示

## 故障排除

### 常见问题

1. **菜单不显示**
   - 检查用户角色是否正确分配
   - 验证菜单权限配置
   - 确认用户状态是否激活

2. **权限检查失败**
   - 检查用户角色是否存在
   - 验证角色是否激活
   - 确认路径权限配置

3. **面包屑不完整**
   - 检查菜单路径配置
   - 验证菜单层级关系
   - 确认当前路径是否正确

### 调试方法

1. **启用日志**: 查看菜单服务的详细日志
2. **检查权限**: 使用权限检查API验证用户权限
3. **测试菜单**: 使用测试用例验证菜单功能

## 扩展

### 添加新菜单项

1. 在 `MenuService._get_system_menu_structure()` 中添加新菜单项
2. 配置菜单的权限要求
3. 更新前端路由配置
4. 添加相应的测试用例

### 自定义菜单逻辑

1. 继承 `MenuService` 类
2. 重写相关方法
3. 注册自定义服务
4. 更新API路由

---

**注意**: 菜单管理模块是系统权限控制的重要组成部分，请确保正确配置用户角色和权限。 