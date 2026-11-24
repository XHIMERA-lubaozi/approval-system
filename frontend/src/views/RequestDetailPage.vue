<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppSidebar from '../components/AppSidebar.vue'
import AppWatermark from '../components/AppWatermark.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { ApiError } from '../api/client'
import { deleteDraft, getRequest, submitRequest, approveRequest, rejectRequest, type ApprovalRequestDetail } from '../api/requests'
import { authState } from '../auth/store'

const route = useRoute()
const router = useRouter()

const requestId = computed(() => {
  const raw = route.params.id
  const value = Array.isArray(raw) ? raw[0] : raw
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
})

const request = ref<ApprovalRequestDetail | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const showDeleteDialog = ref(false)
const deleting = ref(false)
const deleteError = ref('')
const operating = ref(false)
const feedback = ref('')
const comment = ref('')
const canApprove = computed(() => request.value?.status === 'in_review' && request.value.current_approver?.id === authState.user?.id)

async function operate(action: 'submit' | 'approve' | 'reject'): Promise<void> {
  if (!request.value || operating.value) return
  if (action === 'reject' && !comment.value.trim()) { feedback.value = '请填写驳回意见'; return }
  const id = request.value.id
  const step = request.value.current_step
  operating.value = true
  feedback.value = ''
  try {
    if (action === 'submit') await submitRequest(id)
    else if (step !== null && action === 'reject') await rejectRequest(id, step, comment.value.trim())
    else if (step !== null) await approveRequest(id, step, comment.value)
    request.value = await getRequest(id)
    comment.value = ''
    feedback.value = action === 'submit' ? '提交成功' : action === 'reject' ? '已驳回' : '审批通过'
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) request.value = await getRequest(id)
    feedback.value = error instanceof ApiError && error.status === 409
      ? '状态已变更，请刷新详情后确认并重新操作。'
      : error instanceof ApiError ? error.message : '操作失败，请稍后重试'
  } finally { operating.value = false }
}


const canManage = computed(
  () =>
    request.value !== null &&
    authState.user?.id === request.value.applicant.id &&
    request.value.status === 'draft',
)

function formatDateTime(value: string | null): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function stepLabel(item: ApprovalRequestDetail): string {
  if (item.status === 'draft') return '未提交'
  if (item.status !== 'in_review') return '已结束'
  if (item.current_step === 1) return '一级审批'
  if (item.current_step === 2) return '二级审批'
  return '—'
}

async function load(): Promise<void> {
  if (!requestId.value) {
    errorMessage.value = '申请不存在'
    loading.value = false
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    request.value = await getRequest(requestId.value)
  } catch (error) {
    errorMessage.value =
      error instanceof ApiError ? error.message : '加载申请详情失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function confirmDelete(): Promise<void> {
  if (!request.value || deleting.value) return

  deleting.value = true
  deleteError.value = ''
  try {
    await deleteDraft(request.value.id)
    await router.replace({ name: 'home' })
  } catch (error) {
    deleteError.value =
      error instanceof ApiError ? error.message : '删除草稿失败，请稍后重试'
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="app-shell">
    <AppSidebar />
    <AppWatermark />

    <main class="content-page">
      <RouterLink class="back-link" to="/">← 返回我的申请</RouterLink>

      <div v-if="loading" class="panel loading-state" role="status">
        加载中…
      </div>

      <div v-else-if="errorMessage" class="panel">
        <p class="alert alert-error" role="alert">{{ errorMessage }}</p>
        <RouterLink class="btn btn-ghost" to="/">返回列表</RouterLink>
      </div>

      <template v-else-if="request">
        <div class="detail-heading">
          <div>
            <p class="eyebrow">申请详情</p>
            <div class="detail-title-row">
              <h1 class="page-title">{{ request.title }}</h1>
              <StatusBadge :status="request.status" />
            </div>
          </div>

          <div v-if="canManage" class="detail-actions">
            <button class="btn btn-primary" :disabled="operating" @click="operate('submit')">提交</button>
            <RouterLink
              class="btn btn-ghost"
              :to="{ name: 'request-edit', params: { id: request.id } }"
            >
              编辑
            </RouterLink>
            <button
              class="btn btn-danger"
              type="button"
              @click="showDeleteDialog = true"
            >
              删除
            </button>
          </div>
        </div>

        <p v-if="feedback" role="status" class="alert">{{ feedback }}</p>
        <section v-if="canApprove" class="panel detail-panel approval-panel">
          <div class="approval-heading">
            <h2 class="section-title">审批操作</h2>
            <p class="muted">填写审批意见后选择通过或驳回；驳回时必须填写意见。</p>
          </div>
          <label for="approval-comment">审批意见</label>
          <textarea
            id="approval-comment"
            v-model="comment"
            class="control approval-comment"
            maxlength="500"
          ></textarea>
          <div class="approval-actions">
            <button
              class="btn btn-primary"
              type="button"
              :disabled="operating"
              @click="operate('approve')"
            >
              通过
            </button>
            <button
              class="btn btn-danger"
              type="button"
              :disabled="operating"
              @click="operate('reject')"
            >
              驳回
            </button>
          </div>
        </section>
        <section class="panel detail-panel">
          <dl class="detail-meta">
            <div>
              <dt>申请人</dt>
              <dd>
                {{ request.applicant.display_name }}
                <span class="meta-sub">@{{ request.applicant.username }}</span>
              </dd>
            </div>
            <div>
              <dt>一级审批人</dt>
              <dd>
                {{ request.first_approver.display_name }}
                <span class="meta-sub">@{{ request.first_approver.username }}</span>
              </dd>
            </div>
            <div>
              <dt>二级审批人</dt>
              <dd>
                {{ request.second_approver.display_name }}
                <span class="meta-sub">@{{ request.second_approver.username }}</span>
              </dd>
            </div>
            <div>
              <dt>当前步骤</dt>
              <dd>{{ stepLabel(request) }}</dd>
            </div>
            <div>
              <dt>当前审批人</dt>
              <dd>
                {{
                  request.current_approver
                    ? request.current_approver.display_name
                    : '—'
                }}
              </dd>
            </div>
            <div>
              <dt>创建时间</dt>
              <dd>{{ formatDateTime(request.created_at) }}</dd>
            </div>
            <div>
              <dt>更新时间</dt>
              <dd>{{ formatDateTime(request.updated_at) }}</dd>
            </div>
            <div>
              <dt>提交时间</dt>
              <dd>{{ formatDateTime(request.submitted_at) }}</dd>
            </div>
          </dl>
        </section>

        <section class="panel detail-panel">
          <h2 class="section-title">申请内容</h2>
          <p class="request-content">{{ request.content }}</p>
        </section>

        <section class="panel detail-panel">
          <h2 class="section-title">审批历史</h2>
          <p v-if="request.history.length === 0" class="muted">
            草稿尚未提交，暂无审批历史。
          </p>
          <ol v-else>
            <li v-for="entry in request.history" :key="entry.id">
              {{ entry.action === 'submit' ? '提交' : (entry.step === 1 ? '一级' : '二级') + (entry.action === 'reject' ? '驳回' : '通过') }} · {{ entry.operator.display_name }} · {{ formatDateTime(entry.operated_at) }}
              <p v-if="entry.comment">意见：{{ entry.comment }}</p>
            </li>
          </ol>
        </section>
      </template>
    </main>

    <div
      v-if="showDeleteDialog && request"
      class="modal-backdrop"
      @click.self="showDeleteDialog = false"
    >
      <section
        class="confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-dialog-title"
      >
        <h2 id="delete-dialog-title" class="section-title">删除草稿</h2>
        <p class="muted">
          删除后无法恢复，确认删除“{{ request.title }}”？
        </p>
        <p v-if="deleteError" class="alert alert-error" role="alert">
          {{ deleteError }}
        </p>
        <div class="confirm-actions">
          <button
            class="btn btn-ghost"
            type="button"
            :disabled="deleting"
            @click="showDeleteDialog = false"
          >
            取消
          </button>
          <button
            class="btn btn-danger"
            type="button"
            :disabled="deleting"
            @click="confirmDelete"
          >
            {{ deleting ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.content-page {
  max-width: 62rem;
  margin-inline: auto;
  padding: 28px 24px 64px;
}

.back-link {
  display: inline-block;
  margin-bottom: 18px;
  color: var(--muted);
  font-size: 0.86rem;
}

.back-link:hover {
  color: var(--brand);
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-panel {
  display: grid;
  gap: 16px;
  margin-bottom: 16px;
}

.approval-heading {
  display: grid;
  gap: 4px;
}

.approval-heading .muted {
  margin: 0;
  font-size: 0.82rem;
}

.approval-comment {
  min-height: 6.5rem;
}

.approval-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.detail-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
  gap: 18px 24px;
  margin: 0;
}

.detail-meta dt {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 600;
}

.detail-meta dd {
  margin: 5px 0 0;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.meta-sub {
  color: var(--muted);
  font-size: 0.8rem;
  font-weight: 400;
}

.section-title {
  margin: 0;
  font-size: 1.02rem;
}

.request-content {
  margin: 0;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: grid;
  padding: 20px;
  background: rgb(23 43 67 / 45%);
  place-items: center;
}

.confirm-dialog {
  width: min(100%, 26rem);
  padding: 24px;
  background: var(--surface);
  border-radius: 16px;
  box-shadow: var(--shadow);
}

.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}

@media (max-width: 640px) {
  .content-page {
    padding: 24px 16px 48px;
  }

  .detail-heading {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
