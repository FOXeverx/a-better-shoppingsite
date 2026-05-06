<template>
  <div class="user-behavior-page">
    <div class="page-header">
      <h2>用户行为分析</h2>
    </div>

    <div class="user-list-section" v-if="!currentUser">
      <div class="filter-section">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或邮箱"
          clearable
          @keyup.enter="fetchUsers"
          style="width: 200px"
        />
        <el-button type="primary" @click="fetchUsers">搜索</el-button>
      </div>

      <el-table :data="users" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">{{ getRoleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" text @click="viewUserDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchUsers"
        />
      </div>
    </div>

    <div class="user-detail-section" v-else>
      <div class="detail-header">
        <el-button @click="goBack" :icon="ArrowLeft">返回</el-button>
        <span class="user-info">用户：{{ currentUser.username }} ({{ currentUser.email }})</span>
      </div>

      <el-tabs v-model="activeTab" class="user-tabs">
        <el-tab-pane label="浏览记录" name="browse">
          <el-table :data="browseLogs" v-loading="browseLoading" border>
            <el-table-column prop="product_name" label="商品" min-width="150" />
            <el-table-column prop="stay_time" label="停留时间" width="100">
              <template #default="{ row }">
                {{ row.stay_time }}秒
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="浏览时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="browsePagination.page"
              v-model:page-size="browsePagination.pageSize"
              :total="browsePagination.total"
              layout="total, prev, pager, next"
              @current-change="fetchBrowseLogs"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="登录记录" name="login">
          <el-table :data="loginLogs" v-loading="loginLoading" border>
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            <el-table-column prop="success" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'">
                  {{ row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="登录时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="loginPagination.page"
              v-model:page-size="loginPagination.pageSize"
              :total="loginPagination.total"
              layout="total, prev, pager, next"
              @current-change="fetchLoginLogs"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="购买记录" name="purchase">
          <div v-if="purchaseLoading" v-loading="purchaseLoading"></div>
          <div v-else-if="categoryStats.length === 0" class="empty-state">
            <el-icon :size="60" color="#c0c4cc"><Warning /></el-icon>
            <p>暂无购买记录</p>
          </div>
          <div v-else>
            <div class="stats-cards">
              <div class="stat-card" v-for="cat in categoryStats" :key="cat.category_id" @click="viewCategoryOrders(cat)">
                <div class="stat-icon">
                  <el-icon :size="32"><ShoppingBag /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-name">{{ cat.category_name }}</div>
                  <div class="stat-quantity">{{ cat.total_quantity }} 件</div>
                  <div class="stat-amount">¥{{ cat.total_amount.toFixed(2) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-drawer v-model="drawerVisible" title="订单详情" direction="rtl" size="60%">
      <el-table :data="orderDetails" v-loading="detailsLoading" border>
        <el-table-column prop="order_number" label="订单号" width="140" />
        <el-table-column prop="created_at" label="日期" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="商品" min-width="150" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="price" label="单价" width="100">
          <template #default="{ row }">
            ¥{{ row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="subtotal" label="小计" width="100">
          <template #default="{ row }">
            ¥{{ row.subtotal.toFixed(2) }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="detailsPagination.page"
          v-model:page-size="detailsPagination.pageSize"
          :total="detailsPagination.total"
          layout="total, prev, pager, next"
          @current-change="fetchOrderDetails"
        />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Warning, ShoppingBag, UserFilled } from '@element-plus/icons-vue'
import {
  getUsersSimple,
  getUserBrowseLogs,
  getUserLoginLogs,
  getUserPurchaseSummary,
  getUserPurchaseByCategory,
  type SimpleUser,
  type UserBrowseLog,
  type UserLoginLog,
  type CategoryPurchase,
  type PurchaseDetail
} from '@/api/admin'

const loading = ref(false)
const users = ref<SimpleUser[]>([])
const currentUser = ref<SimpleUser | null>(null)
const searchKeyword = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const activeTab = ref('browse')

const browseLogs = ref<UserBrowseLog[]>([])
const browseLoading = ref(false)
const browsePagination = reactive({ page: 1, pageSize: 20, total: 0 })

const loginLogs = ref<UserLoginLog[]>([])
const loginLoading = ref(false)
const loginPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const categoryStats = ref<CategoryPurchase[]>([])
const purchaseLoading = ref(false)

const drawerVisible = ref(false)
const orderDetails = ref<PurchaseDetail[]>([])
const detailsLoading = ref(false)
const selectedCategory = ref<CategoryPurchase | null>(null)
const detailsPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const roleMap: Record<string, string> = {
  customer: '客户',
  sales: '销售',
  admin: '管理员'
}
const roleTypeMap: Record<string, string> = {
  customer: 'info',
  sales: 'warning',
  admin: 'danger'
}

function getRoleType(role: string) {
  return roleTypeMap[role] || 'info'
}

function getRoleText(role: string) {
  return roleMap[role] || role
}

function formatDate(date: string) {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsersSimple({
      search: searchKeyword.value || undefined,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.success) {
      users.value = res.data || []
      pagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

function viewUserDetail(user: SimpleUser) {
  currentUser.value = user
  activeTab.value = 'browse'
  browsePagination.page = 1
  loginPagination.page = 1
  detailsPagination.page = 1
  fetchBrowseLogs()
  fetchLoginLogs()
  fetchPurchaseSummary()
}

function goBack() {
  currentUser.value = null
  browseLogs.value = []
  loginLogs.value = []
  categoryStats.value = []
}

async function fetchBrowseLogs() {
  if (!currentUser.value) return
  browseLoading.value = true
  try {
    const res = await getUserBrowseLogs(currentUser.value.id, {
      page: browsePagination.page,
      page_size: browsePagination.pageSize
    })
    if (res.success) {
      browseLogs.value = res.data || []
      browsePagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load browse logs:', error)
  } finally {
    browseLoading.value = false
  }
}

async function fetchLoginLogs() {
  if (!currentUser.value) return
  loginLoading.value = true
  try {
    const res = await getUserLoginLogs(currentUser.value.id, {
      page: loginPagination.page,
      page_size: loginPagination.pageSize
    })
    if (res.success) {
      loginLogs.value = res.data || []
      loginPagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load login logs:', error)
  } finally {
    loginLoading.value = false
  }
}

async function fetchPurchaseSummary() {
  if (!currentUser.value) return
  purchaseLoading.value = true
  try {
    const res = await getUserPurchaseSummary(currentUser.value.id)
    if (res.success) {
      categoryStats.value = res.data || []
    }
  } catch (error) {
    console.error('Failed to load purchase summary:', error)
  } finally {
    purchaseLoading.value = false
  }
}

async function viewCategoryOrders(category: CategoryPurchase) {
  selectedCategory.value = category
  drawerVisible.value = true
  detailsPagination.page = 1
  fetchOrderDetails()
}

async function fetchOrderDetails() {
  if (!currentUser.value || !selectedCategory.value) return
  detailsLoading.value = true
  try {
    const res = await getUserPurchaseByCategory(
      currentUser.value.id,
      selectedCategory.value.category_id,
      {
        page: detailsPagination.page,
        page_size: detailsPagination.pageSize
      }
    )
    if (res.success) {
      orderDetails.value = res.data || []
      detailsPagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load order details:', error)
  } finally {
    detailsLoading.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped lang="scss">
.user-behavior-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0;
    font-size: 20px;
  }
}

.filter-section {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.user-detail-section {
  .detail-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;

    .user-info {
      font-size: 16px;
      font-weight: 600;
    }
  }
}

.user-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;

  p {
    margin-top: 16px;
    font-size: 14px;
  }
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    background: #ecf5ff;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-icon {
    color: #409eff;
  }

  .stat-info {
    flex: 1;

    .stat-name {
      font-size: 14px;
      color: #606266;
      margin-bottom: 4px;
    }

    .stat-quantity {
      font-size: 12px;
      color: #909399;
      margin-bottom: 4px;
    }

    .stat-amount {
      font-size: 16px;
      font-weight: 600;
      color: #f56c6c;
    }
  }
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>