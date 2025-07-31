import request from '@/utils/request'

export const oauthApi = {
  // 获取OAuth提供商列表
  getProviders() {
    return request.get('/api/v1/oauth/providers')
  },

  // OAuth登录回调
  oauthCallback(provider: string, data: any) {
    return request.post(`/api/v1/oauth/${provider}/callback`, data)
  },

  // OIDC登录回调
  oidcCallback(data: any) {
    return request.post('/api/v1/oauth/oidc/callback', data)
  },

  // 发现OIDC配置
  discoverOidc(issuer: string) {
    return request.get(`/api/v1/oauth/oidc/discover/${encodeURIComponent(issuer)}`)
  },

  // 绑定OAuth账号
  bindOAuthAccount(provider: string, data: any) {
    return request.post(`/api/v1/oauth/${provider}/bind`, data)
  },

  // 解绑OAuth账号
  unbindOAuthAccount(provider: string, userId: string) {
    return request.delete(`/api/v1/oauth/${provider}/unbind?user_id=${userId}`)
  },

  // 发送短信验证码
  sendSmsCode(phone: string) {
    return request.post('/api/v1/auth/send-sms-code', { phone })
  },

  // 手机号登录
  phoneLogin(data: { phone: string; code: string }) {
    return request.post('/api/v1/auth/phone-login', data)
  },

  // 邮箱验证码登录
  emailLogin(data: { email: string; code: string }) {
    return request.post('/api/v1/auth/email-login', data)
  },

  // 发送邮箱验证码
  sendEmailCode(email: string) {
    return request.post('/api/v1/auth/send-email-code', { email })
  }
} 