<template>
  <div v-if="error" class="error-boundary">
    <el-result
      icon="error"
      title="页面出错了"
      :sub-title="error.message"
    >
      <template #extra>
        <el-button type="primary" @click="handleRetry">
          重试
        </el-button>
        <el-button @click="handleGoHome">
          返回首页
        </el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref<Error | null>(null)

onErrorCaptured((err: Error) => {
  error.value = err
  console.error('Error caught by boundary:', err)
  return false
})

const handleRetry = () => {
  error.value = null
  window.location.reload()
}

const handleGoHome = () => {
  error.value = null
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  padding: 40px;
  text-align: center;
}
</style> 