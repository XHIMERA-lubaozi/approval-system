<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppSidebar from '../components/AppSidebar.vue'
import { ApiError, fieldMessages } from '../api/client'
import {
  createDraft,
  getRequest,
  listUsers,
  updateDraft,
  type UserSummary,
} from '../api/requests'
import { authState } from '../auth/store'

const route = useRoute()
const router = useRouter()

const requestId = computed(() => {
  const raw = route.params.id
  const value = Array.isArray(raw) ? raw[0] : raw
  const parsed = Number(value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
})
const isEdit = computed(() => route.name === 'request-edit')

const loading = ref(true)
const submitting = ref(false)
const pageError = ref('')
const formError = ref('')
const notEditable = ref(false)
const users = ref<UserSummary[]>([])

const form = reactive({
  title: '',
  content: '',
  firstApproverId: '',
  secondApproverId: '',
})

const fieldErrors = reactive({
  title: [] as string[],
  content: [] as string[],
  firstApproverId: [] as string[],
  secondApproverId: [] as string[],
})

const approverOptions = computed(() =>
  users.value.filter((user) => user.id !== authState.user?.id),
)

async function load(): Promise<void> {
  loading.value = true
  pageError.value = ''

  if (isEdit.value && !requestId.value) {
    pageError.value = '申请不存在'
    loading.value = false
    return
  }

  try {
    const [userList, detail] = await Promise.all([
      listUsers(),
      isEdit.value && requestId.value
        ? getRequest(requestId.value)
        : Promise.resolve(null),
    ])
    users.value = userList

    if (!detail) return

    if (
      detail.applicant.id !== authState.user?.id ||
      detail.status !== 'draft'
    ) {
      notEditable.value = true
      pageError.value = '只有申请人可以编辑自己的草稿。'
      return
    }

    form.title = detail.title
    form.content = detail.content
    form.firstApproverId = String(detail.first_approver.id)
    form.secondApproverId = String(detail.second_approver.id)
  } catch (error) {
    pageError.value =
      error instanceof ApiError ? error.message : '加载草稿失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function validate(): boolean {
  fieldErrors.title = !form.title.trim()
    ? ['请输入标题']
    : form.title.length > 100
      ? ['标题不能超过 100 个字符']
      : []
  fieldErrors.content = !form.content.trim()
    ? ['请输入内容']
    : form.content.length > 2000
      ? ['内容不能超过 2000 个字符']
      : []
  fieldErrors.firstApproverId = !form.firstApproverId
    ? ['请选择一级审批人']
    : Number(form.firstApproverId) === authState.user?.id
      ? ['不能选择自己作为审批人']
      : []
  fieldErrors.secondApproverId = !form.secondApproverId
    ? ['请选择二级审批人']
    : Number(form.secondApproverId) === authState.user?.id
      ? ['不能选择自己作为审批人']
      : []

  return (
    fieldErrors.title.length === 0 &&
    fieldErrors.content.length === 0 &&
    fieldErrors.firstApproverId.length === 0 &&
    fieldErrors.secondApproverId.length === 0
  )
}

function clearFieldError(field: keyof typeof fieldErrors): void {
  fieldErrors[field] = []
}

async function onSubmit(): Promise<void> {
  if (submitting.value) return

  formError.value = ''
  if (!validate()) return

  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      content: form.content,
      first_approver_id: Number(form.firstApproverId),
      second_approver_id: Number(form.secondApproverId),
    }
    const saved =
      isEdit.value && requestId.value
        ? await updateDraft(requestId.value, payload)
        : await createDraft(payload)
    await router.replace({
      name: 'request-detail',
      params: { id: saved.id },
    })
  } catch (error) {
    if (error instanceof ApiError) {
      fieldErrors.title = fieldMessages(error.details, 'title')
      fieldErrors.content = fieldMessages(error.details, 'content')
      fieldErrors.firstApproverId = fieldMessages(
        error.details,
        'first_approver_id',
      )
      fieldErrors.secondApproverId = fieldMessages(
        error.details,
        'second_approver_id',
      )
      const hasFieldError =
        fieldErrors.title.length > 0 ||
        fieldErrors.content.length > 0 ||
        fieldErrors.firstApproverId.length > 0 ||
        fieldErrors.secondApproverId.length > 0
      formError.value = hasFieldError ? '' : error.message
    } else {
      formError.value = '保存草稿失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <div class="app-shell">
    <AppSidebar />

    <main class="content-page">
      <div class="page-heading">
        <div>
          <p class="eyebrow">申请管理</p>
          <h1 class="page-title">
            {{ isEdit ? '编辑草稿' : '新建草稿' }}
          </h1>
        </div>
        <RouterLink
          class="btn btn-ghost"
          :to="
            isEdit && requestId
              ? { name: 'request-detail', params: { id: requestId } }
              : { name: 'home' }
          "
        >
          返回
        </RouterLink>
      </div>

      <div v-if="loading" class="panel loading-state" role="status">
        加载中…
      </div>

      <div v-else-if="pageError" class="panel">
        <p class="alert alert-error" role="alert">{{ pageError }}</p>
        <RouterLink class="btn btn-ghost" :to="{ name: 'home' }">
          返回我发起的
        </RouterLink>
      </div>

      <form v-else-if="!notEditable" class="panel form-panel" novalidate @submit.prevent="onSubmit">
        <div class="form-field">
          <label for="request-title">标题</label>
          <input
            id="request-title"
            v-model="form.title"
            class="control"
            maxlength="100"
            name="title"
            placeholder="例如：采购两台显示器"
            :aria-invalid="fieldErrors.title.length > 0"
            :aria-describedby="
              fieldErrors.title.length > 0 ? 'request-title-error' : undefined
            "
            @input="clearFieldError('title')"
          />
          <p
            v-if="fieldErrors.title.length > 0"
            id="request-title-error"
            class="field-error"
          >
            {{ fieldErrors.title[0] }}
          </p>
        </div>

        <div class="form-field">
          <label for="request-content">内容</label>
          <textarea
            id="request-content"
            v-model="form.content"
            class="control content-control"
            maxlength="2000"
            name="content"
            placeholder="补充申请背景、用途和期望完成时间。"
            :aria-invalid="fieldErrors.content.length > 0"
            :aria-describedby="
              fieldErrors.content.length > 0 ? 'request-content-error' : undefined
            "
            @input="clearFieldError('content')"
          ></textarea>
          <p
            v-if="fieldErrors.content.length > 0"
            id="request-content-error"
            class="field-error"
          >
            {{ fieldErrors.content[0] }}
          </p>
        </div>

        <div class="approver-grid">
          <div class="form-field">
            <label for="first-approver">一级审批人</label>
            <select
              id="first-approver"
              v-model="form.firstApproverId"
              class="control"
              name="first_approver_id"
              :aria-invalid="fieldErrors.firstApproverId.length > 0"
              :aria-describedby="
                fieldErrors.firstApproverId.length > 0
                  ? 'first-approver-error'
                  : undefined
              "
              @change="clearFieldError('firstApproverId')"
            >
              <option value="">请选择一级审批人</option>
              <option
                v-for="user in approverOptions"
                :key="user.id"
                :value="String(user.id)"
              >
                {{ user.display_name }}（{{ user.username }}）
              </option>
            </select>
            <p
              v-if="fieldErrors.firstApproverId.length > 0"
              id="first-approver-error"
              class="field-error"
            >
              {{ fieldErrors.firstApproverId[0] }}
            </p>
          </div>

          <div class="form-field">
            <label for="second-approver">二级审批人</label>
            <select
              id="second-approver"
              v-model="form.secondApproverId"
              class="control"
              name="second_approver_id"
              :aria-invalid="fieldErrors.secondApproverId.length > 0"
              :aria-describedby="
                fieldErrors.secondApproverId.length > 0
                  ? 'second-approver-error'
                  : undefined
              "
              @change="clearFieldError('secondApproverId')"
            >
              <option value="">请选择二级审批人</option>
              <option
                v-for="user in approverOptions"
                :key="user.id"
                :value="String(user.id)"
              >
                {{ user.display_name }}（{{ user.username }}）
              </option>
            </select>
            <p
              v-if="fieldErrors.secondApproverId.length > 0"
              id="second-approver-error"
              class="field-error"
            >
              {{ fieldErrors.secondApproverId[0] }}
            </p>
          </div>
        </div>

        <p class="field-hint approver-hint">
          两级审批人可以相同，但不能选择自己。审批人候选列表不包含当前账号。
        </p>

        <p v-if="formError" class="alert alert-error" role="alert">
          {{ formError }}
        </p>

        <div class="form-actions">
          <button class="btn btn-primary" type="submit" :disabled="submitting">
            {{ submitting ? '保存中…' : '保存草稿' }}
          </button>
          <RouterLink
            class="btn btn-ghost"
            :to="
              isEdit && requestId
                ? { name: 'request-detail', params: { id: requestId } }
                : { name: 'home' }
            "
          >
            取消
          </RouterLink>
        </div>
      </form>
    </main>
  </div>
</template>

<style scoped>
.content-page {
  max-width: 54rem;
  margin-inline: auto;
  padding: 32px 24px 64px;
}

.page-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 18px;
}

.page-title {
  margin: 0;
  font-size: clamp(1.6rem, 3vw, 2.1rem);
  line-height: 1.15;
}

.form-panel {
  display: grid;
  gap: 22px;
}

.form-field {
  display: grid;
  gap: 7px;
}

.form-field label {
  font-size: 0.88rem;
  font-weight: 600;
}

.content-control {
  min-height: 11rem;
  line-height: 1.6;
  resize: vertical;
}

.approver-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.approver-hint {
  margin-top: -8px;
}

.form-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding-top: 4px;
}

@media (max-width: 640px) {
  .content-page {
    padding: 24px 16px 48px;
  }

  .page-heading {
    align-items: stretch;
    flex-direction: column;
  }

  .approver-grid {
    grid-template-columns: 1fr;
  }
}
</style>
