import { get, post } from '@/api'
import instance from '@/api'
import type { ApiResponse, OrderCreateRequest } from '@/types/api'
import type { Order } from '@/types/order'

export const createOrder = (data: OrderCreateRequest) => {
  return post<ApiResponse<Order>>('/order', data)
}

export const getOrderList = (params?: { page?: number; page_size?: number; status?: string }) => {
  return get<ApiResponse<Order[]>>('/order', { params: params || {} })
}

export const getOrderDetail = (id: number) => {
  return get<ApiResponse<Order>>(`/order/${id}`)
}

export const confirmOrder = (token: string) => {
  return instance.get('/order/confirm', { params: { token } })
}

export const cancelOrder = (id: number) => {
  return post<ApiResponse>(`/order/${id}/cancel`)
}