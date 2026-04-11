'use client'

import { useState, useEffect } from 'react'
import {
  Database,
  Cloud,
  Server,
  CheckCircle,
  XCircle,
  Loader2,
  Trash2,
  TestTube,
  Plus,
  RefreshCw
} from 'lucide-react'
import api from '@/lib/api'

interface Preset {
  id: string
  name: string
  db_type: string
  description: string
  environment: 'local' | 'cloud'
}

interface Connection {
  id: number
  name: string
  db_type: string
  host: string
  port: number
  database_name: string
  created_at: string
}

const DB_ICONS: Record<string, string> = {
  postgresql: '🐘',
  mysql: '🐬',
  mongodb: '🍃',
  clickhouse: '⚡',
}

const DB_COLORS: Record<string, { color: string; bg: string }> = {
  postgresql: { color: '#3b82f6', bg: '#3b82f620' },
  mysql: { color: '#f97316', bg: '#f9731620' },
  mongodb: { color: '#22c55e', bg: '#22c55e20' },
  clickhouse: { color: '#f59e0b', bg: '#f59e0b20' },
}

export default function ConnectionsPage() {
  const [presets, setPresets] = useState<Preset[]>([])
  const [connections, setConnections] = useState<Connection[]>([])
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState<string | null>(null)
  const [testing, setTesting] = useState<number | null>(null)
  const [testResults, setTestResults] = useState<Record<number, boolean | null>>({})
  const [deleting, setDeleting] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 4000)
  }

  const fetchData = async () => {
    try {
      const [presetsRes, connectionsRes] = await Promise.all([
        api.get('/connections/presets/'),
        api.get('/connections/'),
      ])
      setPresets(presetsRes.data)
      setConnections(connectionsRes.data.results || connectionsRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleConnect = async (preset: Preset) => {
    setConnecting(preset.id)
    try {
      await api.post('/connections/connect_preset/', {
        preset_id: preset.id,
      })
      showMessage('success', `${preset.name} connected successfully!`)
      fetchData()
    } catch (err: any) {
      showMessage('error', err.response?.data?.error || 'Failed to connect.')
    } finally {
      setConnecting(null)
    }
  }

  const handleTest = async (connection: Connection) => {
    setTesting(connection.id)
    setTestResults((prev) => ({ ...prev, [connection.id]: null }))
    try {
      const res = await api.post(`/connections/${connection.id}/test/`)
      setTestResults((prev) => ({ ...prev, [connection.id]: res.data.success }))
    } catch {
      setTestResults((prev) => ({ ...prev, [connection.id]: false }))
    } finally {
      setTesting(null)
    }
  }

  const handleDelete = async (id: number) => {
    setDeleting(id)
    try {
      await api.delete(`/connections/${id}/`)
      showMessage('success', 'Connection removed.')
      fetchData()
    } catch {
      showMessage('error', 'Failed to remove connection.')
    } finally {
      setDeleting(null)
    }
  }

  const isConnected = (presetName: string) =>
    connections.some((c) => c.name === presetName)

  const localPresets = presets.filter((p) => p.environment === 'local')
  const cloudPresets = presets.filter((p) => p.environment === 'cloud')

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-8">
        <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#6366f1' }} />
      </div>
    )
  }

  return (
    <div className="p-8">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Database Connections</h1>
          <p className="mt-1" style={{ color: '#64748b' }}>
            Connect to databases — credentials are managed securely by the server.
          </p>
        </div>
        <button
          onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl transition-all"
          style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8' }}>
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className="mb-6 p-4 rounded-xl flex items-center gap-3"
          style={{
            background: message.type === 'success' ? '#22c55e20' : '#ef444420',
            border: `1px solid ${message.type === 'success' ? '#22c55e' : '#ef4444'}`,
            color: message.type === 'success' ? '#22c55e' : '#ef4444',
          }}>
          {message.type === 'success'
            ? <CheckCircle className="w-5 h-5" />
            : <XCircle className="w-5 h-5" />}
          {message.text}
        </div>
      )}

      {/* Local Presets */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Server className="w-5 h-5" style={{ color: '#64748b' }} />
          <h2 className="text-lg font-semibold text-white">Local Databases</h2>
          <span className="text-xs px-2 py-0.5 rounded-full"
            style={{ background: '#334155', color: '#94a3b8' }}>
            Docker
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {localPresets.map((preset) => {
            const connected = isConnected(preset.name)
            const colors = DB_COLORS[preset.db_type] || DB_COLORS.postgresql
            return (
              <div key={preset.id}
                className="p-5 rounded-2xl transition-all"
                style={{
                  background: '#1e293b',
                  border: connected
                    ? `1px solid ${colors.color}40`
                    : '1px solid #334155',
                }}>

                {/* Icon and type */}
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                    style={{ background: colors.bg }}>
                    {DB_ICONS[preset.db_type]}
                  </div>
                  {connected && (
                    <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full"
                      style={{ background: '#22c55e20', color: '#22c55e' }}>
                      <CheckCircle className="w-3 h-3" /> Connected
                    </span>
                  )}
                </div>

                <h3 className="font-semibold text-white mb-1">{preset.name}</h3>
                <p className="text-xs mb-4" style={{ color: '#64748b' }}>
                  {preset.description}
                </p>

                <button
                  onClick={() => handleConnect(preset)}
                  disabled={connected || connecting === preset.id}
                  className="w-full py-2 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
                  style={{
                    background: connected ? '#334155' : colors.bg,
                    color: connected ? '#64748b' : colors.color,
                    cursor: connected ? 'not-allowed' : 'pointer',
                  }}>
                  {connecting === preset.id
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Connecting...</>
                    : connected
                      ? 'Already Connected'
                      : <><Plus className="w-4 h-4" /> Connect</>
                  }
                </button>
              </div>
            )
          })}
        </div>
      </div>

      {/* Cloud Presets */}
      {cloudPresets.length > 0 && (
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Cloud className="w-5 h-5" style={{ color: '#64748b' }} />
            <h2 className="text-lg font-semibold text-white">Cloud Databases</h2>
            <span className="text-xs px-2 py-0.5 rounded-full"
              style={{ background: '#334155', color: '#94a3b8' }}>
              Remote
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {cloudPresets.map((preset) => {
              const connected = isConnected(preset.name)
              const colors = DB_COLORS[preset.db_type] || DB_COLORS.postgresql
              return (
                <div key={preset.id}
                  className="p-5 rounded-2xl transition-all"
                  style={{
                    background: '#1e293b',
                    border: connected
                      ? `1px solid ${colors.color}40`
                      : '1px solid #334155',
                  }}>

                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl"
                      style={{ background: colors.bg }}>
                      {DB_ICONS[preset.db_type]}
                    </div>
                    <div className="flex items-center gap-1">
                      <Cloud className="w-3 h-3" style={{ color: '#6366f1' }} />
                      {connected && (
                        <span className="flex items-center gap-1 text-xs px-2 py-1 rounded-full ml-1"
                          style={{ background: '#22c55e20', color: '#22c55e' }}>
                          <CheckCircle className="w-3 h-3" /> Connected
                        </span>
                      )}
                    </div>
                  </div>

                  <h3 className="font-semibold text-white mb-1">{preset.name}</h3>
                  <p className="text-xs mb-4" style={{ color: '#64748b' }}>
                    {preset.description}
                  </p>

                  <button
                    onClick={() => handleConnect(preset)}
                    disabled={connected || connecting === preset.id}
                    className="w-full py-2 rounded-xl text-sm font-medium transition-all flex items-center justify-center gap-2"
                    style={{
                      background: connected ? '#334155' : colors.bg,
                      color: connected ? '#64748b' : colors.color,
                      cursor: connected ? 'not-allowed' : 'pointer',
                    }}>
                    {connecting === preset.id
                      ? <><Loader2 className="w-4 h-4 animate-spin" /> Connecting...</>
                      : connected
                        ? 'Already Connected'
                        : <><Plus className="w-4 h-4" /> Connect</>
                    }
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Active Connections */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          Active Connections ({connections.length})
        </h2>

        {connections.length === 0 ? (
          <div className="text-center py-12 rounded-2xl"
            style={{ background: '#1e293b', border: '1px solid #334155' }}>
            <Database className="w-12 h-12 mx-auto mb-3" style={{ color: '#334155' }} />
            <p className="text-white font-medium mb-1">No active connections</p>
            <p className="text-sm" style={{ color: '#64748b' }}>
              Click Connect on any database above to get started.
            </p>
          </div>
        ) : (
          <div className="rounded-2xl overflow-hidden"
            style={{ background: '#1e293b', border: '1px solid #334155' }}>
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  {['Database', 'Type', 'Host', 'Status', 'Actions'].map((h) => (
                    <th key={h} className="text-left px-6 py-4 text-xs font-medium uppercase"
                      style={{ color: '#64748b' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {connections.map((conn, i) => {
                  const colors = DB_COLORS[conn.db_type] || DB_COLORS.postgresql
                  const testResult = testResults[conn.id]
                  return (
                    <tr key={conn.id}
                      style={{
                        borderBottom: i < connections.length - 1
                          ? '1px solid #334155'
                          : 'none',
                      }}>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{DB_ICONS[conn.db_type]}</span>
                          <span className="font-medium text-white">{conn.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs px-2 py-1 rounded-full capitalize"
                          style={{ background: colors.bg, color: colors.color }}>
                          {conn.db_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm" style={{ color: '#94a3b8' }}>
                        {conn.host.length > 30 ? conn.host.substring(0, 30) + '...' : conn.host}
                      </td>
                      <td className="px-6 py-4">
                        {testResult === null || testResult === undefined ? (
                          <span className="text-xs" style={{ color: '#64748b' }}>Not tested</span>
                        ) : testResult ? (
                          <span className="flex items-center gap-1 text-xs"
                            style={{ color: '#22c55e' }}>
                            <CheckCircle className="w-3 h-3" /> Online
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs"
                            style={{ color: '#ef4444' }}>
                            <XCircle className="w-3 h-3" /> Failed
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleTest(conn)}
                            disabled={testing === conn.id}
                            className="p-2 rounded-lg transition-all"
                            style={{
                              background: '#0f172a',
                              color: '#6366f1',
                            }}
                            title="Test connection">
                            {testing === conn.id
                              ? <Loader2 className="w-4 h-4 animate-spin" />
                              : <TestTube className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => handleDelete(conn.id)}
                            disabled={deleting === conn.id}
                            className="p-2 rounded-lg transition-all"
                            style={{
                              background: '#0f172a',
                              color: '#ef4444',
                            }}
                            title="Remove connection">
                            {deleting === conn.id
                              ? <Loader2 className="w-4 h-4 animate-spin" />
                              : <Trash2 className="w-4 h-4" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}