import { createApp } from 'vue'
import App from './App.vue'
import { bootstrapAuth } from '@/composables/useAuth'
import { isDowntime } from '@/config/env'
import router from './router'
import './style.css'

if (!isDowntime()) {
  void bootstrapAuth()
}
createApp(App).use(router).mount('#app')
