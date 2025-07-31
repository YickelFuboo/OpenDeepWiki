<template>
  <div class="oauth-callback">
    <div class="callback-container">
      <div class="loading-spinner" v-if="loading">
        <el-icon class="is-loading"><Loading /></el-icon>
        <p>正在处理登录...</p>
      </div>
      
      <div class="error-message" v-if="error">
        <el-icon><Warning /></el-icon>
        <p>{{ error }}</p>
        <el-button type="primary" @click="$router.push('/login')">
          返回登录页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Warning } from '@element-plus/icons-vue'
import { oauthApi } from '@/api/oauth'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    // 从URL参数获取OAuth回调数据
    const provider = route.query.provider as string
    const code = route.query.code as string
    const state = route.query.state as string
    const error = route.query.error as string
    
    if (error) {
      throw new Error(`OAuth错误: ${error}`)
    }
    
    if (!provider || !code) {
      throw new Error('缺少必要的OAuth参数')
    }
    
    // 调用OAuth回调API
    const response = await oauthApi.oauthCallback(provider, {
      code,
      state
    })
    
    // 处理登录成功
    if (response.data.access_token) {
      // 存储令牌
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      // 更新用户信息
      await userStore.setUserInfo(response.data.user)
      
      ElMessage.success(`${provider}登录成功`)
      router.push('/')
    } else {
      throw new Error('登录失败：未获取到访问令牌')
    }
    
  } catch (err: any) {
    console.error('OAuth回调处理失败:', err)
    error.value = err.message || 'OAuth登录失败'
    loading.value = false
  }
})
</script>

<style scoped>
.oauth-callback {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.callback-container {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.loading-spinner .el-icon {
  font-size: 48px;
  color: #409eff;
}

.loading-spinner p {
  color: #666;
  font-size: 16px;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.error-message .el-icon {
  font-size: 48px;
  color: #f56c6c;
}

.error-message p {
  color: #f56c6c;
  font-size: 16px;
}
</style> 