import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from 'vue-router'

import { setUnauthorizedHandler } from '../api/client'
import { authState, restoreSession, signOut } from '../auth/store'
import HomePage from '../views/HomePage.vue'
import LoginPage from '../views/LoginPage.vue'
import RegisterPage from '../views/RegisterPage.vue'
import RequestDetailPage from '../views/RequestDetailPage.vue'
import RequestFormPage from '../views/RequestFormPage.vue'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    guestOnly?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
    meta: { requiresAuth: true },
  },
  { path: '/pending', name: 'pending', component: HomePage, meta: { requiresAuth: true } },
  {
    path: '/requests',
    redirect: '/',
  },
  {
    path: '/requests/new',
    name: 'request-new',
    component: RequestFormPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/:id/edit',
    name: 'request-edit',
    component: RequestFormPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/requests/:id',
    name: 'request-detail',
    component: RequestDetailPage,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterPage,
    meta: { guestOnly: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  await restoreSession()

  if (to.meta.requiresAuth && authState.user === null) {
    const query = to.fullPath === '/' ? {} : { redirect: to.fullPath }
    return { name: 'login', query }
  }

  if (to.meta.guestOnly && authState.user !== null) {
    return { name: 'home' }
  }

  return true
})

setUnauthorizedHandler(() => {
  signOut()

  const current = router.currentRoute.value
  if (current.meta.requiresAuth && current.name !== 'login') {
    void router
      .replace({ name: 'login', query: { redirect: current.fullPath } })
      .catch(() => undefined)
  }
})
