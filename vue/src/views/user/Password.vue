<template>
  <div class="password-page container">
    <div class="page-header">
      <h1>修改密码</h1>
    </div>
    
    <div class="password-content">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        class="password-form"
      >
        <el-form-item label="当前密码" prop="old_password">
          <el-input
            v-model="form.old_password"
            type="password"
            placeholder="请输入当前密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="form.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirm_password">
          <el-input
            v-model="form.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="验证码" prop="verification_code">
          <el-input
            v-model="form.verification_code"
            placeholder="请输入邮箱收到的验证码"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            修改密码
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { changePassword } from '@/api/user'

const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
  verification_code: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== form.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  old_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const res = await changePassword({
        old_password: form.old_password,
        new_password: form.new_password,
        verification_code: form.verification_code
      })
      if (res.success) {
        ElMessage.success('密码修改成功，请重新登录')
        handleReset()
        setTimeout(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          window.location.href = '/login'
        }, 1500)
      }
    } catch (error) {
      console.error('Failed to change password:', error)
    } finally {
      submitting.value = false
    }
  })
}

function handleReset() {
  form.old_password = ''
  form.new_password = ''
  form.confirm_password = ''
  formRef.value?.resetFields()
}
</script>

<style scoped lang="scss">
.password-page {
  padding: 20px 0;
}

.page-header {
  margin-bottom: 20px;
  
  h1 {
    font-size: 24px;
    font-weight: 600;
  }
}

.password-content {
  background: #fff;
  border-radius: 8px;
  padding: 30px;
  max-width: 600px;
}

.password-form {
  .el-input {
    width: 100%;
  }
}
</style>