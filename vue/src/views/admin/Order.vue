<template>
  <div class="admin-order-page">
    <div class="page-header">
      <el-select v-model="statusFilter" placeholder="订单状态" clearable @change="fetchOrders">
        <el-option label="待确认" value="CREATED" />
        <el-option label="已确认" value="CONFIRMED" />
        <el-option label="配送中" value="SHIPPED" />
        <el-option label="已完成" value="COMPLETED" />
        <el-option label="已取消" value="CANCELLED" />
      </el-select>
    </div>
    
    <el-table :data="orders" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="order_number" label="订单号" width="180" />
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="total_amount" label="金额" width="100">
        <template #default="{ row }">
          ¥{{ (row.total_amount || 0).toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="shipping_address" label="收货地址" min-width="150" />
      <el-table-column prop="created_at" label="下单时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text @click="goToDetail(row.id)">查看</el-button>
          <el-dropdown @command="(cmd: string) => handleCommand(cmd, row.id, row.status)">
            <el-button type="primary" text>
              更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="CONFIRMED">确认订单</el-dropdown-item>
                <el-dropdown-item command="SHIPPED">标记发货</el-dropdown-item>
                <el-dropdown-item command="COMPLETED">完成订单</el-dropdown-item>
                <el-dropdown-item command="CANCELLED" divided>取消订单</el-dropdown-item>
                <template v-if="authStore.isAdmin">
                  <el-dropdown-item command="DELETE" divided>删除订单</el-dropdown-item>
                </template>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchOrders"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { getAllOrders, updateOrderStatus, deleteOrder } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import type { AdminOrder } from '@/types/admin'
import type { OrderStatus } from '@/types/order'

const router = useRouter()
const authStore = useAuthStore()

const orders = ref<AdminOrder[]>([])
const loading = ref(false)
const statusFilter = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

async function fetchOrders() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    console.log('Fetching orders with params:', params)
    const res = await getAllOrders(params)
    console.log('Orders response:', res)
    if (res.success) {
      orders.value = res.data || []
      if (res.pagination) {
        pagination.total = res.pagination.total || 0
      }
    }
  } catch (error) {
    console.error('Failed to load orders:', error)
  } finally {
    loading.value = false
  }
}

async function handleCommand(cmd: string, id: number, currentStatus: string) {
  if (cmd === 'DELETE') {
    try {
      await ElMessageBox.confirm('确定要删除该订单吗？此操作不可恢复。', '警告', {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'error'
      })
      
      const res = await deleteOrder(id)
      if (res.success) {
        ElMessage.success('订单已删除')
        fetchOrders()
      }
    } catch (error) {
      console.error('Failed to delete order:', error)
    }
    return
  }
  
  if (cmd === currentStatus) return
  
  try {
    await ElMessageBox.confirm(`确定要将订单状态修改为"${getStatusText(cmd as OrderStatus)}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await updateOrderStatus(id, cmd)
    if (res.success) {
      ElMessage.success('状态更新成功')
      fetchOrders()
    }
  } catch (error) {
    console.error('Failed to update status:', error)
  }
}

function goToDetail(id: number) {
  router.push(`/admin/order/${id}`)
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function getStatusType(status: OrderStatus) {
  const map: Record<OrderStatus, string> = {
    CREATED: 'warning',
    CONFIRMED: 'success',
    SHIPPED: 'info',
    COMPLETED: 'success',
    CANCELLED: 'danger'
  }
  return map[status] || 'info'
}

function getStatusText(status: OrderStatus) {
  const map: Record<OrderStatus, string> = {
    CREATED: '待确认',
    CONFIRMED: '已确认',
    SHIPPED: '配送中',
    COMPLETED: '已完成',
    CANCELLED: '已取消'
  }
  return map[status] || status
}

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped lang="scss">
.admin-order-page {
  .page-header {
    margin-bottom: 20px;
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}
</style>