<template>
  <div class="empty-container">
    <el-icon :size="60" class="empty-icon">
      <component :is="icon" />
    </el-icon>
    <p class="empty-text">{{ text }}</p>
    <slot name="action"></slot>
  </div>
</template>

<script setup lang="ts">
import { FolderOpened } from '@element-plus/icons-vue'

defineProps<{
  text?: string
  icon?: any
}>()
</script>

<style scoped lang="scss">
.empty-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
  
  .empty-icon {
    margin-bottom: 16px;
    color: #dcdfe6;
  }
  
  .empty-text {
    font-size: 14px;
    margin-bottom: 20px;
  }
}
</style>