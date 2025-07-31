import { ref, watch } from 'vue'

export function useDebounce<T>(value: T, delay: number = 300) {
  const debouncedValue = ref<T>(value)

  let timeoutId: NodeJS.Timeout

  watch(value, (newValue) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })

  return debouncedValue
} 