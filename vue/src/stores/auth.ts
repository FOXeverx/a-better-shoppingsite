import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, UserRole } from '@/types/user'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || 'customer')
  const isAdmin = computed(() => userRole.value === 'admin')
  const isSales = computed(() => userRole.value === 'sales' || userRole.value === 'admin')

  function init() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login({ username, password })
      if (res.success && res.data) {
        token.value = res.data.token
        user.value = res.data.user
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('user', JSON.stringify(res.data.user))
        return true
      }
      return false
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.register({ username, email, password, confirm_password: password })
      if (res.success) {
        return true
      }
      return false
    } catch (error) {
      console.error('Register failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  async function fetchCurrentUser() {
    if (!token.value) return
    loading.value = true
    try {
      const res = await authApi.getCurrentUser()
      if (res.success && res.data) {
        user.value = res.data
        localStorage.setItem('user', JSON.stringify(res.data))
      }
    } catch (error) {
      console.error('Fetch user failed:', error)
      logout()
    } finally {
      loading.value = false
    }
  }

  function hasRole(roles: UserRole | UserRole[]): boolean {
    if (!user.value) return false
    const roleList = Array.isArray(roles) ? roles : [roles]
    return roleList.includes(user.value.role)
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    userRole,
    isAdmin,
    isSales,
    init,
    login,
    register,
    logout,
    fetchCurrentUser,
    hasRole
  }
})