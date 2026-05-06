<template>
  <div class="order-confirmed-page container">
    <div class="confirm-card">
      <div class="icon-wrapper" :class="{ success: confirmed, error: !confirmed }">
        <el-icon v-if="loading" class="is-loading"><Loading /></el-icon>
        <el-icon v-else-if="confirmed"><CircleCheckFilled /></el-icon>
        <el-icon v-else><CircleCloseFilled /></el-icon>
      </div>
      
      <h1 v-if="loading">正在确认订单...</h1>
      <h1 v-else-if="confirmed">订单确认成功</h1>
      <h1 v-else>订单确认失败</h1>
      
      <p v-if="loading" class="message">请稍候</p>
      <p v-else-if="confirmed" class="message">
        {{ successMessage }}
      </p>
      <p v-else class="message">{{ errorMessage }}</p>
      
      <div class="actions" v-if="!loading">
        <el-button type="primary" @click="goToHome">返回首页</el-button>
        <el-button v-if="confirmed && orderId" @click="goToOrderDetail">查看订单详情</el-button>
        <el-button v-else-if="confirmed" @click="goToOrders">查看订单列表</el-button>
      </div>
      
      <p v-if="confirmed" class="hint">
        提示：如您已打开订单详情页面，请刷新该页面查看最新状态
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { get } from '@/api'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const confirmed = ref(false)
const errorMessage = ref('')
const orderId = ref<number | null>(null)
const successMessage = ref('')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    loading.value = false
    confirmed.value = false
    errorMessage.value = '无效的确认链接'
    return
  }

  try {
    const res = await get<any>('/order/confirm', { params: { token } })
    if (res.success) {
      confirmed.value = true
      ElMessage.success('订单确认成功')
      if (res.data?.order_id) {
        orderId.value = res.data.order_id
      }
      successMessage.value = '您的订单已成功确认，感谢您的购买'
    } else {
      confirmed.value = false
      errorMessage.value = res.message || '确认失败'
    }
  } catch (error: any) {
    confirmed.value = false
    errorMessage.value = '确认失败，请重试'
  } finally {
    loading.value = false
  }
})

function goToHome() {
  router.push('/')
}

function goToOrders() {
  router.push('/orders')
}

function goToOrderDetail() {
  if (orderId.value) {
    router.push(`/order/${orderId.value}`)
  }
}
</script>

<style scoped lang="scss">
.order-confirmed-page {
  padding: 60px 0;
  display: flex;
  justify-content: center;
}

.confirm-card {
  background: #fff;
  border-radius: 12px;
  padding: 60px 80px;
  text-align: center;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.icon-wrapper {
  font-size: 64px;
  margin-bottom: 24px;
  
  &.success {
    color: #67c23a;
  }
  
  &.error {
    color: #f56c6c;
  }
  
  .is-loading {
    animation: rotate 1s linear infinite;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.message {
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.hint {
  margin-top: 24px;
  font-size: 13px;
  color: #909399;
}
</style>