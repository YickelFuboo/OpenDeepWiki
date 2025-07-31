<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="layout-aside">
      <div class="logo">
        <h2>OpenDeepWiki</h2>
      </div>
      
      <el-menu
        :default-active="$route.path"
        class="layout-menu"
        router
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        
        <el-menu-item index="/repositories">
          <el-icon><Folder /></el-icon>
          <span>仓库管理</span>
        </el-menu-item>
        
        <el-menu-item index="/documents">
          <el-icon><Document /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
        
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI对话</span>
        </el-menu-item>
        
        <el-sub-menu index="admin">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/roles">
            <el-icon><UserFilled /></el-icon>
            <span>角色管理</span>
          </el-menu-item>
          

          
          <el-menu-item index="/app-config">
            <el-icon><Tools /></el-icon>
            <span>应用配置</span>
          </el-menu-item>
        </el-sub-menu>
        
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" :to="item.path">
              {{ item.name }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" :src="userStore.user?.avatar">
                {{ userStore.user?.full_name?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userStore.user?.full_name }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 面包屑导航
const breadcrumbs = computed(() => {
  const paths = route.path.split('/').filter(Boolean)
  const items = [{ path: '/', name: '首页' }]
  
  let currentPath = ''
  paths.forEach((path, index) => {
    currentPath += `/${path}`
    const name = getRouteName(path)
    if (name) {
      items.push({ path: currentPath, name })
    }
  })
  
  return items
})

const getRouteName = (path: string) => {
  const routeNames: Record<string, string> = {
    repositories: '仓库管理',
    documents: '文档管理',
    users: '用户管理',
    roles: '角色管理',

    'app-config': '应用配置',
    chat: 'AI对话',
    settings: '设置'
  }
  return routeNames[path] || path
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      // 跳转到个人资料页面
      break
    case 'password':
      // 打开修改密码对话框
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        userStore.logout()
        router.push('/login')
      } catch {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.layout-aside {
  background-color: #001529;
  color: white;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #1f2937;
}

.logo h2 {
  color: white;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.layout-menu {
  border-right: none;
}

.layout-header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.username {
  margin: 0 8px;
  font-size: 14px;
  color: #333;
}

.layout-main {
  background-color: #f5f7fa;
  padding: 20px;
}

@media (max-width: 768px) {
  .layout-aside {
    width: 100% !important;
    height: auto !important;
  }
  
  .layout-container {
    flex-direction: column;
  }
  
  .layout-header {
    padding: 0 10px;
  }
  
  .layout-main {
    padding: 10px;
  }
}
</style> 