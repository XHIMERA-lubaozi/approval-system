<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import { registerUser } from '../api/auth'
import BrandLogo from '../components/BrandLogo.vue'
import AuthWatermark from '../components/AuthWatermark.vue'
import PasswordInput from '../components/PasswordInput.vue'
import { ApiError, fieldMessages } from '../api/client'

const router = useRouter()

const PASSWORD_HINT =
  '至少 8 位，需包含大写字母、小写字母、数字、符号中的至少两类；不能是常见密码或与账号过于相似。'
const PASSWORD_RULE_MESSAGE =
  '密码至少 8 位，且包含大写字母、小写字母、数字、符号中的至少两类'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  displayName: '',
})

const fieldErrors = reactive({
  username: [] as string[],
  password: [] as string[],
  displayName: [] as string[],
})
const formError = ref('')
const submitting = ref(false)
const confirmTouched = ref(false)
const passwordServerInvalid = ref(false)

const passwordTypeCount = computed(() => {
  const password = form.password
  return [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((pattern) =>
    pattern.test(password),
  ).length
})

const passwordFormatValid = computed(
  () => form.password.length >= 8 && passwordTypeCount.value >= 2,
)

const passwordStatus = computed<'idle' | 'valid' | 'invalid'>(() => {
  if (!form.password) return 'idle'
  if (passwordServerInvalid.value || !passwordFormatValid.value) {
    return 'invalid'
  }
  return 'valid'
})

const confirmError = computed(() => {
  if (!confirmTouched.value) return ''
  if (!form.confirmPassword) return '请再次输入密码'
  if (form.confirmPassword !== form.password) return '两次输入的密码不一致'
  return ''
})

watch(
  () => form.password,
  () => {
    fieldErrors.password = []
    passwordServerInvalid.value = false
  },
)

watch(
  () => form.confirmPassword,
  () => {
    confirmTouched.value = true
  },
)

function validate(): boolean {
  fieldErrors.username = form.username.trim() ? [] : ['请输入账号']
  fieldErrors.password = !form.password
    ? ['请输入密码']
    : passwordFormatValid.value
      ? []
      : [PASSWORD_RULE_MESSAGE]
  fieldErrors.displayName = form.displayName.trim() ? [] : ['请输入昵称']
  confirmTouched.value = true

  return (
    fieldErrors.username.length === 0 &&
    fieldErrors.password.length === 0 &&
    fieldErrors.displayName.length === 0 &&
    !confirmError.value
  )
}

function clearFieldError(field: 'username' | 'displayName'): void {
  fieldErrors[field] = []
}

async function onSubmit(): Promise<void> {
  if (submitting.value) return

  formError.value = ''
  if (!validate()) return

  submitting.value = true
  try {
    await registerUser({
      username: form.username,
      password: form.password,
      display_name: form.displayName,
    })
    await router.replace({
      name: 'login',
      query: { registered: '1', username: form.username },
    })
  } catch (error) {
    if (error instanceof ApiError) {
      fieldErrors.username = fieldMessages(error.details, 'username')
      fieldErrors.password = fieldMessages(error.details, 'password')
      fieldErrors.displayName = fieldMessages(error.details, 'display_name')
      passwordServerInvalid.value = fieldErrors.password.length > 0
      const hasFieldError =
        fieldErrors.username.length > 0 ||
        fieldErrors.password.length > 0 ||
        fieldErrors.displayName.length > 0
      formError.value = hasFieldError ? '' : error.message
    } else {
      formError.value = '注册失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth-shell">
    <AuthWatermark />
    <section class="auth-card" aria-label="注册">
      <header class="auth-header">
        <BrandLogo />
      </header>

      <form class="form" novalidate @submit.prevent="onSubmit">
        <div class="field">
          <label for="register-username">账号</label>
          <input
            id="register-username"
            v-model="form.username"
            maxlength="150"
            name="username"
            type="text"
            autocomplete="username"
            :aria-invalid="fieldErrors.username.length > 0"
            :aria-describedby="
              fieldErrors.username.length > 0
                ? 'register-username-error'
                : 'register-username-hint'
            "
            @input="clearFieldError('username')"
          />
          <p
            v-if="fieldErrors.username.length > 0"
            id="register-username-error"
            class="field-error"
          >
            {{ fieldErrors.username[0] }}
          </p>
          <p v-else id="register-username-hint" class="field-hint">
            可使用字母、数字及 @ . + - _。
          </p>
        </div>

        <div class="field">
          <div class="field-label-row">
            <label for="register-password">密码</label>
            <span
              v-if="passwordStatus !== 'idle'"
              class="password-status"
              :class="
                passwordStatus === 'valid' ? 'is-valid' : 'is-invalid'
              "
              role="status"
              :aria-label="
                passwordStatus === 'valid' ? '密码符合要求' : '密码不符合要求'
              "
            >
              <svg
                v-if="passwordStatus === 'valid'"
                viewBox="0 0 20 20"
                fill="none"
                aria-hidden="true"
              >
                <circle
                  cx="10"
                  cy="10"
                  r="9"
                  fill="currentColor"
                  opacity="0.14"
                />
                <path
                  d="M5.8 10.2l2.7 2.7 5.7-5.8"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              <svg v-else viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <circle
                  cx="10"
                  cy="10"
                  r="9"
                  fill="currentColor"
                  opacity="0.14"
                />
                <path
                  d="M7 7l6 6M13 7l-6 6"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
              </svg>
              {{ passwordStatus === 'valid' ? '符合' : '不符合' }}
            </span>
          </div>
          <PasswordInput
            id="register-password"
            v-model="form.password"
            name="password"
            autocomplete="new-password"
            :invalid="fieldErrors.password.length > 0"
            :describedby="
              fieldErrors.password.length > 0
                ? 'register-password-error'
                : 'register-password-hint'
            "
          />
          <p
            v-if="fieldErrors.password.length > 0"
            id="register-password-error"
            class="field-error"
          >
            {{ fieldErrors.password[0] }}
          </p>
          <p v-else id="register-password-hint" class="field-hint">
            {{ PASSWORD_HINT }}
          </p>
        </div>

        <div class="field">
          <label for="register-confirm-password">确认密码</label>
          <PasswordInput
            id="register-confirm-password"
            v-model="form.confirmPassword"
            name="confirm_password"
            autocomplete="new-password"
            :invalid="confirmError !== ''"
            :describedby="
              confirmError !== ''
                ? 'register-confirm-password-error'
                : undefined
            "
          />
          <p
            v-if="confirmError"
            id="register-confirm-password-error"
            class="field-error"
          >
            {{ confirmError }}
          </p>
        </div>

        <div class="field">
          <label for="register-display-name">昵称</label>
          <input
            id="register-display-name"
            v-model="form.displayName"
            maxlength="150"
            name="display_name"
            type="text"
            autocomplete="nickname"
            :aria-invalid="fieldErrors.displayName.length > 0"
            :aria-describedby="
              fieldErrors.displayName.length > 0
                ? 'register-display-name-error'
                : undefined
            "
            @input="clearFieldError('displayName')"
          />
          <p
            v-if="fieldErrors.displayName.length > 0"
            id="register-display-name-error"
            class="field-error"
          >
            {{ fieldErrors.displayName[0] }}
          </p>
        </div>

        <p v-if="formError" class="alert alert-error" role="alert">
          {{ formError }}
        </p>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? '注册中…' : '注册' }}
        </button>
      </form>

      <p class="auth-switch">
        已有账号？
        <RouterLink to="/login">返回登录</RouterLink>
      </p>
    </section>
  </main>
</template>
