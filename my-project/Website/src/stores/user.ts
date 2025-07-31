import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'

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

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  const login = async (username: string, password: string) => {
    try {
      loading.value = true
      const response = await authApi.login({ username, password })
      if (response.success) {
        token.value = response.data.access_token
        localStorage.setItem('token', response.data.access_token)
        await getUserInfo()
        return { success: true }
      }
      return { success: false, message: response.message }
    } catch (error: any) {
      return { success: false, message: error.message }
    } finally {
      loading.value = false
    }
  }

  const register = async (userData: { username: string; email: string; password: string; full_name: string }) => {
    try {
      loading.value = true
      const response = await authApi.register(userData)
      return { success: response.success, message: response.message }
    } catch (error: any) {
      return { success: false, message: error.message }
    } finally {
      loading.value = false
    }
  }

  const getUserInfo = async () => {
    try {
      const response = await authApi.getCurrentUser()
      if (response.success) {
        user.value = response.data
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  const initUser = async () => {
    if (token.value) {
      await getUserInfo()
    }
  }

  const changePassword = async (oldPassword: string, newPassword: string) => {
    try {
      loading.value = true
      const response = await authApi.changePassword({ old_password: oldPassword, new_password: newPassword })
      return { success: response.success, message: response.message }
    } catch (error: any) {
      return { success: false, message: error.message }
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    token,
    loading,
    login,
    register,
    logout,
    getUserInfo,
    initUser,
    changePassword
  }
}) 