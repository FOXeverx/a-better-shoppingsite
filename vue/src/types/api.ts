import type { User } from './user'
export type { User }

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: {
    code: string
    message: string
  }
  pagination?: Pagination
}

export interface Pagination {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export interface LoginResponse {
  token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface UpdateUserRequest {
  email?: string
  username?: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface ProductCreateRequest {
  name: string
  description?: string
  price: number
  stock: number
  category_id?: number
  image_url?: string
}

export interface ProductUpdateRequest {
  name?: string
  description?: string
  price?: number
  stock?: number
  category_id?: number
  image_url?: string
  is_active?: boolean
}

export interface ProductListParams {
  page?: number
  page_size?: number
  category_id?: number
  search?: string
  min_price?: number
  max_price?: number
  sort?: string
  order?: string
}

export interface CartAddRequest {
  product_id: number
  quantity: number
}

export interface CartUpdateRequest {
  quantity: number
}

export interface OrderCreateRequest {
  shipping_address: string
  note?: string
}

export interface OrderConfirmParams {
  token: string
}

export interface AdminUserCreateRequest {
  username: string
  email: string
  password: string
  role: 'customer' | 'sales' | 'admin'
}

export interface StatsParams {
  period?: 'daily' | 'weekly' | 'monthly'
  start_date?: string
  end_date?: string
}