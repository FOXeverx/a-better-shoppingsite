<template>
  <div class="admin-user-page">
    <div class="page-header">
      <el-button type="primary" @click="handleAdd">新增用户</el-button>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户..."
        style="width: 200px"
        @keyup.enter="fetchUsers"
      />
    </div>
    
    <el-table :data="users" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="getRoleType(row.role)">
            {{ getRoleText(row.role) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" text @click="handleDelete(row)">删除</el-button>
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
    
    <el-dialog
      v-model="dialogVisible"
      title="用户管理"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role">
            <el-option label="普通用户" value="customer" />
            <el-option label="销售" value="sales" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/admin'
import type { AdminUser } from '@/types/admin'

const users = ref<AdminUser[]>([])
const loading = ref(false)
const searchKeyword = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingUserId = ref<number | null>(null)
const submitting = ref(false)

const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  email: '',
  password: '',
  role: 'customer' as 'customer' | 'sales' | 'admin'
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUserList({
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.success && res.data) {
      users.value = res.data
      pagination.total = res.data.length
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editingUserId.value = null
  Object.assign(form, {
    username: '',
    email: '',
    password: '',
    role: 'customer'
  })
  dialogVisible.value = true
}

function handleEdit(row: AdminUser) {
  isEdit.value = true
  editingUserId.value = row.id
  Object.assign(form, {
    username: row.username,
    email: row.email,
    password: '',
    role: row.role
  })
  dialogVisible.value = true
}

async function handleDelete(row: AdminUser) {
  try {
    await ElMessageBox.confirm('确定要删除该用户吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await deleteUser(row.id)
    if (res.success) {
      ElMessage.success('删除成功')
      fetchUsers()
    }
  } catch {
    // User cancelled
  }
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      let res
      if (isEdit.value && editingUserId.value) {
        res = await updateUser(editingUserId.value, {
          email: form.email,
          password: form.password || undefined,
          role: form.role
        })
      } else {
        res = await createUser({
          username: form.username,
          email: form.email,
          password: form.password,
          role: form.role
        })
      }
      if (res.success) {
        ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
        dialogVisible.value = false
        fetchUsers()
      }
    } catch (error) {
      console.error('Failed to save user:', error)
    } finally {
      submitting.value = false
    }
  })
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

function getRoleType(role: string) {
  const map: Record<string, string> = {
    customer: 'info',
    sales: 'warning',
    admin: 'danger'
  }
  return map[role] || 'info'
}

function getRoleText(role: string) {
  const map: Record<string, string> = {
    customer: '普通用户',
    sales: '销售',
    admin: '管理员'
  }
  return map[role] || role
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped lang="scss">
.admin-user-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}
</style>