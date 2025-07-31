// 应用常量定义

// API相关常量
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
export const API_TIMEOUT = 30000

// 应用信息
export const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'OpenDeepWiki'
export const APP_VERSION = '1.0.0'

// 本地存储键名
export const STORAGE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'user_info',
  THEME: 'theme',
  LANGUAGE: 'language'
} as const

// 路由路径
export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  DASHBOARD: '/',
  REPOSITORIES: '/repositories',
  DOCUMENTS: '/documents',
  USERS: '/users',
  ROLES: '/roles',

  APP_CONFIG: '/app-config',
  CHAT: '/chat',
  SETTINGS: '/settings'
} as const

// 状态常量
export const STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled'
} as const

// 仓库类型
export const REPOSITORY_TYPES = {
  GITHUB: 'github',
  GITEE: 'gitee',
  GITLAB: 'gitlab',
  OTHER: 'other'
} as const

// 文档类型
export const DOCUMENT_TYPES = {
  README: 'readme',
  API_DOC: 'api_doc',
  ARCHITECTURE: 'architecture',
  DEPLOYMENT: 'deployment',
  DEVELOPMENT: 'development'
} as const



// 权限常量
export const PERMISSIONS = {
  READ: 'read',
  WRITE: 'write',
  DELETE: 'delete',
  ADMIN: 'admin'
} as const

// 角色常量
export const ROLES = {
  ADMIN: 'admin',
  USER: 'user',
  GUEST: 'guest'
} as const

// 主题常量
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto'
} as const

// 语言常量
export const LANGUAGES = {
  ZH_CN: 'zh-CN',
  EN_US: 'en-US'
} as const

// 分页常量
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_SIZE: 10,
  MAX_SIZE: 100
} as const

// 文件上传常量
export const UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: ['.txt', '.md', '.json', '.yaml', '.yml']
} as const

// 图表颜色
export const CHART_COLORS = [
  '#409eff',
  '#67c23a',
  '#e6a23c',
  '#f56c6c',
  '#909399',
  '#9c27b0',
  '#ff9800',
  '#795548'
] as const

// 响应式断点
export const BREAKPOINTS = {
  XS: 480,
  SM: 768,
  MD: 992,
  LG: 1200,
  XL: 1920
} as const 