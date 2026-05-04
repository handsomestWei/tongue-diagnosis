import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserMe } from '../lib/http'
import { clearStoredAuth, fetchMe, getStoredToken, loginRequest, setStoredAuth } from '../lib/http'

export type Role = 'admin' | 'annotator' | 'viewer'

function parseStoredUser(): UserMe | null {
  try {
    const raw = localStorage.getItem('td_user')
    if (!raw) return null
    return JSON.parse(raw) as UserMe
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getStoredToken())
  const user = ref<UserMe | null>(parseStoredUser())
  const loading = ref(false)

  const role = computed(() => (user.value?.role ?? '') as Role)
  const isAuthenticated = computed(() => Boolean(token.value && user.value))

  const canUpload = computed(() => role.value === 'admin' || role.value === 'annotator')
  const canTrain = computed(() => canUpload.value)
  const canManageModels = computed(() => role.value === 'admin')
  const canSettings = computed(() => role.value === 'admin')
  /** viewer 仅查看推理/纠错列表，不可提交 mutation */
  const canMutateReview = computed(() => role.value === 'admin' || role.value === 'annotator')

  function setSession(accessToken: string, u: UserMe) {
    token.value = accessToken
    user.value = u
    setStoredAuth(accessToken, u)
  }

  function logout() {
    token.value = null
    user.value = null
    clearStoredAuth()
  }

  async function login(username: string, password: string) {
    loading.value = true
    try {
      const data = await loginRequest(username, password)
      setSession(data.access_token, {
        username: data.username,
        full_name: data.full_name,
        role: data.role,
      })
    } finally {
      loading.value = false
    }
  }

  async function hydrateFromServer() {
    if (!token.value) return
    try {
      const me = await fetchMe()
      user.value = me
      setStoredAuth(token.value, me)
    } catch {
      logout()
    }
  }

  function hasRouteRole(allow?: Role[]) {
    if (!allow || allow.length === 0) return true
    return allow.includes(role.value)
  }

  return {
    token,
    user,
    loading,
    role,
    isAuthenticated,
    canUpload,
    canTrain,
    canManageModels,
    canSettings,
    canMutateReview,
    login,
    logout,
    hydrateFromServer,
    setSession,
    hasRouteRole,
  }
})
