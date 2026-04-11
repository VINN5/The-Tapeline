'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import {
  Database,
  LayoutDashboard,
  GitBranch,
  FileText,
  LogOut,
  User,
  ChevronRight,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/lib/store'
import api from '@/lib/api'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, setUser, logout, isAuthenticated } = useAuthStore()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/login')
      return
    }

    // Fetch user profile if not already loaded
    if (!user) {
      api.get('/accounts/profile/')
        .then((res) => setUser(res.data))
        .catch(() => {
          logout()
          router.push('/login')
        })
    }
  }, [])

  const handleLogout = async () => {
    try {
      const refresh = localStorage.getItem('refresh_token')
      await api.post('/accounts/logout/', { refresh })
    } catch {}
    logout()
    router.push('/login')
  }

  const navItems = [
    {
      href: '/dashboard',
      label: 'Overview',
      icon: LayoutDashboard,
    },
    {
      href: '/dashboard/connections',
      label: 'Connections',
      icon: Database,
    },
    {
      href: '/dashboard/jobs',
      label: 'Extraction Jobs',
      icon: GitBranch,
    },
    {
      href: '/dashboard/files',
      label: 'Files',
      icon: FileText,
    },
  ]

  return (
    <div className="min-h-screen flex" style={{ background: '#0f172a' }}>

      {/* Sidebar */}
      <aside
        className="flex flex-col transition-all duration-300"
        style={{
          width: sidebarOpen ? '260px' : '70px',
          background: '#1e293b',
          borderRight: '1px solid #334155',
          minHeight: '100vh',
        }}>

        {/* Logo */}
        <div className="flex items-center gap-3 p-5"
          style={{ borderBottom: '1px solid #334155' }}>
          <div className="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #6366f1, #22d3ee)' }}>
            <Database className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <span className="font-bold text-white text-lg">TapeLine</span>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="ml-auto p-1 rounded-lg transition-colors"
            style={{ color: '#64748b' }}>
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            const Icon = item.icon
            return (
              <Link
                key={item.href}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all"
                style={{
                  background: isActive ? '#6366f120' : 'transparent',
                  color: isActive ? '#6366f1' : '#94a3b8',
                  border: isActive ? '1px solid #6366f130' : '1px solid transparent',
                }}>
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && (
                  <>
                    <span className="text-sm font-medium">{item.label}</span>
                    {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                  </>
                )}
              </Link>
            )
          })}
        </nav>

        {/* User info */}
        <div className="p-3" style={{ borderTop: '1px solid #334155' }}>
          {sidebarOpen && user && (
            <div className="flex items-center gap-3 px-3 py-2 rounded-xl mb-2"
              style={{ background: '#0f172a' }}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: 'linear-gradient(135deg, #6366f1, #22d3ee)' }}>
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-medium text-white truncate">{user.username}</p>
                <p className="text-xs capitalize" style={{ color: '#64748b' }}>{user.role}</p>
              </div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-xl transition-all"
            style={{ color: '#ef4444' }}>
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span className="text-sm font-medium">Logout</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}