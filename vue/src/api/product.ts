import { get, post, put, del } from '@/api'
import type { ApiResponse, ProductListParams, ProductCreateRequest, ProductUpdateRequest } from '@/types/api'
import type { Product, ProductListItem, ProductDetail, ProductRecommend, Category } from '@/types/product'
import type { Pagination } from '@/types/api'

export const getProductList = (params?: ProductListParams) => {
  return get<ApiResponse<ProductListItem[]>>('/product', { params })
}

export const getCategoryList = () => {
  return get<ApiResponse<Category[]>>('/product/category/list')
}

export const getCategoryFlatList = () => {
  return get<ApiResponse<{ id: number; name: string; parent_id: number | null }[]>>('/product/category')
}

export const createCategory = (data: { name: string; parent_id?: number }) => {
  return post<ApiResponse<{ id: number; name: string; parent_id: number | null }>>('/product/category', data)
}

export const updateCategory = (id: number, data: { name: string; parent_id?: number }) => {
  return put<ApiResponse<{ id: number; name: string; parent_id: number | null }>>(`/product/category/${id}`, data)
}

export const deleteCategory = (id: number) => {
  return del<ApiResponse>(`/product/category/${id}`)
}

export const getProductDetail = (id: number) => {
  return get<ApiResponse<ProductDetail>>(`/product/${id}`)
}

export const createProduct = (data: ProductCreateRequest) => {
  return post<ApiResponse<Product>>('/product', data)
}

export const updateProduct = (id: number, data: ProductUpdateRequest) => {
  return put<ApiResponse<Product>>(`/product/${id}`, data)
}

export const deleteProduct = (id: number) => {
  return del<ApiResponse>(`/product/${id}`)
}

export const getProductRecommend = (productId: number) => {
  return get<ApiResponse<ProductRecommend[]>>(`/recommend/product/${productId}`)
}

export const getUserRecommend = () => {
  return get<ApiResponse<ProductRecommend[]>>('/recommend/user/me')
}

export const logBrowse = (productId: number, stayTime: number = 0) => {
  return post<ApiResponse>('/log/browse', { product_id: productId, stay_time: stayTime })
}

export const uploadImage = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return post<ApiResponse<{ url: string; filename: string }>>('/upload/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export interface Comment {
  id: number
  product_id: number
  user_id: number
  username: string
  content: string
  created_at: string
}

export const getProductComments = (productId: number) => {
  return get<ApiResponse<Comment[]>>(`/product/${productId}/comments`)
}

export const addProductComment = (productId: number, content: string) => {
  return post<ApiResponse<Comment>>(`/product/${productId}/comments`, { content })
}

export const deleteProductComment = (commentId: number) => {
  return del<ApiResponse>(`/product/comments/${commentId}`)
}