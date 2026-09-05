import { createApp } from 'vue'
import App from './App.vue'
import { bootstrapAuth } from '@/composables/useAuth'
import router from './router'
import './style.css'

void bootstrapAuth()
createApp(App).use(router).mount('#app')
