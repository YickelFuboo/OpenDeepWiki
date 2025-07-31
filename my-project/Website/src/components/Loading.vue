<template>
  <div class="loading-container" v-if="loading">
    <div class="loading-spinner">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <p class="loading-text">{{ text }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading?: boolean
  text?: string
}

withDefaults(defineProps<Props>(), {
  loading: false,
  text: '加载中...'
})
</script>

<style scoped>
.loading-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-spinner {
  text-align: center;
}

.loading-spinner .el-icon {
  font-size: 32px;
  color: #409eff;
  margin-bottom: 16px;
}

.loading-text {
  color: #666;
  font-size: 14px;
  margin: 0;
}
</style> 