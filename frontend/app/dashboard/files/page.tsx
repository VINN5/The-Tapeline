'use client'

import { useState, useEffect } from 'react'
import {
  FileText,
  Download,
  Share2,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle,
  RefreshCw,
  FileJson,
  Sheet,
  Search,
  X,
  User,
  Lock,
  Users,
} from 'lucide-react'
import api from '@/lib/api'
import { formatDate } from '@/lib/utils'

interface StoredFile {
  id: number
  job: number
  file_format: 'json' | 'csv'
  file: string
  source_metadata: {
    db_type?: string
    database_name?: string
    table_name?: string
    extracted_at?: string
    submitted_at?: string
    record_count?: number
  }
  created_at: string
  owner: number
  shared_with: number[]
}

export default function FilesPage() {
  const [files, setFiles] = useState<StoredFile[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterFormat, setFilterFormat] = useState<'all' | 'json' | 'csv'>('all')
  const [shareFileId, setShareFileId] = useState<number | null>(null)
  const [shareUsername, setShareUsername] = useState('')
  const [sharing, setSharing] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 5000)
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    setLoading(true)
    try {
      const res = await api.get('/files/')
      setFiles(res.data.results || res.data)
    } catch {
      showMessage('error', 'Failed to load files.')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (file: StoredFile) => {
    try {
      const backendBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace('/api', '')
      const fileUrl = file.file.startsWith('http') ? file.file : `${backendBase}${file.file}`
      const response = await fetch(fileUrl)
      if (!response.ok) throw new Error('Download failed')
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const filename = file.file.split('/').pop() || `export_${file.id}.${file.file_format}`
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      showMessage('error', 'Failed to download file.')
    }
  }

  const handleShare = async () => {
    if (!shareFileId || !shareUsername.trim()) return
    setSharing(true)
    try {
      await api.post(`/files/${shareFileId}/share/`, { username: shareUsername.trim() })
      showMessage('success', `File shared with ${shareUsername} successfully.`)
      setShareFileId(null)
      setShareUsername('')
      fetchFiles()
    } catch (err: any) {
      showMessage('error', err.response?.data?.error || 'Failed to share file.')
    } finally {
      setSharing(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this file?')) return
    setDeletingId(id)
    try {
      await api.delete(`/files/${id}/`)
      setFiles((prev) => prev.filter((f) => f.id !== id))
      showMessage('success', 'File deleted successfully.')
    } catch {
      showMessage('error', 'Failed to delete file.')
    } finally {
      setDeletingId(null)
    }
  }

  const filteredFiles = files.filter((file) => {
    const matchesSearch =
      file.source_metadata?.table_name?.toLowerCase().includes(search.toLowerCase()) ||
      file.source_metadata?.database_name?.toLowerCase().includes(search.toLowerCase()) ||
      file.file_format.toLowerCase().includes(search.toLowerCase())
    const matchesFormat = filterFormat === 'all' || file.file_format === filterFormat
    return matchesSearch && matchesFormat
  })

  const DB_ICONS: Record<string, string> = {
    postgresql: '🐘',
    mysql: '🐬',
    mongodb: '🍃',
    clickhouse: '⚡',
  }

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
          <h1 className="text-2xl font-bold text-white">Stored Files</h1>
          <p className="mt-1" style={{ color: '#64748b' }}>
            Download, share, or delete your exported JSON and CSV files.
          </p>
        </div>
        <button
          onClick={fetchFiles}
          className="flex items-center gap-2 px-4 py-2 rounded-xl transition-all"
          style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8' }}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Message */}
      {message && (
        <div
          className="mb-6 p-4 rounded-xl flex items-center gap-3"
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

      {/* Share Modal */}
      {shareFileId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.6)' }}>
          <div
            className="rounded-2xl p-6 w-full max-w-md"
            style={{ background: '#1e293b', border: '1px solid #334155' }}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <Share2 className="w-5 h-5" style={{ color: '#6366f1' }} />
                Share File
              </h3>
              <button
                onClick={() => { setShareFileId(null); setShareUsername('') }}
                className="p-1 rounded-lg"
                style={{ color: '#64748b' }}>
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2" style={{ color: '#cbd5e1' }}>
                  Username to share with
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#64748b' }} />
                  <input
                    type="text"
                    value={shareUsername}
                    onChange={(e) => setShareUsername(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleShare()}
                    placeholder="Enter username..."
                    className="w-full pl-10 pr-4 py-3 rounded-xl text-white outline-none"
                    style={{ background: '#0f172a', border: '1px solid #334155' }}
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => { setShareFileId(null); setShareUsername('') }}
                  className="flex-1 py-3 rounded-xl font-medium transition-all"
                  style={{ background: '#0f172a', border: '1px solid #334155', color: '#64748b' }}>
                  Cancel
                </button>
                <button
                  onClick={handleShare}
                  disabled={sharing || !shareUsername.trim()}
                  className="flex-1 py-3 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2"
                  style={{
                    background: sharing || !shareUsername.trim()
                      ? '#334155'
                      : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                    cursor: sharing || !shareUsername.trim() ? 'not-allowed' : 'pointer',
                  }}>
                  {sharing
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Sharing...</>
                    : <><Share2 className="w-4 h-4" /> Share</>}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#64748b' }} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by table, database..."
            className="w-full pl-10 pr-4 py-2.5 rounded-xl text-white outline-none"
            style={{ background: '#1e293b', border: '1px solid #334155' }}
          />
        </div>
        <div className="flex gap-2">
          {(['all', 'json', 'csv'] as const).map((fmt) => (
            <button
              key={fmt}
              onClick={() => setFilterFormat(fmt)}
              className="px-4 py-2.5 rounded-xl text-sm font-medium transition-all uppercase"
              style={{
                background: filterFormat === fmt ? '#6366f120' : '#1e293b',
                border: filterFormat === fmt ? '1px solid #6366f1' : '1px solid #334155',
                color: filterFormat === fmt ? '#6366f1' : '#64748b',
              }}>
              {fmt}
            </button>
          ))}
        </div>
      </div>

      {/* Files Grid */}
      {filteredFiles.length === 0 ? (
        <div
          className="rounded-2xl flex flex-col items-center justify-center py-20"
          style={{ background: '#1e293b', border: '1px solid #334155' }}>
          <FileText className="w-12 h-12 mb-4" style={{ color: '#334155' }} />
          <p className="text-white font-medium mb-1">
            {files.length === 0 ? 'No files yet' : 'No files match your search'}
          </p>
          <p className="text-sm" style={{ color: '#64748b' }}>
            {files.length === 0
              ? 'Submit an extraction job to generate your first file.'
              : 'Try adjusting your search or filter.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredFiles.map((file) => {
            const meta = file.source_metadata
            const isJson = file.file_format === 'json'
            return (
              <div
                key={file.id}
                className="rounded-2xl p-5 flex flex-col gap-4 transition-all hover:border-indigo-500/30"
                style={{ background: '#1e293b', border: '1px solid #334155' }}>

                {/* File header */}
                <div className="flex items-start gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{
                      background: isJson ? '#6366f120' : '#22c55e20',
                      border: `1px solid ${isJson ? '#6366f140' : '#22c55e40'}`,
                    }}>
                    {isJson
                      ? <FileJson className="w-5 h-5" style={{ color: '#6366f1' }} />
                      : <Sheet className="w-5 h-5" style={{ color: '#22c55e' }} />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span
                        className="text-xs font-bold uppercase px-2 py-0.5 rounded-full"
                        style={{
                          background: isJson ? '#6366f120' : '#22c55e20',
                          color: isJson ? '#6366f1' : '#22c55e',
                        }}>
                        {file.file_format}
                      </span>
                      {file.shared_with?.length > 0 && (
                        <span
                          className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1"
                          style={{ background: '#f59e0b20', color: '#f59e0b' }}>
                          <Users className="w-3 h-3" />
                          Shared
                        </span>
                      )}
                    </div>
                    <p className="text-white font-medium mt-1 truncate">
                      {meta?.table_name || `Job #${file.job}`}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
                      {meta?.db_type && DB_ICONS[meta.db_type]} {meta?.database_name || '—'}
                    </p>
                  </div>
                </div>

                {/* Metadata */}
                <div
                  className="rounded-xl p-3 space-y-1.5"
                  style={{ background: '#0f172a' }}>
                  {meta?.record_count !== undefined && (
                    <div className="flex justify-between text-xs">
                      <span style={{ color: '#64748b' }}>Records</span>
                      <span className="text-white font-medium">{meta.record_count}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-xs">
                    <span style={{ color: '#64748b' }}>Created</span>
                    <span className="text-white">{formatDate(file.created_at)}</span>
                  </div>
                  {meta?.submitted_at && (
                    <div className="flex justify-between text-xs">
                      <span style={{ color: '#64748b' }}>Submitted</span>
                      <span className="text-white">{formatDate(meta.submitted_at)}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-auto">
                  <button
                    onClick={() => handleDownload(file)}
                    className="flex-1 flex items-center justify-center gap-2 py-2 rounded-xl text-sm font-medium transition-all"
                    style={{
                      background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                      color: 'white',
                    }}>
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                  <button
                    onClick={() => setShareFileId(file.id)}
                    className="px-3 py-2 rounded-xl transition-all"
                    title="Share file"
                    style={{ background: '#0f172a', border: '1px solid #334155', color: '#94a3b8' }}>
                    <Share2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(file.id)}
                    disabled={deletingId === file.id}
                    className="px-3 py-2 rounded-xl transition-all"
                    title="Delete file"
                    style={{ background: '#0f172a', border: '1px solid #334155', color: '#ef4444' }}>
                    {deletingId === file.id
                      ? <Loader2 className="w-4 h-4 animate-spin" />
                      : <Trash2 className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Summary footer */}
      {files.length > 0 && (
        <div className="mt-6 flex items-center gap-4 text-sm" style={{ color: '#64748b' }}>
          <span>{files.length} total file{files.length !== 1 ? 's' : ''}</span>
          <span>·</span>
          <span>{files.filter(f => f.file_format === 'json').length} JSON</span>
          <span>·</span>
          <span>{files.filter(f => f.file_format === 'csv').length} CSV</span>
          {files.some(f => f.shared_with?.length > 0) && (
            <>
              <span>·</span>
              <span className="flex items-center gap-1">
                <Lock className="w-3 h-3" />
                {files.filter(f => f.shared_with?.length > 0).length} shared
              </span>
            </>
          )}
        </div>
      )}
    </div>
  )
}
