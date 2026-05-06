import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/home/Index.vue'),
    meta: { title: '首页', public: true }
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', public: true, layout: 'auth' }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', public: true, layout: 'auth' }
  },
  {
    path: '/products',
    name: 'products',
    component: () => import('@/views/product/List.vue'),
    meta: { title: '商品列表', public: true }
  },
  {
    path: '/product/:id',
    name: 'product-detail',
    component: () => import('@/views/product/Detail.vue'),
    meta: { title: '商品详情', public: true }
  },
  {
    path: '/category/:id',
    name: 'category',
    component: () => import('@/views/category/Index.vue'),
    meta: { title: '分类商品', public: true }
  },
  {
    path: '/cart',
    name: 'cart',
    component: () => import('@/views/cart/Index.vue'),
    meta: { title: '购物车', requiresAuth: true }
  },
  {
    path: '/order/confirm',
    name: 'order-confirm',
    component: () => import('@/views/order/Confirm.vue'),
    meta: { title: '确认订单', requiresAuth: true }
  },
  {
    path: '/order-confirmed',
    name: 'order-confirmed',
    component: () => import('@/views/order/Confirmed.vue'),
    meta: { title: '订单确认', public: true }
  },
  {
    path: '/orders',
    name: 'orders',
    component: () => import('@/views/order/List.vue'),
    meta: { title: '我的订单', requiresAuth: true }
  },
  {
    path: '/order/:id',
    name: 'order-detail',
    component: () => import('@/views/order/Detail.vue'),
    meta: { title: '订单详情', requiresAuth: true }
  },
  {
    path: '/user/profile',
    name: 'profile',
    component: () => import('@/views/user/Profile.vue'),
    meta: { title: '个人资料', requiresAuth: true }
  },
  {
    path: '/user/password',
    name: 'password',
    component: () => import('@/views/user/Password.vue'),
    meta: { title: '修改密码', requiresAuth: true }
  },
  {
    path: '/recommend',
    name: 'recommend',
    component: () => import('@/views/recommend/Index.vue'),
    meta: { title: '个性化推荐', requiresAuth: true }
  },
  {
    path: '/admin',
    component: () => import('@/layouts/Admin.vue'),
    meta: { requiresAuth: true, role: ['admin', 'sales'] },
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: { title: '管理后台' }
      },
      {
        path: 'products',
        name: 'admin-products',
        component: () => import('@/views/admin/Product.vue'),
        meta: { title: '商品管理' }
      },
      {
        path: 'categories',
        name: 'admin-categories',
        component: () => import('@/views/admin/Category.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('@/views/admin/User.vue'),
        meta: { title: '用户管理', role: ['admin'] }
      },
      {
        path: 'orders',
        name: 'admin-orders',
        component: () => import('@/views/admin/Order.vue'),
        meta: { title: '订单管理' }
      },
      {
        path: 'order/:id',
        name: 'admin-order-detail',
        component: () => import('@/views/admin/OrderDetail.vue'),
        meta: { title: '订单详情' }
      },
      {
        path: 'stats',
        name: 'admin-stats',
        component: () => import('@/views/admin/Stats.vue'),
        meta: { title: '销售统计' }
      },
      {
        path: 'logs',
        name: 'admin-logs',
        component: () => import('@/views/admin/Logs.vue'),
        meta: { title: '操作日志', role: ['admin'] }
      },
      {
        path: 'security-threats',
        name: 'admin-security-threats',
        component: () => import('@/views/admin/SecurityThreats.vue'),
        meta: { title: '安全威胁', role: ['admin'] }
      },
      {
        path: 'analysis',
        name: 'admin-analysis',
        component: () => import('@/views/admin/Analysis.vue'),
        meta: { title: '数据分析' }
      }
    ]
  },
  {
    path: '/sales',
    component: () => import('@/layouts/Sales.vue'),
    meta: { requiresAuth: true, role: ['sales'] },
    children: [
      {
        path: '',
        name: 'sales-dashboard',
        component: () => import('@/views/sales/Dashboard.vue'),
        meta: { title: '销售后台' }
      },
      {
        path: 'products',
        name: 'sales-products',
        component: () => import('@/views/admin/Product.vue'),
        meta: { title: '商品管理' }
      },
      {
        path: 'categories',
        name: 'sales-categories',
        component: () => import('@/views/admin/Category.vue'),
        meta: { title: '分类管理' }
      },
      {
        path: 'orders',
        name: 'sales-orders',
        component: () => import('@/views/admin/Order.vue'),
        meta: { title: '订单管理' }
      },
      {
        path: 'stats',
        name: 'sales-stats',
        component: () => import('@/views/admin/Stats.vue'),
        meta: { title: '销售统计' }
      },
      {
        path: 'users',
        name: 'sales-users',
        component: () => import('@/views/sales/UserBehavior.vue'),
        meta: { title: '用户行为分析' }
      },
      {
        path: 'analysis',
        name: 'sales-analysis',
        component: () => import('@/views/admin/Analysis.vue'),
        meta: { title: '数据分析' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/error/NotFound.vue'),
    meta: { title: '404', public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  document.title = (to.meta.title as string) || '电商平台'
  
  if (to.meta.public) {
    next()
    return
  }
  
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  if (to.meta.role) {
    const roles = to.meta.role as string[]
    if (!authStore.hasRole(roles as any)) {
      next({ name: 'home' })
      return
    }
  }
  
  next()
})

export default router