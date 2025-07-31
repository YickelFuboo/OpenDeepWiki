<template>
  <div class="mermaid-container">
    <div ref="mermaidRef" class="mermaid"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import mermaid from 'mermaid'

interface Props {
  chart: string
  theme?: 'default' | 'forest' | 'dark' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  theme: 'default'
})

const mermaidRef = ref<HTMLElement>()

onMounted(() => {
  // 配置mermaid
  mermaid.initialize({
    startOnLoad: false,
    theme: props.theme,
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true
    },
    sequence: {
      useMaxWidth: true
    },
    gantt: {
      useMaxWidth: true
    }
  })
  
  renderChart()
})

watch(() => props.chart, () => {
  renderChart()
})

const renderChart = async () => {
  if (!mermaidRef.value || !props.chart) return
  
  try {
    // 清空容器
    mermaidRef.value.innerHTML = ''
    
    // 渲染图表
    const { svg } = await mermaid.render('mermaid-chart', props.chart)
    mermaidRef.value.innerHTML = svg
  } catch (error) {
    console.error('Mermaid rendering error:', error)
    mermaidRef.value.innerHTML = '<p class="error">图表渲染失败</p>'
  }
}
</script>

<style scoped>
.mermaid-container {
  width: 100%;
  overflow-x: auto;
  margin: 16px 0;
}

.mermaid {
  text-align: center;
}

.error {
  color: #f56c6c;
  text-align: center;
  padding: 20px;
}
</style> 