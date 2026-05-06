<template>
  <div class="auth-layout">
    <div class="auth-container">
      <div class="auth-logo">
        <router-link to="/">
          <h1>电商平台</h1>
        </router-link>
      </div>
      <div class="auth-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped lang="scss">
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-container {
  width: 100%;
  max-width: 400px;
  padding: 20px;
}

.auth-logo {
  text-align: center;
  margin-bottom: 30px;
  
  a {
    color: #fff;
    
    h1 {
      font-size: 32px;
      font-weight: 700;
    }
  }
}

.auth-content {
  background: #fff;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
</style>