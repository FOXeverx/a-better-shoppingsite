<template>
  <div class="not-found-page">
    <div class="content">
      <h1>404</h1>
      <p>页面未找到</p>
      <el-button type="primary" @click="$router.push('/')">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.not-found-page {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
  
  .content {
    text-align: center;
    
    h1 {
      font-size: 120px;
      font-weight: 700;
      color: #409eff;
      margin-bottom: 20px;
    }
    
    p {
      font-size: 24px;
      color: #606266;
      margin-bottom: 30px;
    }
  }
}
</style>