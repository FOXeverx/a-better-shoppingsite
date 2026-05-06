<template>
  <div class="login-container">
    <h2 class="form-title">登录</h2>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-position="top"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="form.username"
          placeholder="请输入用户名或邮箱"
          prefix-icon="User"
        />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          type="password"
          placeholder="请输入密码"
          prefix-icon="Lock"
          show-password
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
          class="submit-btn"
        >
          登录
        </el-button>
      </el-form-item>
      <div class="forgot-link">
        <span class="forgot-btn" @click="showForgotDialog = true">忘记密码？</span>
      </div>
    </el-form>
    <div class="form-footer">
      <span>还没有账号？</span>
      <router-link to="/register">立即注册</router-link>
    </div>

    <el-dialog v-model="showForgotDialog" title="找回密码" width="400px">
      <el-form :model="forgotForm" :rules="forgotRules" ref="forgotFormRef" label-position="top">
        <el-form-item label="用户名或邮箱" prop="username">
          <el-input v-model="forgotForm.username" placeholder="请输入用户名或注册邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForgotDialog = false">取消</el-button>
        <el-button type="primary" :loading="forgotLoading" @click="handleForgotPassword">发送新密码</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const showForgotDialog = ref(false)
const forgotLoading = ref(false)
const forgotFormRef = ref<FormInstance>()
const forgotForm = reactive({
  username: ''
})
const forgotRules: FormRules = {
  username: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }]
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

import { post } from '@/api'

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    const success = await authStore.login(form.username, form.password)
    loading.value = false
    
    if (success) {
      ElMessage.success('登录成功')
      const redirect = route.query.redirect as string
      router.push(redirect || '/')
    } else {
      ElMessage.error('用户名或密码错误')
    }
  })
}

async function handleForgotPassword() {
  if (!forgotFormRef.value) return
  
  await forgotFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    forgotLoading.value = true
    try {
      const res = await post<{ success: boolean; message: string }>('/auth/forgot-password', forgotForm)
      ElMessage.success(res.message)
      showForgotDialog.value = false
    } catch {
      ElMessage.error('发送失败')
    } finally {
      forgotLoading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  width: 100%;
}

.form-title {
  text-align: center;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 30px;
  color: #303133;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.form-footer {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #606266;
  
  a {
    color: #409eff;
    margin-left: 8px;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.forgot-link {
  text-align: center;
  margin-bottom: 20px;
  
  .forgot-btn {
    color: #409eff;
    font-size: 14px;
    cursor: pointer;
    
    &:hover {
      text-decoration: underline;
    }
  }
}
</style>