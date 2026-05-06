<template>
  <div class="security-threats-page">
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #409eff;">
          <el-icon :size="24"><Warning /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总威胁数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #f56c6c;">
          <el-icon :size="24"><WarningFilled /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.unresolved }}</div>
          <div class="stat-label">未处理</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #e6a23c;">
          <el-icon :size="24"><CircleClose /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.high_critical }}</div>
          <div class="stat-label">高危/严重</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #67c23a;">
          <el-icon :size="24"><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today }}</div>
          <div class="stat-label">今日新增</div>
        </div>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="page-tabs">
      <el-tab-pane label="威胁记录" name="threats">
        <div class="filter-section">
          <el-select v-model="filters.threat_type" placeholder="威胁类型" clearable @change="fetchThreats">
            <el-option label="触发限流" value="rate_limit" />
            <el-option label="IP被封禁" value="blocked_ip" />
            <el-option label="UA被拦截" value="blocked_ua" />
            <el-option label="暴力破解" value="brute_force" />
            <el-option label="可疑访问" value="suspicious_access" />
          </el-select>
          <el-select v-model="filters.severity" placeholder="严重程度" clearable @change="fetchThreats">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
          <el-select v-model="filters.is_resolved" placeholder="状态" clearable @change="fetchThreats">
            <el-option label="未处理" :value="false" />
            <el-option label="已处理" :value="true" />
          </el-select>
        </div>

        <el-table :data="threats" v-loading="loading" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="threat_type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getThreatTypeTag(row.threat_type)">{{ getThreatTypeText(row.threat_type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP地址" width="130" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityTag(row.severity)">{{ getSeverityText(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="user_agent" label="User-Agent" min-width="200">
            <template #default="{ row }">
              <el-text size="small" :title="row.user_agent">{{ row.user_agent?.substring(0, 50) }}...</el-text>
            </template>
          </el-table-column>
          <el-table-column prop="is_resolved" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_resolved ? 'success' : 'danger'">
                {{ row.is_resolved ? '已处理' : '未处理' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" text size="small" @click="resolveThreatHandler(row.id)" :disabled="row.is_resolved">
                标记处理
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            layout="total, prev, pager, next"
            @current-change="fetchThreats"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="IP封禁" name="blocks">
        <div class="filter-section">
          <el-button type="danger" @click="showBlockDialog = true">手动封禁IP</el-button>
        </div>

        <el-table :data="blocks" v-loading="blocksLoading" border>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="ip_address" label="IP地址" width="130" />
          <el-table-column prop="block_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.block_type === 'manual' ? 'warning' : 'info'">
                {{ row.block_type === 'manual' ? '手动' : '自动' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="原因" min-width="150" />
          <el-table-column prop="expires_at" label="过期时间" width="160">
            <template #default="{ row }">
              {{ row.expires_at ? formatDate(row.expires_at) : '永久' }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="封禁时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" text size="small" @click="unblockIPHandler(row.id)">解封</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="blocksPagination.page"
            v-model:page-size="blocksPagination.pageSize"
            :total="blocksPagination.total"
            layout="total, prev, pager, next"
            @current-change="fetchBlocks"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showBlockDialog" title="手动封禁IP" width="400px">
      <el-form :model="blockForm" label-width="80px">
        <el-form-item label="IP地址">
          <el-input v-model="blockForm.ip_address" placeholder="如: 192.168.1.100" />
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="blockForm.reason" placeholder="封禁原因" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="blockForm.expires_minutes" placeholder="选择有效期">
            <el-option label="30分钟" :value="30" />
            <el-option label="1小时" :value="60" />
            <el-option label="24小时" :value="1440" />
            <el-option label="永久" :value="null" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBlockDialog = false">取消</el-button>
        <el-button type="danger" @click="submitBlock">确认封禁</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, WarningFilled, CircleClose, Clock } from '@element-plus/icons-vue'
import {
  getSecurityThreats,
  resolveThreat,
  getThreatStats,
  getIPBlocks,
  createIPBlock,
  unblockIP as unblockAPI,
  type SecurityThreat,
  type IPBlock,
  type ThreatStats
} from '@/api/admin'

const activeTab = ref('threats')
const loading = ref(false)
const threats = ref<SecurityThreat[]>([])
const blocksLoading = ref(false)
const blocks = ref<IPBlock[]>([])
const stats = reactive<ThreatStats>({ total: 0, unresolved: 0, high_critical: 0, today: 0 })

const filters = reactive({
  threat_type: '',
  severity: '',
  is_resolved: null as boolean | null
})

const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const blocksPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const showBlockDialog = ref(false)
const blockForm = reactive({
  ip_address: '',
  reason: '',
  expires_minutes: 30
})

function formatDate(date: string) {
  return date ? new Date(date).toLocaleString('zh-CN') : '-'
}

function getThreatTypeText(type: string) {
  const map: Record<string, string> = {
    rate_limit: '触发限流',
    blocked_ip: 'IP被封禁',
    blocked_ua: 'UA被拦截',
    brute_force: '暴力破解',
    suspicious_access: '可疑访问'
  }
  return map[type] || type
}

function getThreatTypeTag(type: string) {
  const map: Record<string, string> = {
    rate_limit: 'warning',
    blocked_ip: 'danger',
    blocked_ua: 'danger',
    brute_force: 'danger',
    suspicious_access: 'warning'
  }
  return map[type] || 'info'
}

function getSeverityText(severity: string) {
  const map: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重'
  }
  return map[severity] || severity
}

function getSeverityTag(severity: string) {
  const map: Record<string, string> = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return map[severity] || 'info'
}

async function fetchStats() {
  try {
    const res = await getThreatStats()
    if (res.success && res.data) {
      Object.assign(stats, res.data)
    }
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function fetchThreats() {
  loading.value = true
  try {
    const res = await getSecurityThreats({
      threat_type: filters.threat_type || undefined,
      severity: filters.severity || undefined,
      is_resolved: filters.is_resolved === null ? undefined : filters.is_resolved,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    if (res.success) {
      threats.value = res.data || []
      pagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load threats:', error)
  } finally {
    loading.value = false
  }
}

async function resolveThreatHandler(id: number) {
  try {
    const res = await resolveThreat(id)
    if (res.success) {
      ElMessage.success('标记成功')
      fetchThreats()
      fetchStats()
    }
  } catch (error) {
    console.error('Failed to resolve threat:', error)
    ElMessage.error('操作失败')
  }
}

async function fetchBlocks() {
  blocksLoading.value = true
  try {
    const res = await getIPBlocks({
      page: blocksPagination.page,
      page_size: blocksPagination.pageSize
    })
    if (res.success) {
      blocks.value = res.data || []
      blocksPagination.total = res.pagination?.total || 0
    }
  } catch (error) {
    console.error('Failed to load blocks:', error)
  } finally {
    blocksLoading.value = false
  }
}

async function submitBlock() {
  if (!blockForm.ip_address) {
    ElMessage.warning('请输入IP地址')
    return
  }
  try {
    const res = await createIPBlock({
      ip_address: blockForm.ip_address,
      reason: blockForm.reason || undefined,
      expires_minutes: blockForm.expires_minutes
    })
    if (res.success) {
      ElMessage.success('封禁成功')
      showBlockDialog.value = false
      blockForm.ip_address = ''
      blockForm.reason = ''
      blockForm.expires_minutes = 30
      fetchBlocks()
    }
  } catch (error) {
    console.error('Failed to block IP:', error)
    ElMessage.error('操作失败')
  }
}

async function unblockIPHandler(id: number) {
  try {
    const res = await unblockAPI(id)
    if (res.success) {
      ElMessage.success('解封成功')
      fetchBlocks()
    }
  } catch (error) {
    console.error('Failed to unblock IP:', error)
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchStats()
  fetchThreats()
  fetchBlocks()
})
</script>

<style scoped lang="scss">
.security-threats-page {
  padding: 20px;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);

  .stat-icon {
    width: 50px;
    height: 50px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
  }

  .stat-info {
    .stat-value {
      font-size: 24px;
      font-weight: 600;
    }
    .stat-label {
      font-size: 12px;
      color: #909399;
    }
  }
}

.page-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}

.filter-section {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>