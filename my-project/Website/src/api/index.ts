import axios from 'axios'
import type { AxiosInstance, AxiosResponse } from 'axios'

import { ElMessage } from 'element-plus'

import router from '@/router'


// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(error.response?.data?.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

// 通用响应类型
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

// 认证相关API
export const authApi = {
  // 用户登录
  login: (data: { username: string; password: string }) =>
    api.post<ApiResponse<{ access_token: string; token_type: string; expires_in: number }>>('/auth/login', data),

  // 用户注册
  register: (data: { username: string; email: string; password: string; full_name: string }) =>
    api.post<ApiResponse>('/auth/register', data),

  // 刷新令牌
  refresh: (data: { refresh_token: string }) =>
    api.post<ApiResponse<{ access_token: string; token_type: string; expires_in: number }>>('/auth/refresh', data),

  // 获取当前用户信息
  getCurrentUser: () => api.get<ApiResponse>('/auth/me'),

  // 修改密码
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post<ApiResponse>('/auth/change-password', data)
}

// 仓库管理API
export const repositoryApi = {
  // 获取仓库列表
  getRepositories: (params?: { page?: number; size?: number; status?: string; search?: string }) =>
    api.get<ApiResponse<PaginatedResponse>>('/repositories', { params }),

  // 创建仓库
  createRepository: (data: {
    name: string
    url: string
    description?: string
    branch?: string
    is_public?: boolean
  }) => api.post<ApiResponse>('/repositories', data),

  // 更新仓库
  updateRepository: (warehouseId: string, data: { name?: string; description?: string }) =>
    api.put<ApiResponse>(`/repositories/${warehouseId}`, data),

  // 删除仓库
  deleteRepository: (warehouseId: string) => api.delete<ApiResponse>(`/repositories/${warehouseId}`),

  // 获取仓库详情
  getRepository: (warehouseId: string) => api.get<ApiResponse>(`/repositories/${warehouseId}`)
}

// 文档管理API
export const documentApi = {
  // 获取文档列表
  getDocuments: (params?: { warehouse_id?: string; page?: number; size?: number }) =>
    api.get<ApiResponse<PaginatedResponse>>('/documents', { params }),

  // 获取文档目录
  getDocumentCatalogs: (warehouseId: string) =>
    api.get<ApiResponse>(`/document-catalogs/${warehouseId}`),

  // 获取文档内容
  getDocumentContent: (catalogId: string) =>
    api.get<ApiResponse>(`/documents/content/${catalogId}`)
}

// 用户管理API
export const userApi = {
  // 获取用户列表
  getUsers: (params?: { page?: number; size?: number; search?: string }) =>
    api.get<ApiResponse<PaginatedResponse>>('/users', { params }),

  // 创建用户
  createUser: (data: { username: string; email: string; password: string; full_name: string; role?: string }) =>
    api.post<ApiResponse>('/users', data),

  // 更新用户
  updateUser: (userId: string, data: { full_name?: string; email?: string; role?: string }) =>
    api.put<ApiResponse>(`/users/${userId}`, data),

  // 删除用户
  deleteUser: (userId: string) => api.delete<ApiResponse>(`/users/${userId}`)
}

// 角色权限API
export const roleApi = {
  // 获取角色列表
  getRoles: () => api.get<ApiResponse>('/roles'),

  // 创建角色
  createRole: (data: { name: string; description?: string; permissions?: string[] }) =>
    api.post<ApiResponse>('/roles', data),

  // 更新角色
  updateRole: (roleId: string, data: { name?: string; description?: string; permissions?: string[] }) =>
    api.put<ApiResponse>(`/roles/${roleId}`, data),

  // 删除角色
  deleteRole: (roleId: string) => api.delete<ApiResponse>(`/roles/${roleId}`)
}

// AI功能API
export const aiApi = {
  // 代码分析
  analyzeCode: (data: { warehouse_id: string; file_path: string; analysis_type: string }) =>
    api.post<ApiResponse>('/ai/analyze', data),

  // 生成文档
  generateDocs: (data: { warehouse_id: string; doc_type: string; template?: string }) =>
    api.post<ApiResponse>('/ai/generate-docs', data),

  // AI对话
  chat: (data: { message: string; context?: string; model?: string }) =>
    api.post<ApiResponse>('/ai/chat', data)
}



// 应用配置API
export const appConfigApi = {
  // 获取应用配置列表
  getAppConfigs: () => api.get<ApiResponse>('/app-config'),

  // 创建应用配置
  createAppConfig: (data: {
    app_id: string
    name: string
    organization_name?: string
    repository_name?: string
    description?: string
    prompt?: string
    introduction?: string
    model?: string
    allowed_domains?: string[]
    enable_domain_validation?: boolean
  }) => api.post<ApiResponse>('/app-config', data),

  // 更新应用配置
  updateAppConfig: (appId: string, data: {
    name?: string
    description?: string
    prompt?: string
    introduction?: string
    model?: string
    allowed_domains?: string[]
    enable_domain_validation?: boolean
  }) => api.put<ApiResponse>(`/app-config/${appId}`, data)
}

export default api 