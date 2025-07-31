<template>
  <div ref="chartRef" class="chart-container" :style="{ height: height }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'

interface Props {
  option: EChartsOption
  height?: string
  theme?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  theme: 'default'
})

const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value, props.theme)
    chartInstance.setOption(props.option)
    
    // 监听窗口大小变化
    window.addEventListener('resize', handleResize)
  }
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

watch(() => props.option, (newOption) => {
  if (chartInstance) {
    chartInstance.setOption(newOption, true)
  }
}, { deep: true })

const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}
</script>

<style scoped>
.chart-container {
  width: 100%;
}
</style> 