import { get, post, put, del } from '@/api'
import type { ApiResponse, AdminUserCreateRequest, StatsParams } from '@/types/api'
import type { AdminStats, LogEntry, Anomaly, AdminUser, AdminOrder, ProductSales, BrowseLog } from '@/types/admin'
import type { Pagination } from '@/types/api'

export const getStats = (params?: StatsParams) => {
  return get<ApiResponse<AdminStats>>('/admin/stats', { params })
}

export const getProductSales = (params?: { start_date?: string; end_date?: string; limit?: number }) => {
  return get<ApiResponse<ProductSales[]>>('/admin/product-sales', { params })
}

export const getAllOrders = (params?: { page?: number; page_size?: number; status?: string }) => {
  return get<ApiResponse<{ data: AdminOrder[], pagination: Pagination }>>('/admin/orders', { params: params || {} })
}

export const getOrderDetail = (id: number) => {
  return get<ApiResponse<AdminOrder>>(`/admin/order/${id}`)
}

export const updateOrderStatus = (id: number, status: string) => {
  return put<ApiResponse>(`/admin/order/${id}/status`, {}, { params: { status } })
}

export const deleteOrder = (id: number) => {
  return del<ApiResponse>(`/admin/order/${id}`)
}

export const getUserList = (params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<AdminUser[]>>('/admin/users', { params })
}

export const createUser = (data: AdminUserCreateRequest) => {
  return post<ApiResponse<AdminUser>>('/admin/user', data)
}

export const getLogs = (params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<LogEntry[]>>('/admin/logs', { params })
}

export const getBrowseLogs = (params?: { page?: number; page_size?: number; product_id?: number; user_id?: number }) => {
  return get<any>('/admin/logs/browse', { params: params || {} })
}

export const getAnomalies = (params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<Anomaly[]>>('/admin/anomalies', { params })
}

export const updateUserStatus = (id: number, isActive: boolean) => {
  return post<ApiResponse>(`/admin/user/${id}/status`, { is_active: isActive })
}

export const deleteUser = (id: number) => {
  return del<ApiResponse>(`/admin/user/${id}`)
}

export const getUserStats = () => {
  return get<ApiResponse<any>>('/admin/user-stats')
}

export const getAnomalyStats = () => {
  return get<ApiResponse<any>>('/admin/anomaly-stats')
}

export const resolveAnomaly = (id: number) => {
  return post<ApiResponse>(`/admin/anomaly/${id}/resolve`)
}

export const getSalesPrediction = (days?: number) => {
  return get<ApiResponse<any>>('/admin/sales-predict', { params: { days } })
}

export interface SimpleUser {
  id: number
  username: string
  email: string
  role: string
  created_at: string
}

export interface UserBrowseLog {
  id: number
  product_id: number
  product_name: string
  stay_time: number
  created_at: string
}

export interface UserLoginLog {
  id: number
  ip_address: string
  user_agent: string
  success: boolean
  created_at: string
}

export interface CategoryPurchase {
  category_id: number
  category_name: string
  total_quantity: number
  total_amount: number
}

export interface PurchaseDetail {
  order_id: number
  order_number: string
  created_at: string
  product_id: number
  product_name: string
  quantity: number
  price: number
  subtotal: number
}

export const getUsersSimple = (params?: { search?: string; page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: SimpleUser[], pagination: Pagination }>>('/admin/users/simple', { params: params || {} })
}

export const getUserBrowseLogs = (userId: number, params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: UserBrowseLog[], pagination: Pagination }>>(`/admin/user/${userId}/browse`, { params: params || {} })
}

export const getUserLoginLogs = (userId: number, params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: UserLoginLog[], pagination: Pagination }>>(`/admin/user/${userId}/logins`, { params: params || {} })
}

export const getUserPurchaseSummary = (userId: number) => {
  return get<ApiResponse<CategoryPurchase[]>>(`/admin/user/${userId}/purchases/summary`)
}

export const getUserPurchaseByCategory = (userId: number, categoryId: number, params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: PurchaseDetail[], pagination: Pagination }>>(`/admin/user/${userId}/purchases/${categoryId}`, { params: params || {} })
}

export interface SecurityThreat {
  id: number
  threat_type: string
  ip_address: string
  user_agent: string
  details: any
  severity: string
  is_resolved: boolean
  created_at: string
  resolved_at: string | null
}

export interface IPBlock {
  id: number
  ip_address: string
  block_type: string
  reason: string
  expires_at: string | null
  created_by_id: number | null
  created_at: string
}

export interface ThreatStats {
  total: number
  unresolved: number
  high_critical: number
  today: number
}

export const getSecurityThreats = (params?: { threat_type?: string; severity?: string; is_resolved?: boolean; page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: SecurityThreat[], pagination: Pagination }>>('/admin/security/threats', { params: params || {} })
}

export const resolveThreat = (threatId: number) => {
  return post<ApiResponse>(`/admin/security/threats/${threatId}/resolve`)
}

export const getThreatStats = () => {
  return get<ApiResponse<ThreatStats>>('/admin/security/threats/stats')
}

export const getIPBlocks = (params?: { page?: number; page_size?: number }) => {
  return get<ApiResponse<{ data: IPBlock[], pagination: Pagination }>>('/admin/security/ip-blocks', { params: params || {} })
}

export const createIPBlock = (data: { ip_address: string; reason?: string; expires_minutes?: number }) => {
  return post<ApiResponse>('/admin/security/ip-blocks', data)
}

export const unblockIP = (blockId: number) => {
  return del<ApiResponse>(`/admin/security/ip-blocks/${blockId}`)
}