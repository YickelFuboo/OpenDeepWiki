<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <el-icon :size="24">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-title">{{ stat.title }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 图表区域 -->
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>仓库统计</span>
          </template>
          <div ref="repositoryChart" style="height: 300px;"></div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.time"
              :type="activity.type"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 快速操作 -->
      <el-col :span="24">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="6" v-for="action in quickActions" :key="action.title">
              <el-button
                :type="action.type"
                :icon="action.icon"
                size="large"
                class="quick-action-btn"
                @click="handleQuickAction(action.action)"
              >
                {{ action.title }}
              </el-button>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'

const router = useRouter()

// 统计数据
const stats = ref([
  {
    title: '总仓库数',
    value: '12',
    icon: 'Folder',
    color: '#409eff'
  },
  {
    title: '总文档数',
    value: '156',
    icon: 'Document',
    color: '#67c23a'
  },
  {
    title: '活跃用户',
    value: '8',
    icon: 'User',
    color: '#e6a23c'
  },
  {
    title: 'AI对话',
    value: '89',
    icon: 'ChatDotRound',
    color: '#f56c6c'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    content: '用户 admin 创建了新仓库 "my-project"',
    time: '2024-07-29 10:30',
    type: 'primary'
  },
  {
    id: 2,
    content: '仓库 "vue-admin" 文档生成完成',
    time: '2024-07-29 09:15',
    type: 'success'
  },
  {
    id: 3,
    content: '用户 john 登录系统',
    time: '2024-07-29 08:45',
    type: 'info'
  },

])

// 快速操作
const quickActions = ref([
  {
    title: '添加仓库',
    icon: 'Plus',
    type: 'primary',
    action: 'addRepository'
  },
  {
    title: 'AI对话',
    icon: 'ChatDotRound',
    type: 'success',
    action: 'chat'
  },
  {
    title: '生成文档',
    icon: 'Document',
    type: 'warning',
    action: 'generateDoc'
  },

])

// 图表引用
const repositoryChart = ref()

// 处理快速操作
const handleQuickAction = (action: string) => {
  switch (action) {
    case 'addRepository':
      router.push('/repositories')
      break
    case 'chat':
      router.push('/chat')
      break
    case 'generateDoc':
      router.push('/documents')
      break

  }
}

// 初始化图表
onMounted(() => {
  const chart = echarts.init(repositoryChart.value)
  
  const option = {
    title: {
      text: '仓库状态分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '仓库状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 8, name: '已完成' },
          { value: 3, name: '处理中' },
          { value: 1, name: '失败' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  chart.setOption(option)
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-title {
  font-size: 14px;
  color: #666;
}

.quick-action-btn {
  width: 100%;
  height: 60px;
  font-size: 16px;
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .el-col {
    margin-bottom: 10px;
  }
  
  .stat-content {
    flex-direction: column;
    text-align: center;
  }
  
  .stat-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
}
</style> 