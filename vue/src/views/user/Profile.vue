<template>
  <div class="profile-page container">
    <div class="page-header">
      <h1>个人资料</h1>
    </div>
    
    <div class="profile-content">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="profile-form"
      >
        <el-form-item label="用户名">
          <el-input v-model="form.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag :type="getRoleType(authStore.user?.role || 'customer')">
            {{ getRoleText(authStore.user?.role || 'customer') }}
          </el-tag>
        </el-form-item>
        <el-form-item label="注册时间">
          <span>{{ formatDate(authStore.user?.created_at) }}</span>
        </el-form-item>
        <el-form-item label="最后登录">
          <span>{{ formatDate(authStore.user?.last_login_at) }}</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存修改
          </el-button>
        </el-form-item>
      </el-form>

        <div class="password-section">
        <h3>修改密码</h3>
        <el-form
          ref="passwordFormRef"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="100px"
        >
          <el-form-item label="当前密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="验证码" prop="verification_code">
            <div class="code-row">
              <el-input v-model="passwordForm.verification_code" placeholder="请输入邮箱验证码" />
              <el-button :loading="codeSending" :disabled="codeSent" @click="sendCode">
                {{ codeSent ? `${codeCountdown}s` : '发送验证码' }}
              </el-button>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="warning" @click="handleChangePassword" :loading="passwordChanging">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="danger-section">
        <h3>永久注销</h3>
        <p class="warning-text">注销后将无法恢复账号，请谨慎操作</p>
        <el-form
          ref="deleteFormRef"
          :model="deleteForm"
          :rules="deleteRules"
          label-width="100px"
        >
          <el-form-item label="登录密码" prop="password">
            <el-input v-model="deleteForm.password" type="password" show-password placeholder="请输入当前密码" />
          </el-form-item>
          <el-form-item>
            <el-button type="danger" @click="handleDeleteAccount" :loading="deleting">
              永久注销账户
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { updateUserProfile, deleteAccount } from '@/api/user'
import { post } from '@/api'
import type { UserRole } from '@/types/user'

const authStore = useAuthStore()
const router = useRouter()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const passwordFormRef = ref<FormInstance>()
const passwordChanging = ref(false)
const codeSending = ref(false)
const codeSent = ref(false)
const codeCountdown = ref(0)
let codeCountdownTimer: ReturnType<typeof setInterval> | null = null

onUnmounted(() => {
  if (codeCountdownTimer) {
    clearInterval(codeCountdownTimer)
    codeCountdownTimer = null
  }
})

const form = reactive({
  username: '',
  email: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  verification_code: ''
})

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

const deleteFormRef = ref<FormInstance>()
const deleting = ref(false)
const deleteForm = reactive({
  password: ''
})

const deleteRules: FormRules = {
  password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ]
}

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const res = await updateUserProfile({ email: form.email })
      if (res.success) {
        ElMessage.success('保存成功')
        if (authStore.user) {
          authStore.user.email = form.email
          localStorage.setItem('user', JSON.stringify(authStore.user))
        }
      }
    } catch (error) {
      console.error('Failed to update profile:', error)
    } finally {
      submitting.value = false
    }
  })
}

function formatDate(date?: string) {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

function getRoleType(role: UserRole) {
  const map: Record<UserRole, string> = {
    customer: 'info',
    sales: 'warning',
    admin: 'danger'
  }
  return map[role]
}

function getRoleText(role: UserRole) {
  const map: Record<UserRole, string> = {
    customer: '普通用户',
    sales: '销售',
    admin: '管理员'
  }
  return map[role]
}

async function sendCode() {
  if (codeSent.value) return
  
  codeSending.value = true
  try {
    const res = await post<{ success: boolean; message: string }>('/auth/send-change-password-code')
    if (res.success) {
      ElMessage.success('验证码已发送到您的邮箱')
      codeSent.value = true
      codeCountdown.value = 300
      if (codeCountdownTimer) clearInterval(codeCountdownTimer)
      codeCountdownTimer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0) {
          if (codeCountdownTimer) {
            clearInterval(codeCountdownTimer)
            codeCountdownTimer = null
          }
          codeSent.value = false
        }
      }, 1000)
    }
  } catch {
    ElMessage.error('发送失败')
  } finally {
    codeSending.value = false
  }
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordChanging.value = true
    try {
      const res = await post<{ success: boolean; message: string }>('/auth/change-password', passwordForm)
      if (res.success) {
        ElMessage.success('密码修改成功，请重新登录')
        passwordForm.old_password = ''
        passwordForm.new_password = ''
        passwordForm.verification_code = ''
        setTimeout(() => {
          authStore.logout()
          router.push('/login')
        }, 1500)
      }
    } catch (error: any) {
      ElMessage.error(error?.response?.data?.detail || '修改失败')
    } finally {
      passwordChanging.value = false
    }
  })
}

async function handleDeleteAccount() {
  if (!deleteFormRef.value) return
  
  try {
    await ElMessageBox.confirm(
      '确定要永久注销您的账户吗？此操作不可恢复！',
      '警告',
      {
        confirmButtonText: '确定注销',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await deleteFormRef.value.validate(async (valid) => {
      if (!valid) return
      
      deleting.value = true
      try {
        const res = await deleteAccount(deleteForm.password)
        if (res.success) {
          ElMessage.success('账户已注销')
          setTimeout(() => {
            authStore.logout()
            router.push('/login')
          }, 1500)
        }
      } catch (error: any) {
        ElMessage.error(error?.response?.data?.detail || '注销失败')
      } finally {
        deleting.value = false
      }
    })
  } catch {
    // User cancelled
  }
}

onMounted(() => {
  if (authStore.user) {
    form.username = authStore.user.username
    form.email = authStore.user.email
  }
})
</script>

<style scoped lang="scss">
.profile-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.profile-content {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  max-width: 600px;
}

.profile-form {
  .el-input,
  .el-select {
    width: 100%;
  }
}

.password-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #ebeef5;
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 20px;
  }
  
  .code-row {
    display: flex;
    gap: 10px;
    
    .el-input {
      flex: 1;
    }
  }
}

.danger-section {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 1px solid #f56c6c;
  
  h3 {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #f56c6c;
  }
  
  .warning-text {
    color: #909399;
    font-size: 14px;
    margin-bottom: 20px;
  }
}
</style>