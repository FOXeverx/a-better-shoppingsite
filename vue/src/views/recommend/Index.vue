<template>
  <div class="recommend-page container">
    <div class="page-header">
      <h1>个性化推荐</h1>
      <p>基于您的浏览和购买记录，为您推荐商品</p>
    </div>
    
    <Loading :loading="loading" text="加载推荐中..." />
    
    <template v-if="!loading">
      <template v-if="recommends.length > 0">
        <div class="recommend-list">
          <div
            class="recommend-item"
            v-for="item in recommends"
            :key="item.product_id"
            @click="goToProduct(item.product_id)"
          >
            <div class="item-image">
              <img v-if="item.image_url" :src="item.image_url" :alt="item.product_name" />
              <div v-else class="no-image">
                <el-icon :size="40"><Picture /></el-icon>
              </div>
            </div>
            <div class="item-info">
              <h4>{{ item.product_name }}</h4>
              <div class="item-meta">
                <span class="score">匹配度: {{ (item.score * 100).toFixed(0) }}%</span>
                <span class="reason" v-if="item.reason">{{ item.reason }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
      
      <Empty v-else text="暂无推荐商品">
        <template #action>
          <el-button type="primary" @click="$router.push('/products')">
            去逛逛
          </el-button>
        </template>
      </Empty>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Picture } from '@element-plus/icons-vue'
import { getUserRecommend } from '@/api/product'
import type { ProductRecommend } from '@/types/product'
import Loading from '@/components/common/Loading.vue'
import Empty from '@/components/common/Empty.vue'

const router = useRouter()

const recommends = ref<ProductRecommend[]>([])
const loading = ref(false)

async function fetchRecommends() {
  loading.value = true
  try {
    const res = await getUserRecommend()
    if (res.success && res.data) {
      recommends.value = res.data
    }
  } catch (error) {
    console.error('Failed to load recommends:', error)
  } finally {
    loading.value = false
  }
}

function goToProduct(id: number) {
  router.push(`/product/${id}`)
}

onMounted(() => {
  fetchRecommends()
})
</script>

<style scoped lang="scss">
.recommend-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 30px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  
  p {
    color: #909399;
  }
}

.recommend-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  
  @media (max-width: 992px) {
    grid-template-columns: repeat(3, 1fr);
  }
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.recommend-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }
  
  .item-image {
    width: 100%;
    height: 180px;
    background: #f5f7fa;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .no-image {
      color: #c0c4cc;
    }
  }
  
  .item-info {
    padding: 12px;
    
    h4 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 8px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    
    .item-meta {
      display: flex;
      flex-direction: column;
      gap: 4px;
      
      .score {
        font-size: 13px;
        color: #409eff;
        font-weight: 600;
      }
      
      .reason {
        font-size: 12px;
        color: #909399;
      }
    }
  }
}
</style>