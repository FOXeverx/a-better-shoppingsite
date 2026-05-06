import { get, post } from '@/api'
import type { ApiResponse, LoginRequest, LoginResponse, RegisterRequest, User } from '@/types/api'
import type { User as UserType } from '@/types/user'

export const login = (data: LoginRequest) => {
  return post<ApiResponse<LoginResponse>>('/auth/login', data)
}

export const register = (data: RegisterRequest) => {
  return post<ApiResponse<UserType>>('/auth/register', data)
}

export const logout = () => {
  return post<ApiResponse>('/auth/logout')
}

export const getCurrentUser = () => {
  return get<ApiResponse<User>>('/auth/me')
}