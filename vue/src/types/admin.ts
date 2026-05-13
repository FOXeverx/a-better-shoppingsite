import type { User } from './user'

export interface AdminStats {
  total_amount: number
  total_orders: number
  total_users: number
  trend: StatsTrend[]
}

export interface StatsTrend {
  date: string
  amount: number
  orders: number
}

export interface LogEntry {
  id: number
  user_id: number
  username: string
  action: string
  target_type: string
  target_id: number
  created_at: string
}

export interface Anomaly {
  id: number
  anomaly_type: string
  description: string
  severity: 'low' | 'medium' | 'high'
  details: any
  is_resolved: boolean
  created_at: string
  resolved_at: string | null
}

export interface AdminUser extends User {
  is_active: boolean
  created_at: string
}

export interface AdminOrderItem {
  product_id: number
  product_name: string
  quantity: number
  price: number
  subtotal: number
}

export interface AdminOrder {
  id: number
  order_number: string
  user_id: number
  username: string
  status: string
  total_amount: number
  shipping_address?: string
  items: AdminOrderItem[]
  created_at: string
  confirmed_at?: string
}

export interface ProductSales {
  product_id: number
  product_name: string
  quantity: number
  revenue: number
  order_count: number
}

export interface BrowseLog {
  id: number
  user_id: number
  username: string
  product_id: number
  product_name: string
  stay_time: number
  created_at: string
}

export interface UserStats {
  total_users: number
  spending_distribution: {
    low: number
    medium: number
    high: number
  }
  avg_spent: number
  avg_orders: number
  region_distribution: Record<string, number>
}

export interface AnomalyStats {
  total: number
  unresolved: number
  by_severity: {
    high: number
    medium: number
    low: number
  }
  last_24h: number
}

export interface SalesPrediction {
  trend: string
  current_avg: number
  prediction: number
  confidence: number
  recent_data: { date: string; amount: number }[]
}

export type OrderStatus = 'CREATED' | 'CONFIRMED' | 'SHIPPED' | 'DELIVERED' | 'CANCELLED'