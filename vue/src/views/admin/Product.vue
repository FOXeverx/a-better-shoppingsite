<template>
  <div class="admin-product-page">
    <div class="page-header">
      <el-button type="primary" @click="handleAdd">新增商品</el-button>
      <el-input
        v-model="searchKeyword"
        placeholder="搜索商品..."
        style="width: 200px"
        @keyup.enter="fetchProducts"
      />
    </div>
    
    <el-table :data="products" v-loading="loading" border>
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="商品名称" min-width="150" />
      <el-table-column prop="price" label="价格" width="100">
        <template #default="{ row }">
          ¥{{ row.price.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="80" />
      <el-table-column prop="category_id" label="分类" width="80" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '上架' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" text @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" text @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="fetchProducts"
      />
    </div>
    
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑商品' : '新增商品'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" />
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="form.stock" :min="0" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <el-cascader
            v-model="form.category_id"
            :options="categoryOptions"
            :props="{ value: 'id', label: 'name', children: 'children', checkStrictly: true }"
            placeholder="选择分类（可选）"
            clearable
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="图片" prop="image_url">
          <div class="image-upload">
            <el-upload
              class="image-uploader"
              :show-file-list="false"
              :auto-upload="false"
              :on-change="handleImageChange"
              accept="image/*"
            >
              <img v-if="form.image_url" :src="form.image_url" class="preview-image" />
              <el-icon v-else class="upload-icon"><Plus /></el-icon>
            </el-upload>
            <el-input v-model="form.image_url" placeholder="或输入图片URL" style="margin-top: 8px" />
          </div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getProductList, getCategoryList, createProduct, updateProduct, deleteProduct, uploadImage } from '@/api/product'
import type { ProductListItem, Product } from '@/types/product'

const products = ref<ProductListItem[]>([])
const loading = ref(false)
const searchKeyword = ref('')

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)

const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  description: '',
  price: 0,
  stock: 0,
  category_id: 1,
  image_url: '',
  is_active: true
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }]
}

const categoryOptions = ref<any[]>([])

async function fetchCategoryOptions() {
  try {
    const res = await getCategoryList()
    if (res.success && res.data) {
      categoryOptions.value = res.data
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

async function fetchProducts() {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      page_size: pagination.pageSize,
      search: searchKeyword.value || undefined
    })
    if (res.success && res.data) {
      products.value = res.data
      if (res.pagination) {
        pagination.total = res.pagination.total
      }
    }
  } catch (error) {
    console.error('Failed to load products:', error)
  } finally {
    loading.value = false
  }
}

function handleAdd() {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    name: '',
    description: '',
    price: 0,
    stock: 0,
    category_id: null,
    image_url: '',
    is_active: true
  })
  dialogVisible.value = true
}

function handleEdit(row: ProductListItem) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    description: row.description || '',
    price: row.price,
    stock: row.stock,
    category_id: row.category_id || null,
    image_url: row.image_url || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

async function handleDelete(row: ProductListItem) {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await deleteProduct(row.id)
    if (res.success) {
      ElMessage.success('删除成功')
      fetchProducts()
    }
  } catch {
    // User cancelled
  }
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const submitData = {
        ...form,
        category_id: form.category_id ? (Array.isArray(form.category_id) ? form.category_id[form.category_id.length - 1] : form.category_id) : undefined
      }
      
      if (isEdit.value && editingId.value) {
        const res = await updateProduct(editingId.value, submitData)
        if (res.success) {
          ElMessage.success('更新成功')
        }
      } else {
        const res = await createProduct(submitData)
        if (res.success) {
          ElMessage.success('创建成功')
        }
      }
      dialogVisible.value = false
      fetchProducts()
    } catch (error) {
      console.error('Failed to save product:', error)
    } finally {
      submitting.value = false
    }
  })
}

async function handleImageChange(file: any) {
  const fileData = file.raw
  if (!fileData) return
  
  console.log('Uploading file:', fileData.name, 'size:', fileData.size)
  try {
    const res = await uploadImage(fileData)
    console.log('Upload response full:', JSON.stringify(res))
    if (res.success && res.data && res.data.url) {
      form.image_url = res.data.url
      console.log('After set - form.image_url:', form.image_url)
      ElMessage.success('图片上传成功')
    } else {
      console.log('Upload failed - no data or no url:', res)
      ElMessage.error('上传失败')
    }
  } catch (error) {
    console.error('Failed to upload image:', error)
    ElMessage.error('上传失败')
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchProducts()
  fetchCategoryOptions()
})
</script>

<style scoped lang="scss">
.admin-product-page {
  .page-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 20px;
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
}

.image-upload {
  .image-uploader {
    :deep(.el-upload) {
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      width: 120px;
      height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &:hover {
        border-color: #409eff;
      }
    }
    
    .upload-icon {
      font-size: 28px;
      color: #8c939d;
    }
    
    .preview-image {
      width: 100%;
      height: 100%;
      object-fit: cover;
      border-radius: 6px;
    }
  }
}
</style>