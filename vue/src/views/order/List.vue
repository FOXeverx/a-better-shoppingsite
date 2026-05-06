<template>
  <div class="order-list-page container">
    <div class="page-header">
      <h1>我的订单</h1>
    </div>
    
    <div class="tabs-wrapper">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="待确认" name="CREATED" />
        <el-tab-pane label="已确认" name="CONFIRMED" />
        <el-tab-pane label="已完成" name="COMPLETED" />
        <el-tab-pane label="已取消" name="CANCELLED" />
      </el-tabs>
    </div>
    
    <Loading v-if="loading" />
    
    <template v-else>
      <div class="order-list" v-if="orders.length > 0">
        <div class="order-card" v-for="order in orders" :key="order.id">
          <div class="order-header">
            <div class="order-info">
              <span class="order-number">订单号: {{ order.order_number }}</span>
              <span class="order-time">{{ formatDate(order.created_at) }}</span>
            </div>
            <div class="order-status">
              <el-tag :type="getStatusType(order.status)">
                {{ getStatusText(order.status) }}
              </el-tag>
            </div>
          </div>
          
          <div class="order-body">
            <div class="order-items">
              <div class="item" v-for="item in order.items" :key="item.product_id">
                <img v-if="item.image_url" :src="item.image_url" :alt="item.product_name" />
                <div class="item-info">
                  <h4>{{ item.product_name }}</h4>
                  <p>¥{{ item.price }} x {{ item.quantity }}</p>
                </div>
              </div>
            </div>
            <div class="order-total">
              <span class="label">合计:</span>
              <span class="amount">¥{{ order.total_amount?.toFixed(2) || '0.00' }}</span>
            </div>
          </div>
          
          <div class="order-footer">
            <el-button type="primary" size="small" @click="goToDetail(order.id)">
              查看详情
            </el-button>
            <el-button
              v-if="order.status === 'CREATED'"
              type="danger"
              size="small"
              @click="handleCancel(order.id)"
            >
              取消订单
            </el-button>
          </div>
        </div>
      </div>
      
      <Empty v-else text="暂无订单" />
      
      <div class="pagination-wrapper" v-if="pagination.total > 0">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchOrders"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOrderList, cancelOrder } from '@/api/order'
import type { Order, OrderStatus } from '@/types/order'

const router = useRouter()

const orders = ref<Order[]>([])
const loading = ref(false)
const activeTab = ref('all')

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

async function fetchOrders() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (activeTab.value !== 'all') {
      params.status = activeTab.value
    }
    
    const res = await getOrderList(params)
    console.log('Order list response:', res)
    if (res.success) {
      orders.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total || 0
      }
    }
  } catch (error) {
    console.error('Failed to load orders:', error)
  } finally {
    loading.value = false
  }
}

function handleTabChange() {
  pagination.page = 1
  fetchOrders()
}

function goToDetail(id: number) {
  router.push(`/order/${id}`)
}

async function handleCancel(orderId: number) {
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await cancelOrder(orderId)
    if (res.success) {
      ElMessage.success('订单已取消')
      fetchOrders()
    }
  } catch {
    // User cancelled
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function getStatusType(status: OrderStatus) {
  const map: Record<OrderStatus, string> = {
    CREATED: 'warning',
    CONFIRMED: 'success',
    SHIPPED: 'info',
    COMPLETED: 'success',
    CANCELLED: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status: OrderStatus) {
  const map: Record<OrderStatus, string> = {
    CREATED: '待确认',
    CONFIRMED: '已确认',
    SHIPPED: '配送中',
    COMPLETED: '已完成',
    CANCELLED: '已取消'
  }
  return map[status] || status
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped lang="scss">
.order-list-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.tabs-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 0 16px;
  margin-bottom: 20px;
}

.order-list {
  .order-card {
    background: #fff;
    border-radius: 8px;
    margin-bottom: 16px;
    overflow: hidden;
  }
  
  .order-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    background: #f5f7fa;
    
    .order-info {
      .order-number {
        font-weight: 600;
        margin-right: 16px;
      }
      
      .order-time {
        color: #909399;
        font-size: 13px;
      }
    }
  }
  
  .order-body {
    display: flex;
    padding: 16px;
    
    .order-items {
      flex: 1;
      
      .item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        
        img {
          width: 50px;
          height: 50px;
          border-radius: 4px;
          object-fit: cover;
          margin-right: 12px;
        }
        
        .item-info {
          h4 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 4px;
          }
          
          p {
            font-size: 13px;
            color: #909399;
          }
        }
      }
    }
    
    .order-total {
      width: 150px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: flex-end;
      
      .label {
        font-size: 14px;
        color: #606266;
      }
      
      .amount {
        font-size: 20px;
        font-weight: 700;
        color: #f56c6c;
      }
    }
  }
  
  .order-footer {
    padding: 16px;
    border-top: 1px solid #f0f0f0;
    text-align: right;
  }
}

.pagination-wrapper {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}
</style>