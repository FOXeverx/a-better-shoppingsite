import { get, post, put, del } from '@/api'
import type { ApiResponse, CartAddRequest, CartUpdateRequest } from '@/types/api'
import type { CartItem, CartSummary } from '@/types/order'

export const getCart = () => {
  return get<ApiResponse<CartItem[]> & { summary?: CartSummary }>('/cart')
}

export const addToCart = (data: CartAddRequest) => {
  return post<ApiResponse>('/cart', data)
}

export const updateCartItem = (id: number, data: CartUpdateRequest) => {
  return put<ApiResponse>(`/cart/${id}`, data)
}

export const removeCartItem = (id: number) => {
  return del<ApiResponse>(`/cart/${id}`)
}

export const clearCart = () => {
  return del<ApiResponse>('/cart')
}