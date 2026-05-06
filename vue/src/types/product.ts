export interface Category {
  id: number
  name: string
  parent_id: number | null
  children?: Category[]
}

export interface Product {
  id: number
  name: string
  description?: string
  price: number
  stock: number
  category_id?: number
  category?: Category
  image_url?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface ProductDetail extends Product {
  sales_count?: number
  rating?: number
}

export interface ProductListItem {
  id: number
  name: string
  description?: string
  price: number
  stock: number
  category_id?: number
  image_url?: string
  is_active: boolean
  created_at: string
}

export interface ProductRecommend {
  product_id: number
  product_name: string
  score: number
  image_url?: string
  reason?: string
}