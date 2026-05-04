import axios from 'axios'

const STORAGE_TOKEN = 'td_access_token'
const STORAGE_USER = 'td_user'

export function getStoredToken(): string | null {
  return localStorage.getItem(STORAGE_TOKEN)
}

export function setStoredAuth(token: string, user: { username: string; full_name: string; role: string }) {
  localStorage.setItem(STORAGE_TOKEN, token)
  localStorage.setItem(STORAGE_USER, JSON.stringify(user))
}

export function clearStoredAuth() {
  localStorage.removeItem(STORAGE_TOKEN)
  localStorage.removeItem(STORAGE_USER)
}

export const http = axios.create({
  baseURL: '/api',
  timeout: 30_000,
})

http.interceptors.request.use((config) => {
  const t = getStoredToken()
  if (t) {
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      clearStoredAuth()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`
      }
    }
    return Promise.reject(err)
  }
)

export type UserMe = { username: string; full_name: string; role: string }

export async function loginRequest(username: string, password: string) {
  const body = new URLSearchParams()
  body.set('username', username)
  body.set('password', password)
  const { data } = await http.post<{
    access_token: string
    token_type: string
    role: string
    username: string
    full_name: string
  }>('/v1/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function fetchMe(): Promise<UserMe> {
  const { data } = await http.get<UserMe>('/v1/auth/me')
  return data
}
