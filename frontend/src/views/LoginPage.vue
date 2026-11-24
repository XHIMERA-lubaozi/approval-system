<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import BrandLogo from '../components/BrandLogo.vue'
import AuthWatermark from '../components/AuthWatermark.vue'
import PasswordInput from '../components/PasswordInput.vue'
import { ApiError, fieldMessages } from '../api/client'
import { signIn } from '../auth/store'

const route = useRoute()
const router = useRouter()

const form = reactive({
  username:
    typeof route.query.username === 'string' ? route.query.username : '',
  password: '',
})

const fieldErrors = reactive({
  username: [] as string[],
  password: [] as string[],
})
const formError = ref('')
const submitting = ref(false)
const justRegistered = computed(() => route.query.registered === '1')

function validate(): boolean {
  fieldErrors.username = form.username.trim() ? [] : ['请输入账号']
  fieldErrors.password = form.password ? [] : ['请输入密码']
  return fieldErrors.username.length === 0 && fieldErrors.password.length === 0
}

function clearFieldError(field: 'username' | 'password'): void {
  fieldErrors[field] = []
}

async function onSubmit(): Promise<void> {
  if (submitting.value) return

  formError.value = ''
  if (!validate()) return

  submitting.value = true
  try {
    await signIn(form.username, form.password)
    const requestedRedirect = route.query.redirect
    const redirect =
      typeof requestedRedirect === 'string' &&
      requestedRedirect.startsWith('/') &&
      !requestedRedirect.startsWith('//')
        ? requestedRedirect
        : '/'
    await router.replace(redirect)
  } catch (error) {
    if (error instanceof ApiError) {
      fieldErrors.username = fieldMessages(error.details, 'username')
      fieldErrors.password = fieldMessages(error.details, 'password')
      const hasFieldError =
        fieldErrors.username.length > 0 || fieldErrors.password.length > 0
      formError.value = hasFieldError ? '' : error.message
    } else {
      formError.value = '登录失败，请稍后重试'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="auth-shell">
    <AuthWatermark />
    <section class="auth-card" aria-label="登录">
      <header class="auth-header">
        <BrandLogo />
      </header>

      <p v-if="justRegistered" class="alert alert-success" role="status">
        注册成功，请使用新账号登录。
      </p>

      <form class="form" novalidate @submit.prevent="onSubmit">
        <div class="field">
          <label for="login-username">账号</label>
          <input
            id="login-username"
            v-model="form.username"
            maxlength="150"
            name="username"
            type="text"
            autocomplete="username"
            :aria-invalid="fieldErrors.username.length > 0"
            :aria-describedby="
              fieldErrors.username.length > 0 ? 'login-username-error' : undefined
            "
            @input="clearFieldError('username')"
          />
          <p
            v-if="fieldErrors.username.length > 0"
            id="login-username-error"
            class="field-error"
          >
            {{ fieldErrors.username[0] }}
          </p>
        </div>

        <div class="field">
          <label for="login-password">密码</label>
          <PasswordInput
            id="login-password"
            v-model="form.password"
            name="password"
            autocomplete="current-password"
            :invalid="fieldErrors.password.length > 0"
            :describedby="
              fieldErrors.password.length > 0 ? 'login-password-error' : undefined
            "
            @update:model-value="clearFieldError('password')"
          />
          <p
            v-if="fieldErrors.password.length > 0"
            id="login-password-error"
            class="field-error"
          >
            {{ fieldErrors.password[0] }}
          </p>
        </div>

        <p v-if="formError" class="alert alert-error" role="alert">
          {{ formError }}
        </p>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>

      <p class="auth-switch">
        还没有账号？
        <RouterLink to="/register">前往注册</RouterLink>
      </p>
    </section>
  </main>
</template>
