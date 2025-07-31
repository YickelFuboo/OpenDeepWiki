<template>
  <div v-if="hasPermission">
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

interface Props {
  permission?: string
  role?: string
}

const props = withDefaults(defineProps<Props>(), {
  permission: '',
  role: ''
})

const userStore = useUserStore()

const hasPermission = computed(() => {
  if (!userStore.user) {
    return false
  }
  
  // 检查角色权限
  if (props.role && userStore.user.role !== props.role) {
    return false
  }
  
  // 检查具体权限
  if (props.permission) {
    // 这里可以根据实际权限系统进行扩展
    return true
  }
  
  return true
})
</script> 