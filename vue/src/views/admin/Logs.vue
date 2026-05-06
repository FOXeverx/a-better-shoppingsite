<template>
  <div class="admin-logs-page">
    <div class="page-header">
      <el-select v-model="actionFilter" placeholder="操作类型" clearable @change="fetchLogs">
        <el-option label="用户登录" value="LOGIN" />
        <el-option label="用户注册" value="REGISTER" />
        <el-option label="创建订单" value="CREATE_ORDER" />
        <el-option label="更新商品" value="UPDATE_PRODUCT" />
        <el-option label="删除商品" value="DELETE_PRODUCT" />
        <el-option label="更新用户" value="UPDATE_USER" />
      </el-select>
    </div>
    
    <el-table :data="logs" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="action" label="操作" width="140">
        <template #default="{ row }">
          <el-tag>{{ getActionText(row.action) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_type" label="目标类型" width="100" />
      <el-table-column prop="target_id" label="目标ID" width="80" />
      <el-table-column prop="created_at" label="操作时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchLogs"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getLogs } from '@/api/admin'
import type { LogEntry } from '@/types/admin'

const logs = ref<LogEntry[]>([])
const loading = ref(false)
const actionFilter = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

async function fetchLogs() {
  loading.value = true
  try {
    const res = await getLogs({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.success && res.data) {
      logs.value = res.data
      pagination.total = res.data.length
    }
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function getActionText(action: string) {
  const map: Record<string, string> = {
    LOGIN: '用户登录',
    REGISTER: '用户注册',
    CREATE_ORDER: '创建订单',
    UPDATE_PRODUCT: '更新商品',
    DELETE_PRODUCT: '删除商品',
    UPDATE_USER: '更新用户'
  }
  return map[action] || action
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped lang="scss">
.admin-logs-page {
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