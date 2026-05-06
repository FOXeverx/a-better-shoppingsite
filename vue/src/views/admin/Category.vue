<template>
  <div class="admin-category-page">
    <div class="page-header">
      <el-button type="primary" @click="handleAdd">新增分类</el-button>
    </div>
    
    <el-table :data="categoryTree" v-loading="loading" border row-key="id" :tree-props="{ children: 'children' }">
      <el-table-column prop="name" label="分类名称" min-width="200" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text @click="handleAddChild(row)">添加子分类</el-button>
          <el-button type="primary" text @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" text @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="400px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="上级分类">
          <el-cascader
            v-model="form.parent_id"
            :options="cascaderOptions"
            :props="{ checkStrictly: true, value: 'id', label: 'name', emitPath: false }"
            placeholder="顶级分类（无上级）"
            clearable
            @change="handleParentChange"
          />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入分类名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { getCategoryList, getCategoryFlatList, createCategory, updateCategory, deleteCategory } from '@/api/product'

interface CategoryNode {
  id: number
  name: string
  parent_id: number | null
  children?: CategoryNode[]
}

const loading = ref(false)
const categories = ref<CategoryNode[]>([])
const categoryTree = ref<CategoryNode[]>([])
const dialogVisible = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const parentIdBeforeEdit = ref<number | null>(null)

const formRef = ref<FormInstance>()
const form = reactive({
  parent_id: null as number | null,
  name: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  if (isEdit.value) return '编辑分类'
  return form.parent_id ? '添加子分类' : '新增分类'
})

const cascaderOptions = computed(() => {
  const options: CategoryNode[] = [{ id: 0, name: '顶级分类', parent_id: null, children: [] }]
  const buildOptions = (cats: CategoryNode[], parent: CategoryNode) => {
    for (const cat of cats) {
      const node = { id: cat.id, name: cat.name, parent_id: cat.parent_id, children: [] as CategoryNode[] }
      parent.children!.push(node)
      if (cat.children && cat.children.length > 0) {
        buildOptions(cat.children, node)
      }
    }
  }
  if (categories.value.length > 0) {
    buildOptions(categories.value, options[0])
  }
  return options
})

async function fetchCategories() {
  loading.value = true
  try {
    const [treeRes, flatRes] = await Promise.all([
      getCategoryList(),
      getCategoryFlatList()
    ])
    if (treeRes.success) {
      categoryTree.value = treeRes.data || []
      categories.value = treeRes.data || []
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editingId.value = null
  form.parent_id = null
  form.name = ''
  dialogVisible.value = true
}

function handleAddChild(row: CategoryNode) {
  isEdit.value = false
  editingId.value = null
  form.parent_id = row.id
  form.name = ''
  dialogVisible.value = true
}

function handleEdit(row: CategoryNode) {
  isEdit.value = true
  editingId.value = row.id
  parentIdBeforeEdit.value = row.parent_id
  form.parent_id = row.parent_id
  form.name = row.name
  dialogVisible.value = true
}

function handleParentChange(value: number | null) {
  if (value === 0) {
    form.parent_id = null
  }
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const data = {
        name: form.name,
        parent_id: form.parent_id || undefined
      }
      
      let res
      if (isEdit.value && editingId.value) {
        res = await updateCategory(editingId.value, data)
      } else {
        res = await createCategory(data)
      }
      
      if (res.success) {
        ElMessage.success(isEdit.value ? '修改成功' : '创建成功')
        dialogVisible.value = false
        fetchCategories()
      }
    } catch (error: any) {
      ElMessage.error(error?.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleDelete(row: CategoryNode) {
  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${row.name}"吗？该分类下的商品将被设为未分类。`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const res = await deleteCategory(row.id)
    if (res.success) {
      ElMessage.success('删除成功')
      fetchCategories()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style scoped lang="scss">
.admin-category-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}
</style>