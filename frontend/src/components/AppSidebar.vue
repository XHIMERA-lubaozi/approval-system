<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import BrandLogo from './BrandLogo.vue'
import { authState, signOut } from '../auth/store'

const route = useRoute()
const router = useRouter()

const isRequestsSection = computed(() =>
  ['home', 'request-detail', 'request-edit'].includes(String(route.name)),
)
const isNewDraft = computed(() => route.name === 'request-new')

const userInitial = computed(
  () => authState.user?.display_name?.trim().charAt(0) ?? '?',
)

async function onLogout(): Promise<void> {
  signOut()
  await router.replace({ name: 'login' })
}
</script>

<template>
  <aside class="app-sidebar">
    <RouterLink class="sidebar-brand" to="/">
      <BrandLogo compact />
    </RouterLink>

    <div class="sidebar-nav-block">
      <p class="sidebar-section-label">工作台</p>
      <nav class="sidebar-nav" aria-label="主导航">
        <RouterLink
          class="sidebar-link"
          :class="{ 'is-active': isRequestsSection }"
          to="/"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <rect x="4" y="3.5" width="16" height="17" rx="2.5" />
            <path d="M8 8h8M8 12h8M8 16h5" />
          </svg>
          <span>我的申请</span>
        </RouterLink>

        <RouterLink
          class="sidebar-link"
          :class="{ 'is-active': route.name === 'pending' }"
          to="/pending"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <rect x="4" y="4" width="16" height="16" rx="2.5" />
            <path d="M4 13h4l1.5 2h5L16 13h4" />
          </svg>
          <span>待我审批</span>
        </RouterLink>
        <RouterLink
          class="sidebar-link"
          :class="{ 'is-active': isNewDraft }"
          to="/requests/new"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <rect x="4" y="3.5" width="16" height="17" rx="2.5" />
            <path d="M12 8v8M8 12h8" />
          </svg>
          <span>新建草稿</span>
        </RouterLink>
      </nav>
    </div>

    <div class="sidebar-spacer"></div>

    <div class="sidebar-user">
      <div class="sidebar-user-row">
        <span class="sidebar-avatar" aria-hidden="true">{{ userInitial }}</span>
        <div class="sidebar-user-meta">
          <strong>{{ authState.user?.display_name }}</strong>
          <span>@{{ authState.user?.username }}</span>
        </div>
      </div>
      <button
        class="btn btn-ghost sidebar-logout"
        type="button"
        @click="onLogout"
      >
        退出登录
      </button>
    </div>
  </aside>
</template>
