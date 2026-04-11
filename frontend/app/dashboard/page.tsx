'use client'

import { useEffect, useState } from 'react'
import {
  Database,
  GitBranch,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Plus,
  ArrowRight
} from 'lucide-react'
import Link from 'next/link'
import api from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { formatDate } from '@/lib/utils'

interface Stats {
  connections: number
  jobs: number
  files: number
  completedJobs: number
  failedJobs: number
}

export default function DashboardPage() {
  const { user } = useAuthStore()
  const [stats, setStats] = useState<Stats>({
    connections: 0,
    jobs: 0,
    files: 0,
    completedJobs: 0,
    failedJobs: 0,
  })
  const [recentJobs, setRecentJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [connectionsRes, jobsRes, filesRes] = await Promise.all([
          api.get('/connections/'),
          api.get('/jobs/'),
          api.get('/files/'),
        ])

        const jobs = jobsRes.data.results || jobsRes.data
        const completed = jobs.filter((j: any) => j.status === 'completed').length
        const failed = jobs.filter((j: any) => j.status === 'failed').length

        setStats({
          connections: (connectionsRes.data.results || connectionsRes.data).length,
          jobs: jobs.length,
          files: (filesRes.data.results || filesRes.data).length,
          completedJobs: completed,
          failedJobs: failed,
        })

        setRecentJobs(jobs.slice(0, 5))
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  const statCards = [
    {
      label: 'Connections',
      value: stats.connections,
      icon: Database,
      color: '#6366f1',
      bg: '#6366f120',
      href: '/dashboard/connections',
    },
    {
      label: 'Extraction Jobs',
      value: stats.jobs,
      icon: GitBranch,
      color: '#22d3ee',
      bg: '#22d3ee20',
      href: '/dashboard/jobs',
    },
    {
      label: 'Stored Files',
      value: stats.files,
      icon: FileText,
      color: '#22c55e',
      bg: '#22c55e20',
      href: '/dashboard/files',
    },
    {
      label: 'Success Rate',
      value: stats.jobs > 0
        ? `${Math.round((stats.completedJobs / stats.jobs) * 100)}%`
        : '0%',
      icon: TrendingUp,
      color: '#f59e0b',
      bg: '#f59e0b20',
      href: '/dashboard/jobs',
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" style={{ color: '#22c55e' }} />
      case 'failed': return <XCircle className="w-4 h-4" style={{ color: '#ef4444' }} />
      default: return <Clock className="w-4 h-4" style={{ color: '#f59e0b' }} />
    }
  }

  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'completed': return { color: '#22c55e', background: '#22c55e20' }
      case 'failed': return { color: '#ef4444', background: '#ef444420' }
      case 'running': return { color: '#22d3ee', background: '#22d3ee20' }
      default: return { color: '#f59e0b', background: '#f59e0b20' }
    }
  }

  return (
    <div className="p-8">

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {user?.username}! 👋
        </h1>
        <p className="mt-1" style={{ color: '#64748b' }}>
          Here&apos;s an overview of your data connector platform.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 mb-8 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon
          return (
            <Link key={card.label} href={card.href}>
              <div
                className="p-6 rounded-2xl transition-all hover:scale-105 cursor-pointer"
                style={{
                  background: '#1e293b',
                  border: '1px solid #334155',
                }}>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center"
                    style={{ background: card.bg }}>
                    <Icon className="w-5 h-5" style={{ color: card.color }} />
                  </div>
                  <ArrowRight className="w-4 h-4" style={{ color: '#334155' }} />
                </div>
                <div className="text-3xl font-bold text-white mb-1">
                  {loading ? '...' : card.value}
                </div>
                <div className="text-sm" style={{ color: '#64748b' }}>{card.label}</div>
              </div>
            </Link>
          )
        })}
      </div>

      {/* Recent Jobs */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl p-6"
          style={{ background: '#1e293b', border: '1px solid #334155' }}>

          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white">Recent Jobs</h2>
            <Link href="/dashboard/jobs"
              className="text-sm flex items-center gap-1 transition-colors"
              style={{ color: '#6366f1' }}>
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 rounded-xl animate-pulse"
                  style={{ background: '#0f172a' }} />
              ))}
            </div>
          ) : recentJobs.length === 0 ? (
            <div className="text-center py-8">
              <GitBranch className="w-10 h-10 mx-auto mb-3" style={{ color: '#334155' }} />
              <p className="text-sm" style={{ color: '#64748b' }}>No jobs yet</p>
              <Link href="/dashboard/jobs"
                className="inline-flex items-center gap-2 mt-3 text-sm px-4 py-2 rounded-xl"
                style={{ background: '#6366f120', color: '#6366f1' }}>
                <Plus className="w-4 h-4" /> Create Job
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentJobs.map((job) => (
                <div key={job.id}
                  className="flex items-center gap-3 p-3 rounded-xl"
                  style={{ background: '#0f172a' }}>
                  {getStatusIcon(job.status)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {job.table_name}
                    </p>
                    <p className="text-xs" style={{ color: '#64748b' }}>
                      {formatDate(job.created_at)}
                    </p>
                  </div>
                  <span className="text-xs px-2 py-1 rounded-full capitalize"
                    style={getStatusStyle(job.status)}>
                    {job.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="rounded-2xl p-6"
          style={{ background: '#1e293b', border: '1px solid #334155' }}>

          <h2 className="text-lg font-semibold text-white mb-6">Quick Actions</h2>

          <div className="space-y-3">
            {[
              {
                href: '/dashboard/connections',
                icon: Database,
                label: 'Add Database Connection',
                description: 'Connect to PostgreSQL, MySQL, MongoDB or ClickHouse',
                color: '#6366f1',
                bg: '#6366f120',
              },
              {
                href: '/dashboard/jobs',
                icon: GitBranch,
                label: 'Run Extraction Job',
                description: 'Pull data from a connected database in batches',
                color: '#22d3ee',
                bg: '#22d3ee20',
              },
              {
                href: '/dashboard/files',
                icon: FileText,
                label: 'View Stored Files',
                description: 'Access your exported JSON and CSV files',
                color: '#22c55e',
                bg: '#22c55e20',
              },
            ].map((action) => {
              const Icon = action.icon
              return (
                <Link key={action.href} href={action.href}>
                  <div className="flex items-center gap-4 p-4 rounded-xl transition-all hover:scale-[1.02] cursor-pointer"
                    style={{ background: '#0f172a', border: '1px solid #1e293b' }}>
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                      style={{ background: action.bg }}>
                      <Icon className="w-5 h-5" style={{ color: action.color }} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{action.label}</p>
                      <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
                        {action.description}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 ml-auto flex-shrink-0"
                      style={{ color: '#334155' }} />
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}