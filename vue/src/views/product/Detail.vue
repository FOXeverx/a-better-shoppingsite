<template>
  <div class="product-detail-page container">
    <Loading :loading="loading" text="加载中..." />
    
    <template v-if="!loading && product">
      <div class="breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item :to="{ path: '/products' }">商品列表</el-breadcrumb-item>
          <el-breadcrumb-item>{{ product.name }}</el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      
      <div class="product-content">
        <div class="product-gallery">
          <div class="main-image">
            <img v-if="product.image_url" :src="product.image_url" :alt="product.name" />
            <div v-else class="no-image">
              <el-icon :size="80"><Picture /></el-icon>
            </div>
          </div>
        </div>
        
        <div class="product-info">
          <h1 class="product-title">{{ product.name }}</h1>
          <p class="product-desc" v-if="product.description">{{ product.description }}</p>
          
          <div class="price-section">
            <span class="label">价格</span>
            <span class="price">¥{{ product.price.toFixed(2) }}</span>
          </div>
          
          <div class="stock-section">
            <span class="label">库存</span>
            <span class="stock" :class="{ 'out-of-stock': product.stock === 0 }">
              {{ product.stock }} 件
              <span v-if="product.stock === 0" class="stock-warning">(缺货)</span>
            </span>
          </div>
          
          <div class="quantity-section" v-if="product.stock > 0">
            <span class="label">数量</span>
            <el-input-number
              v-model="quantity"
              :min="1"
              :max="product.stock"
              size="large"
            />
          </div>
          
          <div class="action-section">
            <el-button 
              type="primary" 
              size="large" 
              @click="handleAddCart"
              :disabled="product.stock === 0"
            >
              {{ product.stock === 0 ? '已售罄' : '加入购物车' }}
            </el-button>
            <el-button 
              type="warning" 
              size="large" 
              @click="handleBuyNow"
              :disabled="product.stock === 0"
            >
              立即购买
            </el-button>
          </div>
        </div>
      </div>
      
      <div class="recommend-section" v-if="authStore.isLoggedIn && recommends.length > 0">
        <h3>相关推荐</h3>
        <div class="recommend-list">
          <div
            v-for="item in recommends"
            :key="item.product_id"
            class="recommend-item"
            @click="goToProduct(item.product_id)"
          >
            <img v-if="item.image_url" :src="item.image_url" :alt="item.product_name" />
            <div v-else class="no-image"></div>
            <p class="name">{{ item.product_name }}</p>
            <p class="score">相似度: {{ (item.score * 100).toFixed(0) }}%</p>
          </div>
        </div>
      </div>
      
      <div class="recommend-section also-bought" v-if="authStore.isLoggedIn && alsoBought.length > 0">
        <h3>浏览过此商品的人也买了</h3>
        <div class="recommend-list">
          <div
            v-for="item in alsoBought"
            :key="item.product_id"
            class="recommend-item"
            @click="goToProduct(item.product_id)"
          >
            <img v-if="item.image_url" :src="item.image_url" :alt="item.product_name" />
            <div v-else class="no-image"></div>
            <p class="name">{{ item.product_name }}</p>
            <p class="score">{{ item.reason }}</p>
          </div>
        </div>
      </div>

      <div class="comment-section">
        <h3>商品评论</h3>
        
        <div class="comment-form" v-if="authStore.isLoggedIn">
          <el-input
            v-model="newComment"
            type="textarea"
            :rows="3"
            placeholder="写下你的评论..."
            :disabled="submitting"
          />
          <el-button 
            type="primary" 
            @click="submitComment" 
            :loading="submitting"
            :disabled="!newComment.trim()"
          >
            发表评论
          </el-button>
        </div>
        <div class="comment-form" v-else>
          <el-alert type="info" :closable="false">
            <router-link to="/login">登录</router-link>后发表评论
          </el-alert>
        </div>

        <div class="comment-list" v-if="comments.length > 0">
          <div v-for="comment in comments" :key="comment.id" class="comment-item">
            <div class="comment-header">
              <span class="username">{{ comment.username }}</span>
              <span class="time">{{ formatTime(comment.created_at) }}</span>
              <el-button 
                v-if="isSalesOrAdmin()" 
                type="danger" 
                size="small" 
                text 
                @click="handleDeleteComment(comment.id)"
              >
                删除
              </el-button>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
          </div>
        </div>
        <Empty v-else text="暂无评论，快来抢先评论吧" />
      </div>
    </template>
    
    <Empty v-else-if="!loading" text="商品不存在" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'
import { getProductDetail, getProductRecommend, logBrowse, getProductComments, addProductComment, deleteProductComment } from '@/api/product'
import { getBoughtAlsoBought } from '@/api/recommend'
import type { ProductDetail } from '@/types/product'
import type { ProductRecommend } from '@/types/product'
import { useCartStore } from '@/stores/cart'
import { useAuthStore } from '@/stores/auth'
import Loading from '@/components/common/Loading.vue'
import Empty from '@/components/common/Empty.vue'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()
const authStore = useAuthStore()

const product = ref<ProductDetail | null>(null)
const recommends = ref<ProductRecommend[]>([])
const alsoBought = ref<any[]>([])
const loading = ref(false)
const quantity = ref(1)
const stayTimer = ref<number>(0)
const comments = ref<any[]>([])
const newComment = ref('')
const submitting = ref(false)

async function fetchComments(productId: number) {
  try {
    const res = await getProductComments(productId)
    if (res.success && res.data) {
      comments.value = res.data
    }
  } catch (error) {
    console.error('Failed to load comments:', error)
  }
}

async function submitComment() {
  if (!product.value || !newComment.value.trim() || submitting.value) return
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  submitting.value = true
  try {
    const res = await addProductComment(product.value.id, newComment.value.trim())
    if (res.success && res.data) {
      comments.value.unshift(res.data)
      newComment.value = ''
      ElMessage.success('评论成功')
    }
  } catch (error) {
    console.error('Failed to add comment:', error)
    ElMessage.error('评论失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeleteComment(commentId: number) {
  try {
    const res = await deleteProductComment(commentId)
    if (res.success) {
      comments.value = comments.value.filter(c => c.id !== commentId)
      ElMessage.success('删除成功')
    }
  } catch (error) {
    console.error('Failed to delete comment:', error)
    ElMessage.error('删除失败')
  }
}

function isSalesOrAdmin() {
  return authStore.isSales
}

function recordBrowse() {
  if (!product.value) return
  
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
    console.log('[Browse] User not logged in, skipping')
    return
  }
  
  stayTimer.value = Date.now()
  logBrowse(product.value.id, 0)
    .then(res => {
      if (res.success) {
        console.log('[Browse] Logged:', res)
      } else {
        console.error('[Browse] Failed:', res.message || res.error?.message)
      }
    })
    .catch(err => console.error('[Browse] Error:', err))
}

function recordStayTime() {
  if (stayTimer.value > 0) {
    const stayTime = Math.floor((Date.now() - stayTimer.value) / 1000)
    if (product.value && stayTime > 0) {
      const authStore = useAuthStore()
      if (authStore.isLoggedIn) {
        logBrowse(product.value.id, stayTime)
          .then(res => console.log('[Browse] Stay time logged:', stayTime, 'seconds'))
          .catch(err => console.error('[Browse] Stay time error:', err))
      }
    }
  }
}

async function fetchProduct() {
  const id = parseInt(route.params.id as string)
  loading.value = true
  console.log('[ProductDetail] Fetching product:', id)
  try {
    const res = await getProductDetail(id)
    console.log('[ProductDetail] Response:', res)
    if (res.success && res.data) {
      product.value = res.data
      fetchRecommends(id)
      fetchAlsoBought(id)
      fetchComments(id)
      recordBrowse()
    } else {
      console.log('[ProductDetail] No data or failed:', res)
    }
  } catch (error) {
    console.error('[ProductDetail] Failed to load product:', error)
  } finally {
    loading.value = false
  }
}

async function fetchAlsoBought(productId: number) {
  try {
    const res = await getBoughtAlsoBought(productId, 5)
    if (res.success && res.data) {
      alsoBought.value = res.data
    }
  } catch (error) {
    console.error('Failed to load also bought:', error)
  }
}

async function fetchRecommends(productId: number) {
  try {
    const res = await getProductRecommend(productId)
    if (res.success && res.data) {
      recommends.value = res.data
    }
  } catch (error) {
    console.error('Failed to load recommends:', error)
  }
}

async function handleAddCart() {
  if (!product.value) return
  const success = await cartStore.addItem(product.value.id, quantity.value)
  if (success) {
    ElMessage.success('已添加到购物车')
  }
}

function handleBuyNow() {
  if (!product.value) return
  handleAddCart().then(() => {
    router.push('/cart')
  })
}

function goToProduct(id: number) {
  router.push(`/product/${id}`)
}

function formatTime(timeStr: string) {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

onMounted(() => {
  fetchProduct()
})

onUnmounted(() => {
  recordStayTime()
})
</script>

<style scoped lang="scss">
.product-detail-page {
  padding: 20px 0;
}

.breadcrumb {
  margin-bottom: 20px;
}

.product-content {
  display: flex;
  gap: 40px;
  background: #fff;
  padding: 30px;
  border-radius: 8px;
}

.product-gallery {
  width: 400px;
  flex-shrink: 0;
  
  .main-image {
    width: 100%;
    height: 400px;
    background: #f5f7fa;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    
    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    
    .no-image {
      color: #c0c4cc;
    }
  }
}

.product-info {
  flex: 1;
}

.product-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
}

.product-desc {
  color: #606266;
  margin-bottom: 24px;
  line-height: 1.6;
}

.price-section,
.stock-section,
.quantity-section {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  
  .label {
    width: 80px;
    color: #909399;
  }
  
  .price {
    font-size: 28px;
    font-weight: 700;
    color: #f56c6c;
  }
  
  .stock {
    font-size: 16px;
    
    &.out-of-stock {
      color: #909399;
    }
    
    .stock-warning {
      color: #f56c6c;
      font-size: 14px;
      margin-left: 8px;
    }
  }
}

.action-section {
  margin-top: 30px;
  display: flex;
  gap: 16px;
}

.recommend-section {
  margin-top: 40px;
  
  h3 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 20px;
  }
  
  &.also-bought {
    h3 {
      color: #409eff;
    }
  }
}

.recommend-list {
  display: flex;
  gap: 16px;
  overflow-x: auto;
}

.recommend-item {
  width: 150px;
  background: #fff;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  img, .no-image {
    width: 100%;
    height: 120px;
    background: #f5f7fa;
    border-radius: 4px;
    margin-bottom: 8px;
    object-fit: cover;
  }
  
  .name {
    font-size: 14px;
    margin-bottom: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .score {
    font-size: 12px;
    color: #909399;
  }
}

.comment-section {
  margin-top: 40px;
  background: #fff;
  padding: 30px;
  border-radius: 8px;

  h3 {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 20px;
  }
}

.comment-form {
  margin-bottom: 24px;

  .el-textarea {
    margin-bottom: 12px;
  }
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-item {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;

  .username {
    font-weight: 600;
    margin-right: 12px;
  }

  .time {
    color: #909399;
    font-size: 12px;
    flex: 1;
  }
}

.comment-content {
  color: #606266;
  line-height: 1.6;
}
</style>