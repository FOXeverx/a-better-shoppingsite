import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Notification {
  id: number
  type: 'success' | 'warning' | 'error' | 'info'
  message: string
}

export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const breadcrumbs = ref<{ title: string; path?: string }[]>([])
  const notifications = ref<Notification[]>([])
  let notificationId = 0

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setBreadcrumbs(bread: { title: string; path?: string }[]) {
    breadcrumbs.value = bread
  }

  function addNotification(type: Notification['type'], message: string) {
    const id = ++notificationId
    notifications.value.push({ id, type, message })
    setTimeout(() => {
      notifications.value = notifications.value.filter(n => n.id !== id)
    }, 5000)
  }

  function clearNotification(id: number) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return {
    loading,
    breadcrumbs,
    notifications,
    setLoading,
    setBreadcrumbs,
    addNotification,
    clearNotification
  }
})