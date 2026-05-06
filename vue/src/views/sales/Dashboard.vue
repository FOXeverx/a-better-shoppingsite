<template>
  <div class="dashboard-page">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #409eff">
          <el-icon :size="30"><ShoppingCart /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_orders }}</div>
          <div class="stat-label">总订单数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" style="background: #67c23a">
          <el-icon :size="30"><Money /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">¥{{ stats.total_amount?.toFixed(2) || '0.00' }}</div>
          <div class="stat-label">总销售额</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" style="background: #e6a23c">
          <el-icon :size="30"><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_users }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
    </div>
    
    <div class="chart-section">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>销售趋势</span>
            <el-select v-model="period" @change="fetchStats" size="small">
              <el-option label="日报" value="daily" />
              <el-option label="周报" value="weekly" />
              <el-option label="月报" value="monthly" />
            </el-select>
          </div>
        </template>
        <div ref="chartRef" class="chart-container"></div>
      </el-card>
    </div>
    
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="actions-grid">
        <div class="action-item" @click="$router.push('/sales/products')">
          <el-icon :size="32"><Goods /></el-icon>
          <span>商品管理</span>
        </div>
        <div class="action-item" @click="$router.push('/sales/orders')">
          <el-icon :size="32"><ShoppingCart /></el-icon>
          <span>订单管理</span>
        </div>
        <div class="action-item" @click="$router.push('/sales/stats')">
          <el-icon :size="32"><DataAnalysis /></el-icon>
          <span>销售统计</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ShoppingCart, Money, User, Goods, DataAnalysis } from '@element-plus/icons-vue'
import { getStats } from '@/api/admin'
import type { AdminStats } from '@/types/admin'

const period = ref('daily')
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const stats = reactive<AdminStats>({
  total_amount: 0,
  total_orders: 0,
  total_users: 0,
  trend: []
})

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance) return
  
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
  chartInstance.setOption(option)
}

async function fetchStats() {
  try {
    const res = await getStats({ period: period.value as any })
    if (res.success && res.data) {
      stats.total_amount = res.data.total_amount
      stats.total_orders = res.data.total_orders
      stats.total_users = res.data.total_users
      stats.trend = res.data.trend || []
      
      await nextTick()
      if (chartInstance) {
        updateChart()
      } else {
        initChart()
      }
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', () => chartInstance?.resize())
})
</script>

<style scoped lang="scss">
.dashboard-page {
  .stats-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 30px;
  }
  
  .stat-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
    }
    
    .stat-info {
      .stat-value {
        font-size: 24px;
        font-weight: 700;
        color: #303133;
      }
      
      .stat-label {
        font-size: 14px;
        color: #909399;
        margin-top: 4px;
      }
    }
  }
  
  .chart-section {
    margin-bottom: 30px;
    
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .chart-container {
      width: 100%;
      height: 350px;
    }
  }
  
  .quick-actions {
    h3 {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
    }
    
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      
      .action-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 12px;
        padding: 20px;
        border-radius: 8px;
        background: #f5f7fa;
        cursor: pointer;
        transition: all 0.3s;
        
        &:hover {
          background: #ecf5ff;
          color: #409eff;
        }
        
        span {
          font-size: 14px;
        }
      }
    }
  }
}
</style>