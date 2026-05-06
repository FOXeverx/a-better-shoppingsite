<template>
  <div class="category-page container">
    <div class="page-header">
      <h1>{{ categoryName }}</h1>
    </div>
    
    <Loading :loading="loading" />
    
    <template v-if="!loading && products.length > 0">
      <div class="product-grid">
        <ProductCard
          v-for="item in products"
          :key="item.id"
          :product="item"
        />
      </div>
      
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchProducts"
        />
      </div>
    </template>
    
    <Empty v-else text="该分类下暂无商品" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getProductList, getCategoryList } from '@/api/product'
import type { ProductListItem } from '@/types/product'
import type { Category } from '@/types/product'
import ProductCard from '@/components/common/ProductCard.vue'
import Loading from '@/components/common/Loading.vue'
import Empty from '@/components/common/Empty.vue'

const route = useRoute()

const products = ref<ProductListItem[]>([])
const categories = ref<Category[]>([])
const loading = ref(false)

const categoryId = computed(() => parseInt(route.params.id as string))

const categoryName = computed(() => {
  const findCategory = (cats: Category[], id: number): string | null => {
    for (const cat of cats) {
      if (cat.id === id) return cat.name
      if (cat.children) {
        const found = findCategory(cat.children, id)
        if (found) return found
      }
    }
    return null
  }
  return findCategory(categories.value, categoryId.value) || '商品分类'
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

async function fetchProducts() {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      page_size: pagination.pageSize,
      category_id: categoryId.value
    })
    if (res.success && res.data) {
      products.value = res.data
      if (res.pagination) {
        pagination.total = res.pagination.total
      }
    }
  } catch (error) {
    console.error('Failed to load products:', error)
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const res = await getCategoryList()
    if (res.success && res.data) {
      categories.value = res.data
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

onMounted(() => {
  fetchProducts()
  fetchCategories()
})
</script>

<style scoped lang="scss">
.category-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.product-grid {
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

.pagination-wrapper {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}
</style>