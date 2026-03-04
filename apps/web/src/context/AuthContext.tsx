import { createContext, ReactNode, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { clearToken, getToken, setToken, setUnauthorizedHandler } from '../lib/api'
import { LoginResponse, User } from '../types/api'

interface AuthContextValue {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate()
  const [token, setTokenState] = useState<string | null>(getToken())
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setTokenState(null)
      setUser(null)
      navigate('/login')
    })
  }, [navigate])


  useEffect(() => {
    const loadUser = async () => {
      if (!token) return
      try {
        const { data } = await api.get<{ user: User }>('/auth/me')
        setUser(data.user)
      } catch {
        clearToken()
        setTokenState(null)
        setUser(null)
      }
    }
    void loadUser()
  }, [token])

  const login = async (email: string, password: string) => {
    const { data } = await api.post<LoginResponse>('/auth/login', { email, password })
    setToken(data.access_token)
    setTokenState(data.access_token)
    setUser(data.user)
  }

  const logout = () => {
    clearToken()
    setTokenState(null)
    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: Boolean(token), login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return ctx
}
