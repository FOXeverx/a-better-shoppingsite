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
            <div class="card-header-row">
              <span>异常告警监控</span>
              <span class="header-extra">近24h: {{ anomalyStats.last_24h }}</span>
            </div>
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
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header-row">
              <span>异常列表</span>
              <div class="header-actions">
                <el-checkbox v-model="showUnresolvedOnly" @change="fetchAnomalies">
                  仅看未处理
                </el-checkbox>
                <el-button size="small" @click="fetchAnomalies">刷新</el-button>
              </div>
            </div>
          </template>
          <el-table :data="anomalyList" v-loading="anomalyLoading" stripe empty-text="暂无异常记录">
            <el-table-column prop="anomaly_type" label="类型" width="140">
              <template #default="{ row }">
                <el-tag size="small" :type="anomalyTypeTag(row.anomaly_type)">{{ anomalyTypeLabel(row.anomaly_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="异常描述" min-width="260" show-overflow-tooltip />
            <el-table-column prop="severity" label="严重程度" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="severityTag(row.severity)" size="small">{{ severityLabel(row.severity) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="发生时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="is_resolved" label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_resolved ? 'success' : 'danger'" size="small">
                  {{ row.is_resolved ? '已处理' : '未处理' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" fixed="right" align="center">
              <template #default="{ row }">
                <el-popconfirm
                  v-if="!row.is_resolved && isAdmin"
                  title="确认处理此异常？"
                  @confirm="handleResolve(row.id)"
                >
                  <template #reference>
                    <el-button type="primary" size="small">处理</el-button>
                  </template>
                </el-popconfirm>
                <el-tag v-else-if="!row.is_resolved" type="danger" size="small">未处理</el-tag>
                <el-button v-else size="small" disabled>已处理</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="anomalyTotal > anomalyPageSize" class="pagination-wrapper">
            <el-pagination
              v-model:current-page="anomalyPage"
              v-model:page-size="anomalyPageSize"
              :total="anomalyTotal"
              layout="total, prev, pager, next"
              @current-change="fetchAnomalies"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getUserStats, getAnomalyStats, getSalesPrediction, getAnomalies, resolveAnomaly } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import type { Anomaly } from '@/types/admin'

const authStore = useAuthStore()
const isAdmin = authStore.isAdmin

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

const anomalyList = ref<Anomaly[]>([])
const anomalyLoading = ref(false)
const anomalyPage = ref(1)
const anomalyPageSize = ref(10)
const anomalyTotal = ref(0)
const showUnresolvedOnly = ref(true)

function formatTime(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { hour12: false })
}

function severityLabel(severity: string) {
  const map: Record<string, string> = { high: '高危', medium: '中危', low: '低危' }
  return map[severity] || severity
}

function severityTag(severity: string) {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return map[severity] || 'info'
}

function anomalyTypeLabel(type: string) {
  const map: Record<string, string> = {
    large_order: '大额订单',
    login_failures: '登录失败',
    low_stock: '库存不足'
  }
  return map[type] || type
}

function anomalyTypeTag(type: string) {
  const map: Record<string, string> = {
    large_order: 'warning',
    login_failures: 'danger',
    low_stock: ''
  }
  return map[type] || ''
}

async function fetchAnomalies() {
  anomalyLoading.value = true
  try {
    const res = await getAnomalies({
      page: anomalyPage.value,
      page_size: anomalyPageSize.value,
      is_resolved: showUnresolvedOnly.value ? false : undefined
    })
    if (res.success) {
      anomalyList.value = (res.data || []) as Anomaly[]
      if (res.pagination) {
        anomalyTotal.value = res.pagination.total
      }
    }
  } catch (error) {
    console.error('Failed to load anomalies:', error)
  } finally {
    anomalyLoading.value = false
  }
}

async function handleResolve(id: number) {
  try {
    const res = await resolveAnomaly(id)
    if (res.success) {
      fetchAnomalies()
      fetchAnomalyStats()
    }
  } catch (error) {
    console.error('Failed to resolve anomaly:', error)
  }
}

async function fetchAnomalyStats() {
  try {
    const res = await getAnomalyStats()
    if (res.success && res.data) {
      anomalyStats.total = res.data.total
      anomalyStats.unresolved = res.data.unresolved
      anomalyStats.by_severity = res.data.by_severity
      anomalyStats.last_24h = res.data.last_24h
    }
  } catch (error) {
    console.error('Failed to load anomaly stats:', error)
  }
}

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
    
    await fetchAnomalyStats()
    
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

onMounted(() => {
  fetchData()
  fetchAnomalies()
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

  .card-header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .header-extra {
    font-size: 12px;
    color: #909399;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .pagination-wrapper {
    margin-top: 16px;
    display: flex;
    justify-content: center;
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