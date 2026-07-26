import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const AUTH_TOKEN_KEY = 'auth_token'

const authClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
})

interface User {
  id: string
  name: string
  email: string
  avatar?: string
  role: 'farmer' | 'agronomist' | 'admin'
  farmCount?: number
  reportsCount?: number
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, role: User['role']) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    try {
      const token = localStorage.getItem(AUTH_TOKEN_KEY)
      if (token) {
        const response = await authClient.get('/auth/me')
        setUser(response.data)
      }
    } catch {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = async (email: string, password: string) => {
    const response = await authClient.post('/auth/login', { email, password })
    const { token, user: userData } = response.data
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    setUser(userData)
    authClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  const register = async (name: string, email: string, password: string, role: User['role']) => {
    const response = await authClient.post('/auth/register', { name, email, password, role })
    const { token, user: userData } = response.data
    localStorage.setItem(AUTH_TOKEN_KEY, token)
    setUser(userData)
    authClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  const logout = async () => {
    try {
      await authClient.post('/auth/logout')
    } finally {
      localStorage.removeItem(AUTH_TOKEN_KEY)
      setUser(null)
      delete authClient.defaults.headers.common['Authorization']
    }
  }

  const updateProfile = async (data: Partial<User>) => {
    const response = await authClient.patch('/auth/profile', data)
    setUser(response.data)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}