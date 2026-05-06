<template>
  <div class="home-page">
    <section class="hero-section">
      <div class="container">
        <h1>欢迎来到电商平台</h1>
        <p>精选商品，优质服务</p>
      </div>
    </section>
    
    <section class="products-section container">
      <div class="section-header">
        <h2>热门推荐</h2>
      </div>
      
      <Loading :loading="loading" text="加载中..." />
      
      <template v-if="!loading && products.length > 0">
        <div class="product-grid">
          <ProductCard
            v-for="item in products"
            :key="item.id"
            :product="item"
          />
        </div>
        
        <div class="view-more">
          <el-button type="primary" size="large" @click="$router.push('/products')">
            查看更多商品
          </el-button>
        </div>
      </template>
      
      <Empty v-else text="暂无商品" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getProductList } from '@/api/product'
import type { ProductListItem } from '@/types/product'
import ProductCard from '@/components/common/ProductCard.vue'
import Loading from '@/components/common/Loading.vue'
import Empty from '@/components/common/Empty.vue'

const products = ref<ProductListItem[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    const res = await getProductList({ page_size: 8 })
    if (res.success && res.data) {
      products.value = res.data
    }
  } catch (error) {
    console.error('Failed to load products:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 80px 0;
  text-align: center;
  
  h1 {
    font-size: 48px;
    font-weight: 700;
    margin-bottom: 16px;
  }
  
  p {
    font-size: 20px;
    opacity: 0.9;
  }
}

.products-section {
  padding: 40px 0;
}

.section-header {
  margin-bottom: 24px;
  
  h2 {
    font-size: 24px;
    font-weight: 600;
    color: #303133;
  }
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: repeat(3, 1fr);
  }
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.view-more {
  text-align: center;
  margin-top: 40px;
}
</style>