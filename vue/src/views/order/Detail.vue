<template>
  <div class="order-detail-page container">
    <div class="page-header">
      <el-button text @click="$router.push('/orders')">
        <el-icon><ArrowLeft /></el-icon>
        返回订单列表
      </el-button>
      <h1>订单详情</h1>
    </div>
    
    <Loading :loading="loading" text="加载中..." />
    
    <template v-if="!loading && order">
      <el-alert
        v-if="order.status === 'CREATED'"
        type="warning"
        :closable="false"
        show-icon
        class="status-alert"
      >
        <template #title>
          订单待确认 — 请前往邮箱查收确认邮件，点击链接完成确认。确认完成后请刷新本页面查看最新状态。
        </template>
      </el-alert>

      <div class="order-info-card">
        <div class="info-header">
          <div class="order-number">订单号: {{ order.order_number }}</div>
          <el-tag :type="getStatusType(order.status)">
            {{ getStatusText(order.status) }}
          </el-tag>
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
            <img v-if="item.image_url" :src="item.image_url" :alt="item.product_name" />
            <div class="item-info">
              <h4>{{ item.product_name }}</h4>
              <p>单价: ¥{{ item.price.toFixed(2) }}</p>
            </div>
            <div class="item-quantity">x{{ item.quantity }}</div>
            <div class="item-subtotal">¥{{ (item.price * item.quantity).toFixed(2) }}</div>
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
      
      <div class="actions-card" v-if="order.status === 'CREATED'">
        <el-button type="danger" @click="handleCancelOrder">取消订单</el-button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getOrderDetail, cancelOrder } from '@/api/order'
import type { Order, OrderStatus } from '@/types/order'
import Loading from '@/components/common/Loading.vue'

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
  } finally {
    loading.value = false
  }
}

async function handleCancelOrder() {
  if (!order.value) return
  
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await cancelOrder(order.value.id)
    if (res.success) {
      ElMessage.success('订单已取消')
      fetchOrder()
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
  fetchOrder()
})
</script>

<style scoped lang="scss">
.order-detail-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    margin-top: 12px;
  }
}

.status-alert {
  margin-bottom: 20px;
}

.order-info-card,
.items-card,
.actions-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
}

.order-info-card {
  .info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    
    .order-number {
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .info-row {
    display: flex;
    padding: 8px 0;
    
    .label {
      width: 100px;
      color: #909399;
    }
  }
}

.items-card {
  h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .item-list {
    .order-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid #f0f0f0;
      
      img {
        width: 60px;
        height: 60px;
        border-radius: 4px;
        object-fit: cover;
        margin-right: 12px;
      }
      
      .item-info {
        flex: 1;
        
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
      
      .item-quantity {
        width: 60px;
        text-align: center;
        color: #606266;
      }
      
      .item-subtotal {
        width: 100px;
        text-align: right;
        font-weight: 600;
        color: #f56c6c;
      }
    }
  }
  
  .total-section {
    margin-top: 20px;
    text-align: right;
    
    .total-row {
      display: flex;
      justify-content: flex-end;
      gap: 40px;
      padding: 8px 0;
      font-size: 14px;
      color: #606266;
      
      .amount {
        font-size: 20px;
        font-weight: 700;
        color: #f56c6c;
      }
    }
  }
}

.actions-card {
  text-align: center;
  
  .el-button {
    margin: 0 8px;
  }
}
</style>