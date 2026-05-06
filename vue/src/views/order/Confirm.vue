<template>
  <div class="order-confirm-page container">
    <div class="page-header">
      <h1>确认订单</h1>
    </div>
    
    <div class="confirm-content">
      <div class="order-section">
        <h3>收货信息</h3>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="收货地址" prop="shipping_address">
            <el-input
              v-model="form.shipping_address"
              type="textarea"
              :rows="3"
              placeholder="请输入详细收货地址"
            />
          </el-form-item>
          <el-form-item label="订单备注">
            <el-input
              v-model="form.note"
              type="textarea"
              :rows="2"
              placeholder="选填，请输入订单备注"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <div class="order-section">
        <h3>商品清单</h3>
        <div class="item-list">
          <div class="order-item" v-for="item in displayItems" :key="item.id">
            <img
              v-if="item.product.image_url"
              :src="item.product.image_url"
              :alt="item.product.name"
            />
            <div class="item-info">
              <h4>{{ item.product.name }}</h4>
              <p>单价: ¥{{ item.product.price.toFixed(2) }}</p>
            </div>
            <div class="item-quantity">x{{ item.quantity }}</div>
            <div class="item-subtotal">¥{{ item.subtotal.toFixed(2) }}</div>
          </div>
        </div>
      </div>
      
      <div class="order-section summary">
        <div class="summary-row">
          <span>商品总数:</span>
          <span>{{ cartStore.summary?.total_items }}</span>
        </div>
        <div class="summary-row total">
          <span>订单金额:</span>
          <span>¥{{ cartStore.summary?.total_amount.toFixed(2) }}</span>
        </div>
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交订单
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { useCartStore } from '@/stores/cart'
import { createOrder } from '@/api/order'

const router = useRouter()
const route = useRoute()
const cartStore = useCartStore()

const selectedIds = computed(() => {
  const idsParam = route.query.ids as string
  if (idsParam) {
    return new Set(idsParam.split(',').map(Number))
  }
  return null
})

const displayItems = computed(() => {
  if (selectedIds.value) {
    return cartStore.items.filter(i => selectedIds.value!.has(i.id))
  }
  return cartStore.items
})

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  shipping_address: '',
  note: ''
})

const rules: FormRules = {
  shipping_address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    if (displayItems.value.length === 0) {
      ElMessage.warning('购物车为空')
      return
    }
    
    submitting.value = true
    try {
      const res = await createOrder({
        shipping_address: form.shipping_address,
        note: form.note
      })
      
      if (res.success && res.data) {
        ElMessage.success('订单创建成功，请前往邮箱确认')
        await cartStore.clearCart()
        router.push(`/order/${res.data.id}`)
      }
    } catch (error) {
      console.error('Failed to create order:', error)
    } finally {
      submitting.value = false
    }
  })
}

onMounted(() => {
  if (cartStore.isEmpty) {
    cartStore.fetchCart()
  }
})
</script>

<style scoped lang="scss">
.order-confirm-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.confirm-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}

.order-section {
  margin-bottom: 30px;
  
  h3 {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #f0f0f0;
  }
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

.summary {
  text-align: right;
  
  .summary-row {
    display: flex;
    justify-content: flex-end;
    gap: 40px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #606266;
    
    &.total {
      font-size: 20px;
      font-weight: 700;
      color: #f56c6c;
      margin-top: 16px;
    }
  }
  
  .el-button {
    margin-top: 16px;
    min-width: 200px;
  }
}
</style>