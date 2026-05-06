import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CartItem, CartSummary } from '@/types/order'
import * as cartApi from '@/api/cart'

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const summary = ref<CartSummary | null>(null)
  const loading = ref(false)

  const totalItems = computed(() => summary.value?.total_items || 0)
  const totalAmount = computed(() => summary.value?.total_amount || 0)
  const isEmpty = computed(() => items.value.length === 0)

  async function fetchCart() {
    loading.value = true
    try {
      const res = await cartApi.getCart()
      console.log('Cart API response:', res)
      if (res.success && res.data) {
        items.value = res.data || []
        summary.value = res.summary || null
        console.log('Cart items:', items.value)
      }
    } catch (error) {
      console.error('Fetch cart failed:', error)
    } finally {
      loading.value = false
    }
  }

  async function addItem(productId: number, quantity: number = 1) {
    loading.value = true
    try {
      const res = await cartApi.addToCart({ product_id: productId, quantity })
      if (res.success) {
        await fetchCart()
        return true
      }
      return false
    } catch (error) {
      console.error('Add to cart failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  async function updateQuantity(itemId: number, quantity: number) {
    if (quantity < 1) return false
    try {
      const res = await cartApi.updateCartItem(itemId, { quantity })
      if (res.success) {
        const item = items.value.find(i => i.id === itemId)
        if (item) {
          item.quantity = quantity
          item.subtotal = item.product.price * quantity
        }
        updateLocalSummary()
        return true
      }
      return false
    } catch (error) {
      console.error('Update cart failed:', error)
      return false
    }
  }

  async function removeItem(itemId: number) {
    try {
      const res = await cartApi.removeCartItem(itemId)
      if (res.success) {
        items.value = items.value.filter(i => i.id !== itemId)
        updateLocalSummary()
        return true
      }
      return false
    } catch (error) {
      console.error('Remove from cart failed:', error)
      return false
    }
  }

  function updateLocalSummary() {
    if (summary.value) {
      summary.value.total_items = items.value.reduce((sum, i) => sum + i.quantity, 0)
      summary.value.total_amount = items.value.reduce((sum, i) => sum + i.subtotal, 0)
    }
  }

  async function clearCart() {
    try {
      const res = await cartApi.clearCart()
      if (res.success) {
        items.value = []
        summary.value = null
        return true
      }
      return false
    } catch (error) {
      console.error('Clear cart failed:', error)
      return false
    }
  }

  return {
    items,
    summary,
    loading,
    totalItems,
    totalAmount,
    isEmpty,
    fetchCart,
    addItem,
    updateQuantity,
    removeItem,
    clearCart
  }
})