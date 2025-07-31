import { createI18n } from 'vue-i18n'

const messages = {
  'zh-CN': {
    common: {
      login: '登录',
      register: '注册',
      logout: '退出登录',
      dashboard: '仪表板',
      repositories: '仓库管理',
      documents: '文档管理',
      users: '用户管理',
      roles: '角色管理',

      appConfig: '应用配置',
      chat: 'AI对话',
      settings: '设置',
      search: '搜索',
      add: '添加',
      edit: '编辑',
      delete: '删除',
      save: '保存',
      cancel: '取消',
      confirm: '确认',
      loading: '加载中...',
      success: '操作成功',
      error: '操作失败',
      warning: '警告',
      info: '提示'
    },
    auth: {
      username: '用户名',
      password: '密码',
      email: '邮箱',
      fullName: '姓名',
      loginTitle: '登录到OpenDeepWiki',
      registerTitle: '注册新账户',
      forgotPassword: '忘记密码？',
      rememberMe: '记住我',
      loginButton: '登录',
      registerButton: '注册',
      loginSuccess: '登录成功',
      registerSuccess: '注册成功',
      invalidCredentials: '用户名或密码错误'
    },
    repository: {
      name: '仓库名称',
      description: '仓库描述',
      url: '仓库地址',
      branch: '分支',
      status: '状态',
      type: '类型',
      organization: '组织',
      createTime: '创建时间',
      updateTime: '更新时间',
      addRepository: '添加仓库',
      editRepository: '编辑仓库',
      deleteRepository: '删除仓库',
      repositoryDetail: '仓库详情',
      cloneRepository: '克隆仓库',
      processRepository: '处理仓库'
    },
    document: {
      title: '文档标题',
      content: '文档内容',
      catalog: '文档目录',
      createTime: '创建时间',
      updateTime: '更新时间',
      addDocument: '添加文档',
      editDocument: '编辑文档',
      deleteDocument: '删除文档',
      generateDocument: '生成文档',
      documentDetail: '文档详情'
    },
    user: {
      username: '用户名',
      email: '邮箱',
      fullName: '姓名',
      role: '角色',
      status: '状态',
      createTime: '创建时间',
      addUser: '添加用户',
      editUser: '编辑用户',
      deleteUser: '删除用户',
      changePassword: '修改密码',
      oldPassword: '原密码',
      newPassword: '新密码',
      confirmPassword: '确认密码'
    },
    role: {
      name: '角色名称',
      description: '角色描述',
      permissions: '权限',
      createTime: '创建时间',
      addRole: '添加角色',
      editRole: '编辑角色',
      deleteRole: '删除角色',
      assignPermissions: '分配权限',
      assignUsers: '分配用户'
    },


    },
    appConfig: {
      appId: '应用ID',
      name: '应用名称',
      description: '应用描述',
      organization: '组织',
      repository: '仓库',
      domain: '域名',
      model: '模型',
      prompt: '提示词',
      introduction: '介绍',
      createTime: '创建时间',
      addConfig: '添加配置',
      editConfig: '编辑配置',
      deleteConfig: '删除配置',
      validateDomain: '验证域名',
      toggleStatus: '切换状态'
    }
  },
  'en-US': {
    common: {
      login: 'Login',
      register: 'Register',
      logout: 'Logout',
      dashboard: 'Dashboard',
      repositories: 'Repositories',
      documents: 'Documents',
      users: 'Users',
      roles: 'Roles',

      appConfig: 'App Config',
      chat: 'AI Chat',
      settings: 'Settings',
      search: 'Search',
      add: 'Add',
      edit: 'Edit',
      delete: 'Delete',
      save: 'Save',
      cancel: 'Cancel',
      confirm: 'Confirm',
      loading: 'Loading...',
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Info'
    }
  }
}

const i18n = createI18n({
  locale: 'zh-CN',
  fallbackLocale: 'en-US',
  messages
})

export default i18n 