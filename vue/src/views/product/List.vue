<template>
  <div class="product-list-page container">
    <div class="page-header">
      <h1>商品列表</h1>
    </div>
    
    <div class="content-wrapper">
      <aside class="filter-sidebar">
        <div class="filter-section">
          <h3>分类筛选</h3>
          <el-tree
            :data="categories"
            :props="{ label: 'name', children: 'children' }"
            @node-click="handleCategoryClick"
            node-key="id"
            default-expand-all
          />
        </div>
        
        <div class="filter-section">
          <h3>价格区间</h3>
          <div class="price-inputs">
            <el-input-number
              v-model="filters.minPrice"
              :min="0"
              placeholder="最低"
              @change="handleFilterChange"
            />
            <span>-</span>
            <el-input-number
              v-model="filters.maxPrice"
              :min="0"
              placeholder="最高"
              @change="handleFilterChange"
            />
          </div>
          <el-button type="primary" size="small" @click="handleFilterChange">
            应用
          </el-button>
        </div>
      </aside>
      
      <main class="product-main">
        <div class="toolbar">
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索商品..."
              @keyup.enter="handleSearch"
              clearable
            >
              <template #append>
                <el-button :icon="Search" @click="handleSearch" />
              </template>
            </el-input>
          </div>
          
          <div class="sort-bar">
            <el-select v-model="sortOrder" @change="handleFilterChange">
              <el-option label="默认排序" value="created_at" />
              <el-option label="价格从低到高" value="price" />
              <el-option label="价格从高到低" value="price" />
            </el-select>
          </div>
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
              :page-sizes="[12, 24, 48]"
              layout="total, sizes, prev, pager, next"
              @size-change="handleFilterChange"
              @current-change="handleFilterChange"
            />
          </div>
        </template>
        
        <Empty v-else text="暂无商品" />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { getProductList, getCategoryList } from '@/api/product'
import type { ProductListItem } from '@/types/product'
import type { Category } from '@/types/product'
import ProductCard from '@/components/common/ProductCard.vue'
import Loading from '@/components/common/Loading.vue'
import Empty from '@/components/common/Empty.vue'

const route = useRoute()
const router = useRouter()

const products = ref<ProductListItem[]>([])
const categories = ref<Category[]>([])
const loading = ref(false)

const searchKeyword = ref('')
const sortOrder = ref('created_at')
const sortOrderDirection = ref('desc')

const filters = reactive({
  categoryId: null as number | null,
  minPrice: null as number | null,
  maxPrice: null as number | null
})

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
})

async function fetchProducts() {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      page_size: pagination.pageSize,
      category_id: filters.categoryId || undefined,
      search: searchKeyword.value || undefined,
      min_price: filters.minPrice || undefined,
      max_price: filters.maxPrice || undefined,
      sort: sortOrder.value,
      order: sortOrderDirection.value
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

function handleSearch() {
  pagination.page = 1
  fetchProducts()
}

function handleFilterChange() {
  pagination.page = 1
  fetchProducts()
}

function handleCategoryClick(data: Category) {
  filters.categoryId = data.id
  router.push({ query: { category: data.id } })
  handleFilterChange()
}

onMounted(() => {
  if (route.query.search) {
    searchKeyword.value = route.query.search as string
  }
  if (route.query.category) {
    filters.categoryId = parseInt(route.query.category as string)
  }
  fetchProducts()
  fetchCategories()
})

watch(() => route.query, () => {
  if (route.query.search) {
    searchKeyword.value = route.query.search as string
    handleFilterChange()
  }
  if (route.query.category) {
    filters.categoryId = parseInt(route.query.category as string)
    handleFilterChange()
  }
})
</script>

<style scoped lang="scss">
.product-list-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.content-wrapper {
  display: flex;
  gap: 20px;
}

.filter-sidebar {
  width: 220px;
  flex-shrink: 0;
  
  .filter-section {
    background: #fff;
    padding: 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    
    h3 {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    
    .price-inputs {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }
  }
}

.product-main {
  flex: 1;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  
  .search-bar {
    width: 300px;
  }
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  
  @media (max-width: 992px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.pagination-wrapper {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}
</style>