<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import AppSidebar from '../components/AppSidebar.vue'
import AppWatermark from '../components/AppWatermark.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { ApiError } from '../api/client'
import {
  listRequests,
  type ApprovalRequest,
  type RequestStatus,
} from '../api/requests'

const route = useRoute()
const pending = computed(() => route.name === 'pending')
const requests = ref<ApprovalRequest[]>([])
const count = ref(0)
const page = ref(1)
const pageSize = ref(10)
const status = ref<'' | RequestStatus>('')
const keyword = ref('')
const appliedKeyword = ref('')
const loading = ref(true)
const errorMessage = ref('')

const totalPages = computed(() =>
  Math.max(1, Math.ceil(count.value / pageSize.value)),
)

const statusOptions: { value: RequestStatus; label: string }[] = [
  { value: 'draft', label: '草稿' },
  { value: 'in_review', label: '审批中' },
  { value: 'approved', label: '已通过' },
  { value: 'rejected', label: '已驳回' },
]

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function stepLabel(item: ApprovalRequest): string {
  if (item.status === 'draft') return '未提交'
  if (item.status !== 'in_review') return '已结束'
  if (item.current_step === 1) return '一级审批'
  if (item.current_step === 2) return '二级审批'
  return '—'
}

async function loadRequests(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await listRequests({
      scope: pending.value ? 'pending' : 'mine',
      page: page.value,
      pageSize: pageSize.value,
      status: status.value || undefined,
      keyword: appliedKeyword.value || undefined,
    })
    requests.value = data.results
    count.value = data.count
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.message : '加载申请列表失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function applyFilters(): void {
  page.value = 1
  appliedKeyword.value = keyword.value.trim()
  void loadRequests()
}

function resetFilters(): void {
  status.value = ''
  keyword.value = ''
  appliedKeyword.value = ''
  page.value = 1
  void loadRequests()
}

function changePage(next: number): void {
  if (next < 1 || next > totalPages.value || next === page.value) return
  page.value = next
  void loadRequests()
}

watch(
  () => route.name,
  (name) => {
    if (name !== 'home' && name !== 'pending') return
    status.value = ''
    keyword.value = ''
    appliedKeyword.value = ''
    page.value = 1
    void loadRequests()
  },
)

onMounted(() => {
  void loadRequests()
})
</script>

<template>
  <div class="app-shell">
    <AppSidebar />
    <AppWatermark />

    <main class="content-page">
      <div class="page-heading">
        <div>
          <h1 class="page-title">{{ pending ? '待我审批' : '我的申请' }}</h1>
        </div>
        <RouterLink v-if="!pending" class="btn btn-primary" to="/requests/new">
          新建草稿
        </RouterLink>
      </div>

      <section class="panel list-panel">
        <form class="filter-bar" @submit.prevent="applyFilters">
          <label v-if="!pending" class="filter-field">
            <span>状态</span>
            <select v-model="status" @change="applyFilters">
              <option value="">全部状态</option>
              <option
                v-for="option in statusOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>

          <label class="filter-field filter-keyword">
            <span>标题关键词</span>
            <input
              v-model="keyword"
              maxlength="100"
              placeholder="搜索申请标题"
              type="search"
            />
          </label>

          <label class="filter-field filter-size">
            <span>每页</span>
            <select v-model.number="pageSize" @change="applyFilters">
              <option :value="10">10 条</option>
              <option :value="20">20 条</option>
              <option :value="50">50 条</option>
            </select>
          </label>

          <div class="filter-actions">
            <button class="btn btn-primary" type="submit" :disabled="loading">
              筛选
            </button>
            <button
              class="btn btn-ghost"
              type="button"
              :disabled="loading"
              @click="resetFilters"
            >
              重置
            </button>
          </div>
        </form>

        <p v-if="errorMessage" class="alert alert-error" role="alert">
          {{ errorMessage }}
        </p>

        <div v-if="loading" class="loading-state" role="status">加载中…</div>

        <div
          v-else-if="requests.length === 0 && !errorMessage"
          class="empty-state"
        >
          <p class="empty-title">{{ pending ? '暂无待审批申请' : '还没有申请' }}</p>
          <p v-if="!pending" class="muted">新建一份草稿，开始你的第一条申请。</p>
          <RouterLink v-if="!pending" class="btn btn-primary" to="/requests/new">
            新建草稿
          </RouterLink>
        </div>

        <div v-else class="table-wrap">
          <table class="request-table">
            <thead>
              <tr>
                <th scope="col">标题</th>
                <th scope="col">状态</th>
                <th scope="col">当前步骤</th>
                <th scope="col">创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in requests" :key="item.id">
                <td>
                  <RouterLink
                    class="request-link"
                    :to="{ name: 'request-detail', params: { id: item.id } }"
                  >
                    {{ item.title }}
                  </RouterLink>
                </td>
                <td><StatusBadge :status="item.status" /></td>
                <td class="muted">{{ stepLabel(item) }}</td>
                <td class="muted">{{ formatDateTime(item.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <footer v-if="!loading && count > 0" class="pagination">
          <span class="muted">共 {{ count }} 条</span>
          <div class="pagination-controls">
            <button
              class="btn btn-ghost"
              type="button"
              :disabled="page <= 1"
              @click="changePage(page - 1)"
            >
              上一页
            </button>
            <span class="pagination-status">{{ page }} / {{ totalPages }}</span>
            <button
              class="btn btn-ghost"
              type="button"
              :disabled="page >= totalPages"
              @click="changePage(page + 1)"
            >
              下一页
            </button>
          </div>
        </footer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.content-page {
  max-width: 68rem;
  margin-inline: auto;
  padding: 32px 24px 64px;
}

.list-panel {
  display: grid;
  gap: 20px;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}

.filter-field {
  display: grid;
  min-width: 10rem;
  gap: 6px;
}

.filter-field > span {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 600;
}

.filter-field input,
.filter-field select {
  min-height: 40px;
  padding: 8px 10px;
  color: var(--ink);
  background: #fbfdff;
  border: 1px solid var(--line);
  border-radius: 9px;
  outline: none;
}

.filter-field input:focus,
.filter-field select:focus {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgb(37 99 235 / 12%);
}

.filter-keyword {
  flex: 1;
  min-width: 15rem;
}

.filter-size {
  min-width: 7rem;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.table-wrap {
  overflow-x: auto;
}

.request-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.92rem;
}

.request-table th,
.request-table td {
  padding: 13px 10px;
  text-align: left;
  border-bottom: 1px solid rgb(23 43 67 / 8%);
}

.request-table th {
  color: var(--muted);
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
}

.request-table tbody tr:hover {
  background: #f7faff;
}

.request-link {
  color: var(--ink);
  font-weight: 600;
}

.request-link:hover {
  color: var(--brand);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 4px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-status {
  min-width: 4rem;
  color: var(--muted);
  font-size: 0.84rem;
  text-align: center;
}

@media (max-width: 640px) {
  .content-page {
    padding: 24px 16px 48px;
  }

  .page-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-field {
    width: 100%;
  }

  .pagination {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
