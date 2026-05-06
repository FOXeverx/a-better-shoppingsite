<template>
  <header class="app-header">
    <div class="container header-content">
      <div class="logo">
        <router-link to="/">
          <h1>电商平台</h1>
        </router-link>
      </div>
      
      <nav class="nav-links">
        <router-link to="/products">全部商品</router-link>
      </nav>
      
      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索商品"
          @keyup.enter="handleSearch"
          :prefix-icon="Search"
        />
      </div>
      
      <div class="header-actions">
        <router-link to="/cart" class="cart-link">
          <el-badge :value="cartStore.totalItems" :hidden="cartStore.totalItems === 0">
            <el-icon :size="24"><ShoppingCart /></el-icon>
          </el-badge>
          <span>购物车</span>
        </router-link>
        
        <template v-if="authStore.isLoggedIn">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ authStore.user?.username }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="orders">我的订单</el-dropdown-item>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="recommend">个性化推荐</el-dropdown-item>
                <el-dropdown-item command="admin" v-if="authStore.isSales">管理后台</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <router-link to="/login" class="auth-link">登录</router-link>
          <router-link to="/register" class="auth-link">注册</router-link>
        </template>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ShoppingCart, User } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()

const searchKeyword = ref('')

function handleSearch() {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/products', query: { search: searchKeyword.value } })
  }
}

function handleUserCommand(command: string) {
  switch (command) {
    case 'orders':
      router.push('/orders')
      break
    case 'profile':
      router.push('/user/profile')
      break
    case 'recommend':
      router.push('/recommend')
      break
    case 'admin':
      if (authStore.user?.role === 'admin') {
        router.push('/admin')
      } else if (authStore.user?.role === 'sales') {
        router.push('/sales')
      }
      break
    case 'logout':
      authStore.logout()
      router.push('/')
      break
  }
}
</script>

<style scoped lang="scss">
.app-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  height: 64px;
  gap: 20px;
}

.logo {
  h1 {
    font-size: 24px;
    font-weight: 700;
    color: #409eff;
  }
}

.nav-links {
  display: flex;
  gap: 20px;
  
  a {
    font-size: 15px;
    color: #606266;
    transition: color 0.3s;
    
    &:hover,
    &.router-link-active {
      color: #409eff;
    }
  }
}

.search-box {
  flex: 1;
  max-width: 400px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  
  .cart-link {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #606266;
    
    &:hover {
      color: #409eff;
    }
  }
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    color: #606266;
    
    &:hover {
      color: #409eff;
    }
  }
  
  .auth-link {
    color: #409eff;
    padding: 6px 12px;
    border: 1px solid #409eff;
    border-radius: 4px;
    font-size: 14px;
    transition: all 0.3s;
    
    &:hover {
      background: #409eff;
      color: #fff;
    }
  }
}
</style>