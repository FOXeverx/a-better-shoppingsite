import { get } from '@/api'
import type { ApiResponse } from '@/types/api'
import type { Category } from '@/types/product'

export const getCategoryList = () => {
  return get<ApiResponse<Category[]>>('/product/category/list')
}