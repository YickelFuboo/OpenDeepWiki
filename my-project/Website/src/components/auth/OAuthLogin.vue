<template>
  <div class="oauth-login">
    <div class="oauth-title">
      <span>或使用以下方式登录</span>
    </div>
    
    <div class="oauth-buttons">
      <!-- GitHub登录 -->
      <el-button
        v-if="providers.includes('github')"
        type="primary"
        class="oauth-btn github-btn"
        @click="handleOAuthLogin('github')"
        :loading="loading === 'github'"
      >
        <i class="fab fa-github"></i>
        GitHub登录
      </el-button>
      
      <!-- Google登录 -->
      <el-button
        v-if="providers.includes('google')"
        type="primary"
        class="oauth-btn google-btn"
        @click="handleOAuthLogin('google')"
        :loading="loading === 'google'"
      >
        <i class="fab fa-google"></i>
        Google登录
      </el-button>
      
      <!-- 微信登录 -->
      <el-button
        v-if="providers.includes('wechat')"
        type="success"
        class="oauth-btn wechat-btn"
        @click="handleOAuthLogin('wechat')"
        :loading="loading === 'wechat'"
      >
        <i class="fab fa-weixin"></i>
        微信登录
      </el-button>
      
      <!-- 支付宝登录 -->
      <el-button
        v-if="providers.includes('alipay')"
        type="primary"
        class="oauth-btn alipay-btn"
        @click="handleOAuthLogin('alipay')"
        :loading="loading === 'alipay'"
      >
        <i class="fab fa-alipay"></i>
        支付宝登录
      </el-button>
      
      <!-- OIDC登录 -->
      <el-button
        v-if="providers.includes('oidc')"
        type="info"
        class="oauth-btn oidc-btn"
        @click="handleOidcLogin"
        :loading="loading === 'oidc'"
      >
        <i class="fas fa-key"></i>
        企业SSO登录
      </el-button>
    </div>
    
    <!-- 手机号登录 -->
    <div v-if="showPhoneLogin" class="phone-login">
      <el-divider>手机号登录</el-divider>
      
      <el-form :model="phoneForm" :rules="phoneRules" ref="phoneFormRef">
        <el-form-item prop="phone">
          <el-input
            v-model="phoneForm.phone"
            placeholder="请输入手机号"
            prefix-icon="Phone"
          />
        </el-form-item>
        
        <el-form-item prop="code">
          <div class="code-input">
            <el-input
              v-model="phoneForm.code"
              placeholder="请输入验证码"
              prefix-icon="Key"
            />
            <el-button
              type="primary"
              :disabled="countdown > 0"
              @click="sendSmsCode"
            >
              {{ countdown > 0 ? `${countdown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            @click="handlePhoneLogin"
            :loading="loading === 'phone'"
            style="width: 100%"
          >
            手机号登录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { oauthApi } from '@/api/oauth'

// Props
interface Props {
  showPhoneLogin?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showPhoneLogin: true
})

// Emits
const emit = defineEmits<{
  success: [data: any]
  error: [error: any]
}>()

// 响应式数据
const loading = ref<string>('')
const providers = ref<string[]>([])
const countdown = ref(0)

// 手机号表单
const phoneForm = reactive({
  phone: '',
  code: ''
})

const phoneFormRef = ref()

// 表单验证规则
const phoneRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

// 获取可用的OAuth提供商
const getOAuthProviders = async () => {
  try {
    const response = await oauthApi.getProviders()
    providers.value = response.data.providers.map((p: any) => p.provider)
  } catch (error) {
    console.error('获取OAuth提供商失败:', error)
  }
}

// 处理OAuth登录
const handleOAuthLogin = async (provider: string) => {
  try {
    loading.value = provider
    
    // 跳转到OAuth授权页面
    const authUrl = `${import.meta.env.VITE_USER_API_BASE_URL}/oauth/${provider}/authorize`
    window.location.href = authUrl
    
  } catch (error) {
    loading.value = ''
    ElMessage.error(`${provider}登录失败`)
    emit('error', error)
  }
}

// 处理OIDC登录
const handleOidcLogin = async () => {
  try {
    loading.value = 'oidc'
    
    // 弹出OIDC配置输入框
    const { value: issuer } = await ElMessageBox.prompt(
      '请输入OIDC发行者URL',
      '企业SSO登录',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^https?:\/\/.+/,
        inputErrorMessage: '请输入有效的URL'
      }
    )
    
    if (issuer) {
      // 验证OIDC配置
      try {
        await oauthApi.discoverOidc(issuer)
        
        // 跳转到OIDC授权页面
        const authUrl = `${import.meta.env.VITE_USER_API_BASE_URL}/oauth/oidc/authorize?issuer=${encodeURIComponent(issuer)}`
        window.location.href = authUrl
        
      } catch (error) {
        ElMessage.error('OIDC配置无效，请检查URL')
      }
    }
    
  } catch (error) {
    loading.value = ''
    if (error !== 'cancel') {
      ElMessage.error('OIDC登录失败')
      emit('error', error)
    }
  }
}

// 发送短信验证码
const sendSmsCode = async () => {
  try {
    if (!phoneForm.phone) {
      ElMessage.warning('请先输入手机号')
      return
    }
    
    // 验证手机号格式
    if (!/^1[3-9]\d{9}$/.test(phoneForm.phone)) {
      ElMessage.error('请输入正确的手机号')
      return
    }
    
    // 调用发送验证码API
    await oauthApi.sendSmsCode(phoneForm.phone)
    
    ElMessage.success('验证码已发送')
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
    
  } catch (error) {
    ElMessage.error('发送验证码失败')
  }
}

// 手机号登录
const handlePhoneLogin = async () => {
  try {
    await phoneFormRef.value.validate()
    
    loading.value = 'phone'
    
    const response = await oauthApi.phoneLogin({
      phone: phoneForm.phone,
      code: phoneForm.code
    })
    
    // 处理登录成功
    const authStore = useAuthStore()
    await authStore.login(response.data)
    
    ElMessage.success('登录成功')
    emit('success', response.data)
    
  } catch (error) {
    loading.value = ''
    ElMessage.error('手机号登录失败')
    emit('error', error)
  }
}

// 组件挂载时获取OAuth提供商
onMounted(() => {
  getOAuthProviders()
})
</script>

<style scoped>
.oauth-login {
  margin-top: 20px;
}

.oauth-title {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.oauth-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.oauth-btn {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.github-btn {
  background-color: #24292e;
  border-color: #24292e;
}

.github-btn:hover {
  background-color: #2f363d;
  border-color: #2f363d;
}

.google-btn {
  background-color: #4285f4;
  border-color: #4285f4;
}

.google-btn:hover {
  background-color: #3367d6;
  border-color: #3367d6;
}

.wechat-btn {
  background-color: #07c160;
  border-color: #07c160;
}

.wechat-btn:hover {
  background-color: #06ad56;
  border-color: #06ad56;
}

.alipay-btn {
  background-color: #1677ff;
  border-color: #1677ff;
}

.alipay-btn:hover {
  background-color: #0958d9;
  border-color: #0958d9;
}

.oidc-btn {
  background-color: #909399;
  border-color: #909399;
}

.oidc-btn:hover {
  background-color: #84868a;
  border-color: #84868a;
}

.phone-login {
  margin-top: 20px;
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
</style> 