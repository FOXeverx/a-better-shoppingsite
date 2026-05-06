<template>
  <div class="analysis-page">
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">用户总数</div>
            <div class="stat-value">{{ userStats.total_users }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">平均消费</div>
            <div class="stat-value">¥{{ userStats.avg_spent?.toFixed(2) || '0.00' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">异常总数</div>
            <div class="stat-value">{{ anomalyStats.total }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">待处理异常</div>
            <div class="stat-value warning">{{ anomalyStats.unresolved }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>用户消费分布</span>
          </template>
          <div ref="spendingChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>用户地域分布</span>
          </template>
          <div ref="regionChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>销售趋势预测</span>
          </template>
          <div ref="predictChartRef" class="chart-container"></div>
          <div class="predict-info">
            <el-tag v-if="prediction.trend === 'increasing'" type="success">上升趋势</el-tag>
            <el-tag v-else-if="prediction.trend === 'decreasing'" type="danger">下降趋势</el-tag>
            <el-tag v-else type="info">稳定</el-tag>
            <span class="confidence">预测可信度: {{ prediction.confidence }}%</span>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>异常告警监控</span>
          </template>
          <div class="anomaly-summary">
            <div class="anomaly-item high">
              <span class="count">{{ anomalyStats.by_severity?.high || 0 }}</span>
              <span class="label">高危</span>
            </div>
            <div class="anomaly-item medium">
              <span class="count">{{ anomalyStats.by_severity?.medium || 0 }}</span>
              <span class="label">中危</span>
            </div>
            <div class="anomaly-item low">
              <span class="count">{{ anomalyStats.by_severity?.low || 0 }}</span>
              <span class="label">低危</span>
            </div>
          </div>
          <el-button type="primary" size="small" @click="refreshAnomalies">刷新监控</el-button>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getUserStats, getAnomalyStats, getSalesPrediction } from '@/api/admin'

const spendingChartRef = ref<HTMLElement>()
const regionChartRef = ref<HTMLElement>()
const predictChartRef = ref<HTMLElement>()
let spendingChart: echarts.ECharts | null = null
let regionChart: echarts.ECharts | null = null
let predictChart: echarts.ECharts | null = null

const userStats = reactive({
  total_users: 0,
  spending_distribution: { low: 0, medium: 0, high: 0 },
  avg_spent: 0,
  avg_orders: 0,
  region_distribution: {} as Record<string, number>
})

const anomalyStats = reactive({
  total: 0,
  unresolved: 0,
  by_severity: { high: 0, medium: 0, low: 0 },
  last_24h: 0
})

const prediction = reactive({
  trend: '',
  current_avg: 0,
  prediction: 0,
  confidence: 0,
  recent_data: [] as { date: string; amount: number }[]
})

function initSpendingChart() {
  if (!spendingChartRef.value) return
  spendingChart = echarts.init(spendingChartRef.value)
  updateSpendingChart()
}

function updateSpendingChart() {
  if (!spendingChart) return
  
  const data = [
    { value: userStats.spending_distribution.low, name: '低消费' },
    { value: userStats.spending_distribution.medium, name: '中等消费' },
    { value: userStats.spending_distribution.high, name: '高消费' }
  ]
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: data,
      label: { formatter: '{b}: {c} ({d}%)' }
    }]
  }
  spendingChart.setOption(option)
}

function initRegionChart() {
  if (!regionChartRef.value) return
  regionChart = echarts.init(regionChartRef.value)
  updateRegionChart()
}

function updateRegionChart() {
  if (!regionChart) return
  
  const regions = Object.keys(userStats.region_distribution)
  const values = Object.values(userStats.region_distribution)
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: regions, axisLabel: { rotate: 30 } },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: values, itemStyle: { color: '#409eff' } }]
  }
  regionChart.setOption(option)
}

function initPredictChart() {
  if (!predictChartRef.value) return
  predictChart = echarts.init(predictChartRef.value)
  updatePredictChart()
}

function updatePredictChart() {
  if (!predictChart || !prediction.recent_data.length) return
  
  const dates = prediction.recent_data.map(d => d.date.split('T')[0])
  const amounts = prediction.recent_data.map(d => d.amount)
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', axisLabel: { formatter: '¥{value}' } },
    series: [{
      type: 'line',
      data: amounts,
      smooth: true,
      itemStyle: { color: '#67c23a' },
      areaStyle: { color: 'rgba(103, 194, 58, 0.1)' },
      markPoint: {
        data: [
          { type: 'max', name: '最高' },
          { type: 'min', name: '最低' }
        ]
      }
    }]
  }
  predictChart.setOption(option)
}

async function fetchData() {
  try {
    const userRes = await getUserStats()
    if (userRes.success && userRes.data) {
      userStats.total_users = userRes.data.total_users
      userStats.spending_distribution = userRes.data.spending_distribution
      userStats.avg_spent = userRes.data.avg_spent
      userStats.avg_orders = userRes.data.avg_orders
      userStats.region_distribution = userRes.data.region_distribution
    }
    
    const anomalyRes = await getAnomalyStats()
    if (anomalyRes.success && anomalyRes.data) {
      anomalyStats.total = anomalyRes.data.total
      anomalyStats.unresolved = anomalyRes.data.unresolved
      anomalyStats.by_severity = anomalyRes.data.by_severity
      anomalyStats.last_24h = anomalyRes.data.last_24h
    }
    
    const predictRes = await getSalesPrediction()
    if (predictRes.success && predictRes.data) {
      prediction.trend = predictRes.data.trend
      prediction.current_avg = predictRes.data.current_avg
      prediction.prediction = predictRes.data.prediction
      prediction.confidence = predictRes.data.confidence
      prediction.recent_data = predictRes.data.recent_data || []
    }
    
    await nextTick()
    if (!spendingChart) initSpendingChart()
    else updateSpendingChart()
    if (!regionChart) initRegionChart()
    else updateRegionChart()
    if (!predictChart) initPredictChart()
    else updatePredictChart()
  } catch (error) {
    console.error('Failed to load analysis data:', error)
  }
}

function refreshAnomalies() {
  fetchData()
}

onMounted(() => {
  fetchData()
  window.addEventListener('resize', () => {
    spendingChart?.resize()
    regionChart?.resize()
    predictChart?.resize()
  })
})
</script>

<style scoped lang="scss">
.analysis-page {
  .stats-row {
    margin-bottom: 20px;
  }
  
  .el-card {
    margin-bottom: 20px;
  }
  
  .stat-item {
    text-align: center;
    
    .stat-label {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }
    
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #303133;
      
      &.warning {
        color: #f56c6c;
      }
    }
  }
  
  .chart-container {
    width: 100%;
    height: 250px;
  }
  
  .predict-info {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 12px;
    
    .confidence {
      font-size: 13px;
      color: #909399;
    }
  }
  
  .anomaly-summary {
    display: flex;
    justify-content: space-around;
    margin-bottom: 16px;
    
    .anomaly-item {
      text-align: center;
      padding: 12px;
      border-radius: 8px;
      
      .count {
        display: block;
        font-size: 28px;
        font-weight: 700;
      }
      
      .label {
        font-size: 13px;
        color: #909399;
      }
      
      &.high {
        background: #fef0f0;
        .count { color: #f56c6c; }
      }
      
      &.medium {
        background: #fdf6ec;
        .count { color: #e6a23c; }
      }
      
      &.low {
        background: #f0f9eb;
        .count { color: #67c23a; }
      }
    }
  }
}
</style>