import { createRouter, createWebHistory } from 'vue-router'
import SignupView from '@/views/SignupView.vue'
import SigninView from '@/views/SigninView.vue'
import UploadView from '@/views/UploadView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'signup', component: SignupView, meta: { title: 'Create Account' } },
    { path: '/signup', redirect: '/' },
    { path: '/signin', name: 'signin', component: SigninView, meta: { title: 'Sign In' } },
    { path: '/upload', name: 'upload', component: UploadView, meta: { title: 'Upload Documents' } },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  const page = typeof to.meta.title === 'string' ? to.meta.title : 'Career Intelligence'
  document.title = `Career Intelligence — ${page}`
})

export default router
