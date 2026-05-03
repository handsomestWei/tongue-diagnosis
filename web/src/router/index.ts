import { createRouter, createWebHistory } from 'vue-router'
import type { Role } from '../stores/auth'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    /** 无需登录（如登录页） */
    public?: boolean
    /** blank = 无侧栏布局 */
    layout?: 'default' | 'blank'
    /** 允许的角色；不填表示仅需登录 */
    roles?: Role[]
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登录', public: true, layout: 'blank' },
    },
    {
      path: '/forbidden',
      name: 'forbidden',
      component: () => import('../views/ForbiddenView.vue'),
      meta: { title: '无权访问', layout: 'blank' },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: '仪表盘' },
    },
    {
      path: '/upload',
      name: 'upload',
      component: () => import('../views/UploadView.vue'),
      meta: { title: '批量上传', roles: ['admin', 'annotator'] },
    },
    {
      path: '/annotate',
      name: 'annotate',
      component: () => import('../views/AnnotateView.vue'),
      meta: { title: '标注工作台', roles: ['admin', 'annotator'] },
    },
    {
      path: '/train',
      name: 'train',
      component: () => import('../views/TrainView.vue'),
      meta: { title: '模型训练', roles: ['admin', 'annotator'] },
    },
    {
      path: '/train/incremental',
      name: 'train-inc',
      component: () => import('../views/IncrementalTrainView.vue'),
      meta: { title: '增量训练', roles: ['admin', 'annotator'] },
    },
    {
      path: '/infer',
      name: 'infer',
      component: () => import('../views/InferView.vue'),
      meta: { title: '批量推理' },
    },
    {
      path: '/review',
      name: 'review',
      component: () => import('../views/ReviewView.vue'),
      meta: { title: '纠错审核' },
    },
    {
      path: '/models',
      name: 'models',
      component: () => import('../views/ModelsView.vue'),
      meta: { title: '模型管理', roles: ['admin'] },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { title: '系统设置', roles: ['admin'] },
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (to.name === 'login' && auth.isAuthenticated) {
      next({ path: '/' })
      return
    }
    next()
    return
  }

  if (!auth.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  const allow = to.meta.roles
  if (allow && allow.length && !auth.hasRouteRole(allow)) {
    next({ name: 'forbidden' })
    return
  }

  next()
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title ?? '舌象平台')} · Tongue Diagnosis`
})

export default router
