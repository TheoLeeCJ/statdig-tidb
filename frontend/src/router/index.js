import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Dashboard from '../components/Dashboard.vue'
import ReportPage from '../components/ReportPage.vue'
import SuperSearch from '../components/SuperSearch.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/report/:md5',
    name: 'ReportPage',
    component: ReportPage
  },
  {
    path: '/supersearch',
    name: 'SuperSearch',
    component: SuperSearch
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router