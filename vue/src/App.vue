<template>
  <component :is="layoutComponent">
    <router-view />
  </component>
</template>

<script setup lang="ts">
import { computed, onMounted, defineComponent } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Default from '@/layouts/Default.vue'
import Auth from '@/layouts/Auth.vue'

const Passthrough = defineComponent({
  setup(_, { slots }) {
    return () => slots.default?.()
  }
})

const route = useRoute()
const authStore = useAuthStore()

const layoutComponent = computed(() => {
  const layout = route.meta.layout as string
  
  if (route.path.startsWith('/admin') || route.path.startsWith('/sales')) {
    return Passthrough
  }
  
  if (layout === 'auth') {
    return Auth
  }
  
  return Default
})

onMounted(() => {
  authStore.init()
  if (authStore.isLoggedIn) {
    authStore.fetchCurrentUser()
  }
})
</script>

<style>
#app {
  min-height: 100vh;
}
</style>