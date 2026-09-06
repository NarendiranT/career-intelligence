import { createRouter, createWebHistory } from 'vue-router'
import { readToken } from '@/api/token'
import { bootstrapAuth, safeNextPath, useAuth } from '@/composables/useAuth'
import { isDowntime } from '@/config/env'
import SignupView from '@/views/SignupView.vue'
import SigninView from '@/views/SigninView.vue'
import HomeView from '@/views/HomeView.vue'
import UploadView from '@/views/UploadView.vue'
import DocumentsView from '@/views/DocumentsView.vue'
import UsageView from '@/views/UsageView.vue'
import ChatView from '@/views/ChatView.vue'
import InterviewView from '@/views/InterviewView.vue'
import MaintenanceView from '@/views/MaintenanceView.vue'
import NotFoundView from '@/views/NotFoundView.vue'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    guest?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'signup', component: SignupView, meta: { title: 'Create Account', guest: true } },
    { path: '/signup', redirect: '/' },
    { path: '/signin', name: 'signin', component: SigninView, meta: { title: 'Sign In', guest: true } },
    { path: '/home', name: 'home', component: HomeView, meta: { title: 'Home', requiresAuth: true } },
    { path: '/upload', name: 'upload', component: UploadView, meta: { title: 'Upload Documents', requiresAuth: true } },
    { path: '/documents', name: 'documents', component: DocumentsView, meta: { title: 'My Documents', requiresAuth: true } },
    { path: '/usage', name: 'usage', component: UsageView, meta: { title: 'Usage', requiresAuth: true } },
    { path: '/analysis', redirect: '/usage' },
    { path: '/chat', name: 'chat', component: ChatView, meta: { title: 'Chat with Assistant', requiresAuth: true } },
    { path: '/interview', name: 'interview', component: InterviewView, meta: { title: 'Prepare for Interviews', requiresAuth: true } },
    { path: '/maintenance', name: 'maintenance', component: MaintenanceView, meta: { title: 'Down for Maintenance' } },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: NotFoundView, meta: { title: 'Page Not Found' } },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
  if (isDowntime()) {
    if (to.name !== 'maintenance') {
      return { name: 'maintenance' }
    }
    return true
  }

  void bootstrapAuth()
  const { isAuthenticated } = useAuth()
  const hasSession = Boolean(readToken()) || isAuthenticated.value
  if (to.meta.requiresAuth && !hasSession) {
    return { name: 'signin', query: { next: to.fullPath } }
  }
  if (to.meta.guest && hasSession) {
    return safeNextPath(to.query.next)
  }
})

router.afterEach((to) => {
  const page = typeof to.meta.title === 'string' ? to.meta.title : 'Career Intelligence'
  document.title = `Career Intelligence — ${page}`
})

export default router
