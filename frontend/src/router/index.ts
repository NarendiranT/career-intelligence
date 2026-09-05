import { createRouter, createWebHistory } from 'vue-router'
import { readToken } from '@/api/token'
import { bootstrapAuth, safeNextPath, useAuth } from '@/composables/useAuth'
import SignupView from '@/views/SignupView.vue'
import SigninView from '@/views/SigninView.vue'
import HomeView from '@/views/HomeView.vue'
import UploadView from '@/views/UploadView.vue'
import DocumentsView from '@/views/DocumentsView.vue'
import AnalysisView from '@/views/AnalysisView.vue'
import ChatView from '@/views/ChatView.vue'

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
    { path: '/analysis', name: 'analysis', component: AnalysisView, meta: { title: 'Analysis & Insights', requiresAuth: true } },
    { path: '/chat', name: 'chat', component: ChatView, meta: { title: 'Chat with Assistant', requiresAuth: true } },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to) => {
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
