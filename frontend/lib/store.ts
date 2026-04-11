import { create } from 'zustand'

interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'user'
}

interface AuthStore {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User) => void
  logout: () => void
}

// Global state store for authentication
// This keeps the logged in user's info available everywhere in the app
export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  isAuthenticated: false,

  setUser: (user) => set({ user, isAuthenticated: true }),

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },
}))