import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: () => import('../views/DashboardView.vue'), meta: { title: '仪表盘' } },
    { path: '/upload', name: 'upload', component: () => import('../views/UploadView.vue'), meta: { title: '批量上传' } },
    { path: '/annotate', name: 'annotate', component: () => import('../views/AnnotateView.vue'), meta: { title: '标注工作台' } },
    { path: '/train', name: 'train', component: () => import('../views/TrainView.vue'), meta: { title: '模型训练' } },
    { path: '/train/incremental', name: 'train-inc', component: () => import('../views/IncrementalTrainView.vue'), meta: { title: '增量训练' } },
    { path: '/infer', name: 'infer', component: () => import('../views/InferView.vue'), meta: { title: '批量推理' } },
    { path: '/review', name: 'review', component: () => import('../views/ReviewView.vue'), meta: { title: '纠错审核' } },
    { path: '/models', name: 'models', component: () => import('../views/ModelsView.vue'), meta: { title: '模型管理' } },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { title: '系统设置' } },
  ],
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '舌象平台')} · Tongue Diagnosis`
})

export default router
