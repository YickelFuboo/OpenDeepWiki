<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>用户登录</h2>
        <p>欢迎使用 OpenDeepWiki</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <!-- 登录方式切换 -->
        <el-tabs v-model="loginMethod" class="login-tabs">
          <el-tab-pane label="密码登录" name="password">
            <el-form-item prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="用户名/邮箱/手机号"
                prefix-icon="User"
                size="large"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                prefix-icon="Lock"
                size="large"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                style="width: 100%"
                @click="handlePasswordLogin"
                :loading="loading"
              >
                登录
              </el-button>
            </el-form-item>
          </el-tab-pane>

          <el-tab-pane label="验证码登录" name="code">
            <el-form-item prop="phone">
              <el-input
                v-model="loginForm.phone"
                placeholder="手机号"
                prefix-icon="Phone"
                size="large"
              />
            </el-form-item>

            <el-form-item prop="code">
              <div class="code-input">
                <el-input
                  v-model="loginForm.code"
                  placeholder="验证码"
                  prefix-icon="Key"
                  size="large"
                />
                <el-button
                  type="primary"
                  :disabled="countdown > 0"
                  @click="sendCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                style="width: 100%"
                @click="handleCodeLogin"
                :loading="loading"
              >
                登录
              </el-button>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>

        <!-- OAuth登录 -->
        <OAuthLogin
          :show-phone-login="false"
          @success="handleOAuthSuccess"
          @error="handleOAuthError"
        />

        <!-- 其他选项 -->
        <div class="login-options">
          <el-link type="primary" @click="$router.push('/register')">
            还没有账号？立即注册
          </el-link>
          <el-link type="primary" @click="$router.push('/forgot-password')">
            忘记密码？
          </el-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import OAuthLogin from '@/components/auth/OAuthLogin.vue'

const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const loginMethod = ref('password')
const loading = ref(false)
const countdown = ref(0)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  phone: '',
  code: ''
})

const loginFormRef = ref()

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名/邮箱/手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

// 密码登录
const handlePasswordLogin = async () => {
  try {
    await loginFormRef.value.validate()
    
    loading.value = true
    
    const response = await authApi.login({
      username: loginForm.username,
      password: loginForm.password
    })
    
    await authStore.login(response.data)
    ElMessage.success('登录成功')
    
    // 跳转到首页或之前的页面
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

// 验证码登录
const handleCodeLogin = async () => {
  try {
    await loginFormRef.value.validate()
    
    loading.value = true
    
    const response = await authApi.phoneLogin({
      phone: loginForm.phone,
      code: loginForm.code
    })
    
    await authStore.login(response.data)
    ElMessage.success('登录成功')
    
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

// 发送验证码
const sendCode = async () => {
  try {
    if (!loginForm.phone) {
      ElMessage.warning('请先输入手机号')
      return
    }
    
    if (!/^1[3-9]\d{9}$/.test(loginForm.phone)) {
      ElMessage.error('请输入正确的手机号')
      return
    }
    
    await authApi.sendSmsCode(loginForm.phone)
    
    ElMessage.success('验证码已发送')
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '发送验证码失败')
  }
}

// OAuth登录成功
const handleOAuthSuccess = async (data: any) => {
  try {
    await authStore.login(data)
    ElMessage.success('登录成功')
    
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  } catch (error: any) {
    ElMessage.error('OAuth登录失败')
  }
}

// OAuth登录失败
const handleOAuthError = (error: any) => {
  ElMessage.error('OAuth登录失败')
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 24px;
}

.login-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.login-form {
  margin-top: 20px;
}

.login-tabs {
  margin-bottom: 20px;
}

.code-input {
  display: flex;
  gap: 12px;
}

.code-input .el-input {
  flex: 1;
}

.code-input .el-button {
  width: 120px;
}

.login-options {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}
</style> 