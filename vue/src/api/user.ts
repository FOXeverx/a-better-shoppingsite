import { get, put, del } from '@/api'
import type { ApiResponse, UpdateUserRequest, ChangePasswordRequest } from '@/types/api'
import type { User } from '@/types/user'

export const getUserProfile = () => {
  return get<ApiResponse<User>>('/user/me')
}

export const updateUserProfile = (data: UpdateUserRequest) => {
  return put<ApiResponse<User>>('/user/me', data)
}

export const changePassword = (data: ChangePasswordRequest) => {
  return put<ApiResponse>('/user/password', data)
}

export const deleteAccount = (password: string) => {
  return del<ApiResponse>('/user/me', { data: { password } })
}