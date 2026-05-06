<template>
  <div class="cart-page container">
    <div class="page-header">
      <h1>购物车</h1>
    </div>
    
    <div v-if="cartStore.loading" class="loading-wrapper">
      <Loading :loading="cartStore.loading" text="加载购物车..." />
    </div>
    
    <div v-else>
      <div v-if="cartStore.items.length > 0">
        <div class="cart-content">
          <div class="cart-items">
            <div class="cart-header">
              <el-checkbox v-model="selectAll" @change="handleSelectAll">全选</el-checkbox>
              <span class="header-label header-info">商品信息</span>
              <span class="header-label header-price">单价</span>
              <span class="header-label header-quantity">数量</span>
              <span class="header-label header-subtotal">小计</span>
              <span class="header-label header-actions">操作</span>
            </div>
            
            <div class="cart-item" v-for="item in cartStore.items" :key="item.id">
              <el-checkbox v-model="selectedItems" :label="item.id" />
              <div class="item-info">
                <img
                  v-if="item.product?.image_url"
                  :src="item.product.image_url"
                  :alt="item.product.name"
                  class="item-image"
                />
                <div v-else class="item-image no-image">
                  <el-icon><Picture /></el-icon>
                </div>
                <div class="item-detail">
                  <h4>{{ item.product?.name }}</h4>
                  <p>库存: {{ item.product?.stock != null ? item.product.stock : 'N/A' }}</p>
                </div>
              </div>
              <div class="item-price">¥{{ item.product?.price?.toFixed(2) || '0.00' }}</div>
              <div class="item-quantity">
                <template v-if="item.product?.stock != null">
                  <el-input-number
                    v-if="item.product.stock > 0"
                    v-model="item.quantity"
                    :min="1"
                    :max="item.product.stock"
                    @change="(val: number) => handleQuantityChange(item.id, val)"
                  />
                  <el-tag v-else type="danger" disable-transitions>已售罄</el-tag>
                </template>
                <el-input-number
                  v-else
                  v-model="item.quantity"
                  :min="1"
                  :max="99"
                  @change="(val: number) => handleQuantityChange(item.id, val)"
                />
              </div>
              <div class="item-subtotal">¥{{ item.subtotal?.toFixed(2) || '0.00' }}</div>
              <div class="item-actions">
                <el-button type="danger" text @click="handleRemove(item.id)">
                  删除
                </el-button>
              </div>
            </div>
          </div>
          
          <div class="cart-summary">
            <div class="summary-row">
              <span>商品总数:</span>
              <span>{{ cartStore.summary?.total_items }}</span>
            </div>
            <div class="summary-row total">
              <span>合计:</span>
              <span>¥{{ cartStore.summary?.total_amount?.toFixed(2) || '0.00' }}</span>
            </div>
            <el-button type="primary" size="large" @click="handleCheckout">
              结算
            </el-button>
          </div>
        </div>
      </div>
      
      <Empty v-else text="购物车为空">
        <template #action>
          <el-button type="primary" @click="$router.push('/products')">
            去购物
          </el-button>
        </template>
      </Empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const cartStore = useCartStore()

const selectAll = ref(false)
const selectedItems = ref<number[]>([])

async function handleQuantityChange(itemId: number, quantity: number) {
  await cartStore.updateQuantity(itemId, quantity)
}

async function handleRemove(itemId: number) {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const success = await cartStore.removeItem(itemId)
    if (success) {
      selectedItems.value = selectedItems.value.filter(id => id !== itemId)
      ElMessage.success('已删除')
    }
  } catch {
    // User cancelled
  }
}

function handleSelectAll(val: boolean) {
  if (val) {
    selectedItems.value = cartStore.items.map(i => i.id)
  } else {
    selectedItems.value = []
  }
}

async function handleCheckout() {
  if (cartStore.items.length === 0) {
    ElMessage.warning('购物车为空')
    return
  }
  const ids = selectedItems.value.length > 0 
    ? selectedItems.value.join(',') 
    : cartStore.items.map(i => i.id).join(',')
  router.push(`/order/confirm?ids=${ids}`)
}

onMounted(() => {
  cartStore.fetchCart()
})

watch(() => cartStore.items, () => {
  selectAll.value = cartStore.items.length > 0 && 
    selectedItems.value.length === cartStore.items.length
})
</script>

<style scoped lang="scss">
.cart-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.cart-content {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.cart-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  font-weight: 600;
  
  .el-checkbox {
    width: 40px;
  }
  
  .header-label {
    text-align: center;
    
    &.header-info {
      flex: 1;
      text-align: left;
    }
    
    &.header-price {
      width: 120px;
    }
    
    &.header-quantity {
      width: 120px;
    }
    
    &.header-subtotal {
      width: 120px;
    }
    
    &.header-actions {
      width: 80px;
    }
  }
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  
  .el-checkbox {
    width: 40px;
  }
  
  .item-info {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    overflow: hidden;
  }
  
  .item-image {
    width: 80px;
    height: 80px;
    border-radius: 4px;
    object-fit: cover;
    background: #f5f7fa;
    
    &.no-image {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #c0c4cc;
    }
  }
  
  .item-detail {
    overflow: hidden;
    min-width: 0;
    
    h4 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    p {
      font-size: 12px;
      color: #909399;
    }
  }
  
  .item-price {
    width: 120px;
    text-align: center;
    font-size: 16px;
    font-weight: 600;
    color: #f56c6c;
  }
  
  .item-quantity {
    width: 120px;
    text-align: center;
  }
  
  .item-subtotal {
    width: 120px;
    text-align: center;
    font-size: 16px;
    font-weight: 700;
    color: #f56c6c;
  }
  
  .item-actions {
    width: 80px;
    text-align: center;
  }
}

.cart-summary {
  padding: 20px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
  
  .summary-row {
    display: flex;
    gap: 40px;
    font-size: 14px;
    color: #606266;
    
    &.total {
      font-size: 20px;
      font-weight: 700;
      color: #f56c6c;
    }
  }
}
</style>