import axios, { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const instance: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

instance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

instance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      if (status === 401) {
        const message = data?.detail || '登录已过期，请重新登录'
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        import('@/stores/auth').then(({ useAuthStore }) => {
          const authStore = useAuthStore()
          authStore.user = null
          authStore.token = null
        })
        ElMessage.error(message)
        router.push('/login')
      } else if (status === 403) {
        const message = data?.detail || '您没有权限执行此操作'
        ElMessage.error(message)
      } else if (status === 429) {
        ElMessage.error('请求过于频繁，请稍后再试')
      } else {
        const message = data?.error?.message || data?.detail || data?.message || '请求失败'
        ElMessage.error(message)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

export default instance

export function request<T = any>(config: AxiosRequestConfig): Promise<T> {
  return instance(config) as Promise<T>
}

export function get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'GET', url, params: config?.params })
}

export function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'POST', url, data })
}

export function put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'PUT', url, data })
}

export function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return request({ ...config, method: 'DELETE', url })
}