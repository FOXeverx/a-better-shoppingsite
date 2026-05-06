export type OrderStatus = 'CREATED' | 'CONFIRMED' | 'SHIPPED' | 'COMPLETED' | 'CANCELLED'

export interface OrderItem {
  product_id: number
  product_name: string
  quantity: number
  price: number
  subtotal?: number
  image_url?: string
}

export interface Order {
  id: number
  order_number: string
  status: OrderStatus
  total_amount: number
  shipping_address?: string
  note?: string
  items: OrderItem[]
  confirm_token?: string
  expires_at?: string
  confirmed_at?: string
  created_at: string
  updated_at?: string
}

export interface OrderCreate {
  shipping_address: string
  note?: string
}

export interface CartItem {
  id: number
  product: ProductBrief
  quantity: number
  subtotal: number
}

export interface ProductBrief {
  id: number
  name: string
  price: number
  image_url?: string
  stock?: number
}

export interface CartSummary {
  total_items: number
  total_amount: number
}

export interface CartState {
  items: CartItem[]
  summary: CartSummary | null
}