'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Database, Eye, EyeOff, Loader2 } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'

// Validation schema for the login form
const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const { setUser } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    setError('')
    try {
      // Call the login endpoint to get JWT tokens
      const response = await api.post('/accounts/login/', data)
      const { access, refresh } = response.data

      // Store tokens in localStorage
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)

      // Get the user's profile
      const profileResponse = await api.get('/accounts/profile/')
      setUser(profileResponse.data)

      router.push('/dashboard')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)' }}>

      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-20"
          style={{ background: 'radial-gradient(circle, #22d3ee, transparent)' }} />
      </div>

      <div className="w-full max-w-md relative z-10">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4"
            style={{ background: 'linear-gradient(135deg, #6366f1, #22d3ee)' }}>
            <Database className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">TapeLine</h1>
          <p className="mt-2" style={{ color: '#94a3b8' }}>
            Data Connector Platform
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8 shadow-2xl"
          style={{ background: '#1e293b', border: '1px solid #334155' }}>

          <h2 className="text-xl font-semibold text-white mb-6">
            Welcome back
          </h2>

          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg text-sm"
              style={{ background: '#ef444420', border: '1px solid #ef4444', color: '#ef4444' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

            {/* Username */}
            <div>
              <label className="block text-sm font-medium mb-2"
                style={{ color: '#cbd5e1' }}>
                Username
              </label>
              <input
                {...register('username')}
                type="text"
                placeholder="Enter your username"
                className="w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 outline-none transition-all"
                style={{
                  background: '#0f172a',
                  border: errors.username ? '1px solid #ef4444' : '1px solid #334155',
                }}
                onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                onBlur={(e) => e.target.style.borderColor = errors.username ? '#ef4444' : '#334155'}
              />
              {errors.username && (
                <p className="mt-1 text-xs" style={{ color: '#ef4444' }}>
                  {errors.username.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-medium mb-2"
                style={{ color: '#cbd5e1' }}>
                Password
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  className="w-full px-4 py-3 rounded-xl text-white placeholder-gray-500 outline-none transition-all"
                  style={{
                    background: '#0f172a',
                    border: errors.password ? '1px solid #ef4444' : '1px solid #334155',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                  onBlur={(e) => e.target.style.borderColor = errors.password ? '#ef4444' : '#334155'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                  style={{ color: '#64748b' }}>
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs" style={{ color: '#ef4444' }}>
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2 mt-6"
              style={{
                background: loading ? '#4338ca' : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                opacity: loading ? 0.7 : 1,
              }}>
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Register link */}
          <p className="mt-6 text-center text-sm" style={{ color: '#64748b' }}>
            Don&apos;t have an account?{' '}
            <Link href="/register"
              className="font-medium transition-colors"
              style={{ color: '#6366f1' }}>
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}