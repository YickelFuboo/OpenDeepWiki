// 全局类型声明

// 用户相关类型
export interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
  avatar?: string
  created_at: string
  updated_at: string
}

// 仓库相关类型
export interface Repository {
  id: string
  name: string
  description?: string
  url: string
  branch: string
  status: string
  type: string
  organization?: string
  created_at: string
  updated_at: string
}

// 文档相关类型
export interface Document {
  id: string
  title: string
  content: string
  warehouse_id: string
  catalog_id?: string
  created_at: string
  updated_at: string
}

// 角色相关类型
export interface Role {
  id: string
  name: string
  description?: string
  permissions: string[]
  created_at: string
  updated_at: string
}



// 应用配置相关类型
export interface AppConfig {
  app_id: string
  name: string
  organization_name?: string
  repository_name?: string
  description?: string
  prompt?: string
  introduction?: string
  model?: string
  allowed_domains: string[]
  enable_domain_validation: boolean
  is_enabled: boolean
  created_at: string
  updated_at: string
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
}

export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 菜单项类型
export interface MenuItem {
  path: string
  name: string
  icon?: string
  children?: MenuItem[]
}

// 面包屑类型
export interface BreadcrumbItem {
  path: string
  name: string
} 