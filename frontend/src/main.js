import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// Provide the API base URL
app.provide('apiBase', 'http://localhost:8000')

app.use(router)
app.mount('#app')
