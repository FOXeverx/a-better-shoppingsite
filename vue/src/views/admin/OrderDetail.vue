<template>
  <div class="order-detail-page container">
    <div class="page-header">
      <el-button text @click="$router.push('/admin/orders')">
        <el-icon><ArrowLeft /></el-icon>
        返回订单列表
      </el-button>
      <h1>订单详情</h1>
    </div>
    
    <Loading :loading="loading" text="加载中..." />
    
    <template v-if="!loading && order">
      <div class="order-info-card">
        <div class="info-header">
          <div class="order-number">订单号: {{ order.order_number }}</div>
          <el-tag :type="getStatusType(order.status)">
            {{ getStatusText(order.status) }}
          </el-tag>
        </div>
        
        <div class="info-row">
          <span class="label">用户名:</span>
          <span>{{ order.username }}</span>
        </div>
        <div class="info-row">
          <span class="label">下单时间:</span>
          <span>{{ formatDate(order.created_at) }}</span>
        </div>
        <div class="info-row" v-if="order.confirmed_at">
          <span class="label">确认时间:</span>
          <span>{{ formatDate(order.confirmed_at) }}</span>
        </div>
        <div class="info-row" v-if="order.shipping_address">
          <span class="label">收货地址:</span>
          <span>{{ order.shipping_address }}</span>
        </div>
        <div class="info-row" v-if="order.note">
          <span class="label">订单备注:</span>
          <span>{{ order.note }}</span>
        </div>
      </div>
      
      <div class="items-card">
        <h3>商品信息</h3>
        <div class="item-list">
          <div class="order-item" v-for="item in order.items" :key="item.product_id">
            <div class="item-info">
              <h4>{{ item.product_name }}</h4>
              <p>单价: ¥{{ item.price.toFixed(2) }}</p>
            </div>
            <div class="item-quantity">x{{ item.quantity }}</div>
            <div class="item-subtotal">¥{{ item.subtotal.toFixed(2) }}</div>
          </div>
        </div>
        
        <div class="total-section">
          <div class="total-row">
            <span>商品总数:</span>
            <span>{{ totalItems }}</span>
          </div>
          <div class="total-row">
            <span>订单金额:</span>
            <span class="amount">¥{{ order.total_amount.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getOrderDetail } from '@/api/admin'
import Loading from '@/components/common/Loading.vue'

interface OrderItem {
  product_id: number
  product_name: string
  quantity: number
  price: number
  subtotal: number
}

interface Order {
  id: number
  order_number: string
  user_id: number
  username: string
  status: string
  total_amount: number
  shipping_address?: string
  note?: string
  items: OrderItem[]
  confirmed_at?: string
  created_at: string
}

const route = useRoute()
const router = useRouter()

const order = ref<Order | null>(null)
const loading = ref(false)

const totalItems = computed(() => {
  if (!order.value) return 0
  return order.value.items.reduce((sum, item) => sum + item.quantity, 0)
})

async function fetchOrder() {
  const id = parseInt(route.params.id as string)
  loading.value = true
  try {
    const res = await getOrderDetail(id)
    if (res.success && res.data) {
      order.value = res.data
    }
  } catch (error) {
    console.error('Failed to load order:', error)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function formatDate(date: string) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    CREATED: 'warning',
    CONFIRMED: 'success',
    CANCELLED: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    CREATED: '待确认',
    CONFIRMED: '已确认',
    CANCELLED: '已取消'
  }
  return map[status] || status
}

onMounted(() => {
  fetchOrder()
})
</script>

<style scoped lang="scss">
.order-detail-page {
  .page-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 24px;
    
    h1 {
      margin: 0;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
    flex: 1;
  }
  }
  
  .order-info-card,
  .items-card,
  .actions-card {
    background: #fff;
    border-radius: 8px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  }
  
  .order-info-card {
    .info-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid #ebeef5;
      
      .order-number {
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }
    }
    
    .info-row {
      display: flex;
      padding: 8px 0;
      
      .label {
        width: 100px;
        color: #909399;
        flex-shrink: 0;
      }
    }
  }
  
  .items-card {
    h3 {
      margin: 0 0 16px;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
    
    .item-list {
      .order-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #ebeef5;
        
        .item-info {
          flex: 1;
          
          h4 {
            margin: 0 0 4px;
            font-size: 14px;
            color: #303133;
          }
          
          p {
            margin: 0;
            color: #909399;
            font-size: 13px;
          }
        }
        
        .item-quantity,
        .item-subtotal {
          width: 100px;
          text-align: right;
          color: #606266;
        }
        
        .item-subtotal {
          color: #f56c6c;
          font-weight: 600;
        }
      }
    }
    
    .total-section {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 2px solid #ebeef5;
      
      .total-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        
        .amount {
          font-size: 18px;
          font-weight: 600;
          color: #f56c6c;
        }
      }
    }
  }
}
</style>