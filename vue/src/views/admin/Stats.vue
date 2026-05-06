<template>
  <div class="admin-stats-page">
    <div class="filter-section">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="handleDateChange"
      />
      <el-select v-model="period" @change="fetchStats">
        <el-option label="日报" value="daily" />
        <el-option label="周报" value="weekly" />
        <el-option label="月报" value="monthly" />
      </el-select>
    </div>
    
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">总销售额</div>
            <div class="stat-value">¥{{ stats.total_amount?.toFixed(2) || '0.00' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">总订单数</div>
            <div class="stat-value">{{ stats.total_orders }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">总用户数</div>
            <div class="stat-value">{{ stats.total_users }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">平均订单金额</div>
            <div class="stat-value">¥{{ avgOrderAmount.toFixed(2) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>销售趋势</span>
          </template>
          <div ref="trendChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>商品销售排行</span>
          </template>
          <div ref="productChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getStats, getProductSales } from '@/api/admin'
import type { AdminStats, ProductSales } from '@/types/admin'

const period = ref('daily')
const dateRange = ref<[Date, Date] | null>(null)
const trendChartRef = ref<HTMLElement>()
const productChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let productChart: echarts.ECharts | null = null

const stats = reactive<AdminStats>({
  total_amount: 0,
  total_orders: 0,
  total_users: 0,
  trend: []
})

const productSales = ref<ProductSales[]>([])

const avgOrderAmount = computed(() => {
  if (!stats.total_orders) return 0
  return stats.total_amount / stats.total_orders
})

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()
}

function updateTrendChart() {
  if (!trendChart) return
  
  const dates = stats.trend.map(t => t.date)
  const orders = stats.trend.map(t => t.orders)
  const amounts = stats.trend.map(t => t.amount)
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['订单数', '销售额'] },
    xAxis: { type: 'category', data: dates, boundaryGap: false },
    yAxis: [
      { type: 'value', name: '订单数', position: 'left' },
      { type: 'value', name: '销售额(元)', position: 'right', axisLabel: { formatter: '¥{value}' } }
    ],
    series: [
      { name: '订单数', type: 'line', data: orders, smooth: true, itemStyle: { color: '#409eff' }, areaStyle: { color: 'rgba(64, 158, 255, 0.1)' } },
      { name: '销售额', type: 'line', yAxisIndex: 1, data: amounts, smooth: true, itemStyle: { color: '#67c23a' }, areaStyle: { color: 'rgba(103, 194, 58, 0.1)' } }
    ]
  }
  trendChart.setOption(option)
}

function initProductChart() {
  if (!productChartRef.value) return
  productChart = echarts.init(productChartRef.value)
  updateProductChart()
}

function updateProductChart() {
  if (!productChart || !productSales.value.length) return
  
  const names = productSales.value.map(p => p.product_name)
  const revenues = productSales.value.map(p => p.revenue)
  const quantities = productSales.value.map(p => p.quantity)
  
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']
  
  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['销售额', '销量'] },
    xAxis: { type: 'category', data: names, axisLabel: { rotate: 30 } },
    yAxis: [
      { type: 'value', name: '销售额(元)', axisLabel: { formatter: '¥{value}' } },
      { type: 'value', name: '销量' }
    ],
    series: [
      { name: '销售额', type: 'bar', data: revenues, itemStyle: { color: '#409eff' } },
      { name: '销量', type: 'line', yAxisIndex: 1, data: quantities, smooth: true, itemStyle: { color: '#e6a23c' } }
    ]
  }
  productChart.setOption(option)
}

function handleDateChange() {
  fetchStats()
}

async function fetchStats() {
  try {
    const params: any = { period: period.value }
    if (dateRange.value) {
      params.start_date = dateRange.value[0].toISOString().split('T')[0]
      params.end_date = dateRange.value[1].toISOString().split('T')[0]
    }
    
    const res = await getStats(params)
    if (res.success && res.data) {
      stats.total_amount = res.data.total_amount
      stats.total_orders = res.data.total_orders
      stats.total_users = res.data.total_users
      stats.trend = res.data.trend || []
      
      await nextTick()
      if (trendChart) {
        updateTrendChart()
      } else {
        initTrendChart()
      }
    }
    
    const salesRes = await getProductSales(params)
    if (salesRes.success && salesRes.data) {
      productSales.value = salesRes.data
      
      await nextTick()
      if (productChart) {
        updateProductChart()
      } else {
        initProductChart()
      }
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', () => {
    trendChart?.resize()
    productChart?.resize()
  })
})
</script>

<style scoped lang="scss">
.admin-stats-page {
  .filter-section {
    margin-bottom: 20px;
    display: flex;
    gap: 16px;
  }
  
  .stats-row {
    margin-bottom: 20px;
    
    .el-card {
      text-align: center;
    }
    
    .stat-item {
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-bottom: 8px;
      }
      
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: #303133;
      }
    }
  }
  
  .chart-container {
    width: 100%;
    height: 400px;
  }
}
</style>