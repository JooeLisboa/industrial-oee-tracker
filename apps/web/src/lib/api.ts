import axios from 'axios'

const TOKEN_KEY = 'access_token'
let unauthorizedHandler: (() => void) | null = null

export const setUnauthorizedHandler = (handler: () => void) => {
  unauthorizedHandler = handler
}

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token: string) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL })

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearToken()
      unauthorizedHandler?.()
      if (!unauthorizedHandler) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api
