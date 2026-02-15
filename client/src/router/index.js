import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
  },
  {
    path: '/progress/:taskId',
    name: 'Progress',
    component: () => import('../views/ProgressView.vue'),
    props: true,
  },
  {
    path: '/result/:taskId',
    name: 'Result',
    component: () => import('../views/ResultView.vue'),
    props: true,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
