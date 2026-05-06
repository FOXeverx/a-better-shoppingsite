import { get, post } from '@/api'
import type { ApiResponse } from '@/types/api'

export const triggerRecommend = () => {
  return post<ApiResponse>('/admin/recommend/trigger')
}

export const getBoughtAlsoBought = (productId: number, limit: number = 5) => {
  return get<ApiResponse<any[]>>(`/recommend/bought-also/${productId}`, { params: { limit } })
}