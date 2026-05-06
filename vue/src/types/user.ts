export type UserRole = 'customer' | 'sales' | 'admin'

export interface User {
  id: number
  username: string
  email: string
  role: UserRole
  is_active: boolean
  last_login_at?: string
  created_at: string
}

export interface UserProfile extends User {
  avatar?: string
  phone?: string
  address?: string
}

export interface UserState {
  user: User | null
  token: string | null
  isLoggedIn: boolean
}