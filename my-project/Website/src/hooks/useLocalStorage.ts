import { ref, watch } from 'vue'

export function useLocalStorage<T>(key: string, defaultValue: T) {
  const storedValue = localStorage.getItem(key)
  const value = ref<T>(storedValue ? JSON.parse(storedValue) : defaultValue)

  const setValue = (newValue: T) => {
    value.value = newValue
    localStorage.setItem(key, JSON.stringify(newValue))
  }

  const removeValue = () => {
    value.value = defaultValue
    localStorage.removeItem(key)
  }

  // 监听值变化，自动同步到localStorage
  watch(value, (newValue) => {
    localStorage.setItem(key, JSON.stringify(newValue))
  }, { deep: true })

  return {
    value,
    setValue,
    removeValue
  }
} 