<template>
  <div class="product-card" @click="goToDetail">
    <div class="product-image">
      <img v-if="product.image_url" :src="product.image_url" :alt="product.name" />
      <div v-else class="no-image">
        <el-icon :size="40"><Picture /></el-icon>
      </div>
    </div>
    <div class="product-info">
      <h3 class="product-name">{{ product.name }}</h3>
      <p class="product-desc" v-if="product.description">{{ product.description }}</p>
      <div class="product-price">
        <span class="price">¥{{ product.price.toFixed(2) }}</span>
      </div>
      <div class="product-meta">
        <span class="stock">库存: {{ product.stock }}</span>
      </div>
    </div>
    <div class="product-actions">
      <el-button type="primary" size="small" @click.stop="handleAddCart">
        加入购物车
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useCartStore } from '@/stores/cart'
import type { Product } from '@/types/product'

const props = defineProps<{
  product: Product
}>()

const router = useRouter()
const cartStore = useCartStore()

function goToDetail() {
  router.push(`/product/${props.product.id}`)
}

async function handleAddCart() {
  const success = await cartStore.addItem(props.product.id)
  if (success) {
    ElMessage.success('已添加到购物车')
  }
}
</script>

<style scoped lang="scss">
.product-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    
    .product-actions {
      opacity: 1;
    }
  }
}

.product-image {
  width: 100%;
  height: 200px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s;
  }
  
  .no-image {
    color: #c0c4cc;
  }
  
  &:hover img {
    transform: scale(1.05);
  }
}

.product-info {
  padding: 12px;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-desc {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
  
  .price {
    font-size: 20px;
    font-weight: 700;
    color: #f56c6c;
  }
}

.product-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.product-actions {
  padding: 12px;
  padding-top: 0;
  opacity: 0;
  transition: opacity 0.3s;
}
</style>