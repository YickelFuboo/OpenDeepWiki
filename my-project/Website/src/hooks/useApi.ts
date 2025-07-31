import { ref, computed } from 'vue'
import type { ApiResponse } from '@/api'

export function useApi<T = any>() {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const hasData = computed(() => data.value !== null)
  const hasError = computed(() => error.value !== null)

  const execute = async (apiCall: () => Promise<ApiResponse<T>>) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await apiCall()
      if (response.success) {
        data.value = response.data
      } else {
        error.value = response.message || '请求失败'
      }
    } catch (err: any) {
      error.value = err.message || '网络错误'
    } finally {
      loading.value = false
    }
  }

  const reset = () => {
    data.value = null
    loading.value = false
    error.value = null
  }

  return {
    data,
    loading,
    error,
    hasData,
    hasError,
    execute,
    reset
  }
} 