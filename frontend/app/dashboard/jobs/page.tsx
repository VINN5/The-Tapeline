'use client'

import { useState, useEffect, useRef } from 'react'
import {
  GitBranch,
  Play,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  ChevronDown,
  Save,
  RefreshCw,
  Table,
  Edit3,
  X,
  Plus,
  Filter,
  ArrowUpDown,
} from 'lucide-react'
import api from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'

interface Connection {
  id: number
  name: string
  db_type: string
}

interface Job {
  id: number
  connection: number
  table_name: string
  batch_size: number
  status: string
  error_message: string | null
  records_count: number
  created_at: string
}

interface DataRecord {
  id: number
  data: { [key: string]: any }
  is_edited: boolean
}

interface FilterRow {
  id: number
  column: string
  operator: string
  value: string
}

const DB_ICONS: Record<string, string> = {
  postgresql: '🐘',
  mysql: '🐬',
  mongodb: '🍃',
  clickhouse: '⚡',
}

const OPERATORS = ['=', '!=', '>', '<', '>=', '<=', 'LIKE']

export default function JobsPage() {
  const [connections, setConnections] = useState<Connection[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // Form state
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null)
  const [tables, setTables] = useState<string[]>([])
  const [loadingTables, setLoadingTables] = useState(false)
  const [selectedTable, setSelectedTable] = useState('')
  const [batchSize, setBatchSize] = useState(100)
  const [fileFormat, setFileFormat] = useState<'json' | 'csv' | 'xlsx'>('json')

  // Query builder state
  const [filters, setFilters] = useState<FilterRow[]>([])
  const [orderBy, setOrderBy] = useState('')
  const [orderDir, setOrderDir] = useState<'asc' | 'desc'>('asc')
  const [showQueryBuilder, setShowQueryBuilder] = useState(false)

  // Active job and its records
  const [activeJob, setActiveJob] = useState<Job | null>(null)
  const [records, setRecords] = useState<DataRecord[]>([])
  const [editedRecords, setEditedRecords] = useState<Map<number, Record<string, any>>>(new Map())
  const [loadingRecords, setLoadingRecords] = useState(false)

  // Message
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Ref for auto-scrolling to grid
  const gridRef = useRef<HTMLDivElement>(null)

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 5000)
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (activeJob && gridRef.current) {
      setTimeout(() => {
        gridRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }, 100)
    }
  }, [activeJob])

  const fetchData = async () => {
    try {
      const [connectionsRes, jobsRes] = await Promise.all([
        api.get('/connections/'),
        api.get('/jobs/'),
      ])
      setConnections(connectionsRes.data.results || connectionsRes.data)
      setJobs(jobsRes.data.results || jobsRes.data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectionChange = async (connectionId: number) => {
    setSelectedConnection(connectionId)
    setSelectedTable('')
    setTables([])
    setLoadingTables(true)
    try {
      const res = await api.get(`/connections/${connectionId}/tables/`)
      setTables(res.data.tables)
    } catch (err: any) {
      showMessage('error', 'Failed to fetch tables. Test the connection first.')
    } finally {
      setLoadingTables(false)
    }
  }

  // Filter helpers
  const addFilter = () => {
    setFilters((prev) => [
      ...prev,
      { id: Date.now(), column: '', operator: '=', value: '' },
    ])
  }

  const updateFilter = (id: number, field: keyof FilterRow, value: string) => {
    setFilters((prev) =>
      prev.map((f) => (f.id === id ? { ...f, [field]: value } : f))
    )
  }

  const removeFilter = (id: number) => {
    setFilters((prev) => prev.filter((f) => f.id !== id))
  }

  const handleCreateJob = async () => {
    if (!selectedConnection || !selectedTable) {
      showMessage('error', 'Please select a connection and table.')
      return
    }
    setCreating(true)
    try {
      // Build clean filters — skip any incomplete rows
      const cleanFilters = filters
        .filter((f) => f.column.trim() && f.value.trim())
        .map(({ column, operator, value }) => ({ column, operator, value }))

      const payload: Record<string, any> = {
        connection: selectedConnection,
        table_name: selectedTable,
        batch_size: batchSize,
      }

      if (cleanFilters.length > 0) payload.filters = cleanFilters
      if (orderBy.trim()) {
        payload.order_by = orderBy.trim()
        payload.order_dir = orderDir
      }

      const res = await api.post('/jobs/', payload)
      showMessage('success', `Job created! Extracted ${res.data.records_count} records.`)
      fetchData()
      handleViewRecords(res.data)
    } catch (err: any) {
      showMessage('error', err.response?.data?.error || 'Failed to create job.')
    } finally {
      setCreating(false)
    }
  }

  const handleViewRecords = async (job: Job) => {
    setActiveJob(job)
    setLoadingRecords(true)
    setEditedRecords(new Map())
    try {
      const res = await api.get(`/jobs/${job.id}/records/`)
      setRecords(res.data)
    } catch {
      showMessage('error', 'Failed to load records.')
    } finally {
      setLoadingRecords(false)
    }
  }

  const handleCellEdit = (recordId: number, key: string, value: string) => {
    setEditedRecords((prev) => {
      const updated = new Map(prev)
      const existing = updated.get(recordId) || {}
      updated.set(recordId, { ...existing, [key]: value })
      return updated
    })
  }

  const getDisplayData = (record: DataRecord) => {
    const edited = editedRecords.get(record.id)
    if (edited) return { ...record.data, ...edited }
    return record.data
  }

  const handleSubmit = async () => {
    if (!activeJob || editedRecords.size === 0) {
      showMessage('error', 'No edits to submit.')
      return
    }
    setSubmitting(true)
    try {
      const recordsToSubmit = Array.from(editedRecords.entries()).map(([id, edits]) => {
        const record = records.find((r) => r.id === id)
        return { id, data: { ...record?.data, ...edits } }
      })

      const res = await api.post(`/jobs/${activeJob.id}/submit/`, {
        records: recordsToSubmit,
        format: fileFormat,
      })

      showMessage('success', res.data.message)
      setEditedRecords(new Map())
      fetchData()
    } catch (err: any) {
      showMessage('error', err.response?.data?.error || 'Failed to submit.')
    } finally {
      setSubmitting(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-4 h-4" style={{ color: '#22c55e' }} />
      case 'failed':    return <XCircle className="w-4 h-4" style={{ color: '#ef4444' }} />
      case 'running':   return <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#22d3ee' }} />
      default:          return <Clock className="w-4 h-4" style={{ color: '#f59e0b' }} />
    }
  }

  const columns = records.length > 0 ? Object.keys(records[0].data) : []

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
          <h1 className="text-2xl font-bold text-white">Extraction Jobs</h1>
          <p className="mt-1" style={{ color: '#64748b' }}>
            Pull data from connected databases and edit it in batches.
          </p>
        </div>
        <button onClick={fetchData}
          className="flex items-center gap-2 px-4 py-2 rounded-xl transition-all"
          style={{ background: '#1e293b', border: '1px solid #334155', color: '#94a3b8' }}>
          <RefreshCw className="w-4 h-4" /> Refresh
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">

        {/* Left: Create Job Form */}
        <div className="lg:col-span-1">
          <div className="rounded-2xl p-6 sticky top-6"
            style={{ background: '#1e293b', border: '1px solid #334155' }}>

            <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
              <Play className="w-5 h-5" style={{ color: '#6366f1' }} />
              New Extraction Job
            </h2>

            {connections.length === 0 ? (
              <div className="text-center py-6">
                <p className="text-sm" style={{ color: '#64748b' }}>No connections available.</p>
                <a href="/dashboard/connections"
                  className="text-sm mt-2 inline-block"
                  style={{ color: '#6366f1' }}>
                  Add a connection first →
                </a>
              </div>
            ) : (
              <div className="space-y-4">

                {/* Connection selector */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#cbd5e1' }}>
                    Database Connection
                  </label>
                  <div className="relative">
                    <select
                      value={selectedConnection || ''}
                      onChange={(e) => handleConnectionChange(Number(e.target.value))}
                      className="w-full px-4 py-3 rounded-xl text-white outline-none appearance-none"
                      style={{ background: '#0f172a', border: '1px solid #334155' }}>
                      <option value="">Select a connection...</option>
                      {connections.map((conn) => (
                        <option key={conn.id} value={conn.id}>
                          {DB_ICONS[conn.db_type]} {conn.name}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                      style={{ color: '#64748b' }} />
                  </div>
                </div>

                {/* Table selector */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#cbd5e1' }}>
                    Table / Collection
                  </label>
                  <div className="relative">
                    {loadingTables ? (
                      <div className="w-full px-4 py-3 rounded-xl flex items-center gap-2"
                        style={{ background: '#0f172a', border: '1px solid #334155' }}>
                        <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#6366f1' }} />
                        <span className="text-sm" style={{ color: '#64748b' }}>Loading tables...</span>
                      </div>
                    ) : (
                      <>
                        <select
                          value={selectedTable}
                          onChange={(e) => setSelectedTable(e.target.value)}
                          disabled={tables.length === 0}
                          className="w-full px-4 py-3 rounded-xl text-white outline-none appearance-none"
                          style={{
                            background: '#0f172a',
                            border: '1px solid #334155',
                            opacity: tables.length === 0 ? 0.5 : 1,
                          }}>
                          <option value="">
                            {tables.length === 0 ? 'Select a connection first...' : 'Select a table...'}
                          </option>
                          {tables.map((table) => (
                            <option key={table} value={table}>{table}</option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                          style={{ color: '#64748b' }} />
                      </>
                    )}
                  </div>
                </div>

                {/* Batch size */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#cbd5e1' }}>
                    Batch Size
                    <span className="ml-2 font-normal" style={{ color: '#64748b' }}>(rows to extract)</span>
                  </label>
                  <input
                    type="number"
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    min={1}
                    max={1000}
                    className="w-full px-4 py-3 rounded-xl text-white outline-none"
                    style={{ background: '#0f172a', border: '1px solid #334155' }}
                  />
                </div>

                {/* ── Query Builder ── */}
                <div className="rounded-xl overflow-hidden"
                  style={{ border: '1px solid #334155' }}>

                  {/* Toggle header */}
                  <button
                    onClick={() => setShowQueryBuilder((v) => !v)}
                    className="w-full flex items-center justify-between px-4 py-3 transition-all"
                    style={{ background: '#0f172a', color: '#94a3b8' }}>
                    <span className="flex items-center gap-2 text-sm font-medium">
                      <Filter className="w-4 h-4" style={{ color: '#6366f1' }} />
                      Query Builder
                      {(filters.length > 0 || orderBy) && (
                        <span className="px-2 py-0.5 rounded-full text-xs"
                          style={{ background: '#6366f120', color: '#6366f1' }}>
                          {filters.filter(f => f.column && f.value).length} filter{filters.filter(f => f.column && f.value).length !== 1 ? 's' : ''}
                          {orderBy ? ` · sort` : ''}
                        </span>
                      )}
                    </span>
                    <ChevronDown
                      className="w-4 h-4 transition-transform"
                      style={{ transform: showQueryBuilder ? 'rotate(180deg)' : 'rotate(0deg)' }}
                    />
                  </button>

                  {showQueryBuilder && (
                    <div className="p-4 space-y-4" style={{ background: '#0f172a50' }}>

                      {/* Filters */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs font-medium uppercase tracking-wide"
                            style={{ color: '#64748b' }}>
                            Filters
                          </span>
                          <button
                            onClick={addFilter}
                            className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg transition-all"
                            style={{ background: '#6366f120', color: '#6366f1' }}>
                            <Plus className="w-3 h-3" /> Add Filter
                          </button>
                        </div>

                        {filters.length === 0 ? (
                          <p className="text-xs" style={{ color: '#475569' }}>
                            No filters — all rows will be extracted.
                          </p>
                        ) : (
                          <div className="space-y-2">
                            {filters.map((f) => (
                              <div key={f.id} className="flex items-center gap-2">
                                {/* Column */}
                                <input
                                  placeholder="column"
                                  value={f.column}
                                  onChange={(e) => updateFilter(f.id, 'column', e.target.value)}
                                  className="flex-1 px-2 py-1.5 rounded-lg text-xs text-white outline-none"
                                  style={{ background: '#1e293b', border: '1px solid #334155', minWidth: 0 }}
                                />
                                {/* Operator */}
                                <select
                                  value={f.operator}
                                  onChange={(e) => updateFilter(f.id, 'operator', e.target.value)}
                                  className="px-2 py-1.5 rounded-lg text-xs text-white outline-none appearance-none"
                                  style={{ background: '#1e293b', border: '1px solid #334155', width: '60px' }}>
                                  {OPERATORS.map((op) => (
                                    <option key={op} value={op}>{op}</option>
                                  ))}
                                </select>
                                {/* Value */}
                                <input
                                  placeholder="value"
                                  value={f.value}
                                  onChange={(e) => updateFilter(f.id, 'value', e.target.value)}
                                  className="flex-1 px-2 py-1.5 rounded-lg text-xs text-white outline-none"
                                  style={{ background: '#1e293b', border: '1px solid #334155', minWidth: 0 }}
                                />
                                {/* Remove */}
                                <button
                                  onClick={() => removeFilter(f.id)}
                                  className="p-1 rounded-lg flex-shrink-0"
                                  style={{ color: '#64748b' }}>
                                  <X className="w-3 h-3" />
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Sort */}
                      <div>
                        <span className="text-xs font-medium uppercase tracking-wide block mb-2"
                          style={{ color: '#64748b' }}>
                          Sort
                        </span>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 flex-1"
                            style={{ position: 'relative' }}>
                            <ArrowUpDown className="w-3 h-3 absolute left-2" style={{ color: '#64748b' }} />
                            <input
                              placeholder="column name"
                              value={orderBy}
                              onChange={(e) => setOrderBy(e.target.value)}
                              className="w-full pl-6 pr-2 py-1.5 rounded-lg text-xs text-white outline-none"
                              style={{ background: '#1e293b', border: '1px solid #334155' }}
                            />
                          </div>
                          <button
                            onClick={() => setOrderDir((d) => d === 'asc' ? 'desc' : 'asc')}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium uppercase transition-all"
                            style={{
                              background: '#6366f120',
                              border: '1px solid #6366f140',
                              color: '#6366f1',
                              minWidth: '48px',
                            }}>
                            {orderDir}
                          </button>
                        </div>
                      </div>

                    </div>
                  )}
                </div>

                {/* Export format */}
                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#cbd5e1' }}>
                    Export Format
                  </label>
                  <div className="flex gap-2">
                    {(['json', 'csv', 'xlsx'] as const).map((fmt) => (
                      <button
                        key={fmt}
                        onClick={() => setFileFormat(fmt)}
                        className="flex-1 py-2 rounded-xl text-sm font-medium transition-all uppercase"
                        style={{
                          background: fileFormat === fmt ? '#6366f120' : '#0f172a',
                          border: fileFormat === fmt ? '1px solid #6366f1' : '1px solid #334155',
                          color: fileFormat === fmt ? '#6366f1' : '#64748b',
                        }}>
                        {fmt}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Run button */}
                <button
                  onClick={handleCreateJob}
                  disabled={creating || !selectedConnection || !selectedTable}
                  className="w-full py-3 rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2 mt-2"
                  style={{
                    background: creating || !selectedConnection || !selectedTable
                      ? '#334155'
                      : 'linear-gradient(135deg, #6366f1, #4f46e5)',
                    cursor: creating || !selectedConnection || !selectedTable
                      ? 'not-allowed'
                      : 'pointer',
                  }}>
                  {creating
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Extracting...</>
                    : <><Play className="w-4 h-4" /> Run Extraction</>
                  }
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right: Jobs list and data grid */}
        <div className="lg:col-span-2 space-y-6">

          {/* Active Job Data Grid */}
          {activeJob && (
            <div ref={gridRef} className="rounded-2xl overflow-hidden"
              style={{ background: '#1e293b', border: '1px solid #6366f1' }}>

              <div className="flex items-center justify-between px-6 py-4"
                style={{ borderBottom: '1px solid #334155', background: '#6366f110' }}>
                <div className="flex items-center gap-3">
                  <Table className="w-5 h-5" style={{ color: '#6366f1' }} />
                  <div>
                    <h3 className="font-semibold text-white">{activeJob.table_name}</h3>
                    <p className="text-xs" style={{ color: '#64748b' }}>
                      {records.length} records
                      {editedRecords.size > 0 && (
                        <span style={{ color: '#f59e0b' }}>
                          {' '}· {editedRecords.size} edited — click Submit to save
                        </span>
                      )}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {editedRecords.size > 0 && (
                    <>
                      <button
                        onClick={() => setEditedRecords(new Map())}
                        className="flex items-center gap-1 px-3 py-2 rounded-xl text-sm transition-all"
                        style={{ background: '#0f172a', color: '#64748b' }}>
                        <X className="w-4 h-4" /> Discard
                      </button>
                      <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all"
                        style={{
                          background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                          color: 'white',
                        }}>
                        {submitting
                          ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</>
                          : <><Save className="w-4 h-4" /> Submit as {fileFormat.toUpperCase()}</>
                        }
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => setActiveJob(null)}
                    className="p-2 rounded-xl transition-all"
                    style={{ background: '#0f172a', color: '#64748b' }}>
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {records.length > 0 && editedRecords.size === 0 && (
                <div className="px-6 py-2 text-xs" style={{ background: '#0f172a50', color: '#64748b' }}>
                  💡 Click any cell below to edit it, then click Submit to save
                </div>
              )}

              {loadingRecords ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#6366f1' }} />
                </div>
              ) : records.length === 0 ? (
                <div className="text-center py-12">
                  <p style={{ color: '#64748b' }}>No records found.</p>
                </div>
              ) : (
                <div className="overflow-auto" style={{ maxHeight: '400px' }}>
                  <table className="w-full text-sm">
                    <thead style={{ position: 'sticky', top: 0, background: '#1e293b', zIndex: 10 }}>
                      <tr style={{ borderBottom: '1px solid #334155' }}>
                        {columns.map((col) => (
                          <th key={col}
                            className="text-left px-4 py-3 text-xs font-medium uppercase whitespace-nowrap"
                            style={{ color: '#64748b' }}>
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((record, rowIndex) => {
                        const displayData = getDisplayData(record)
                        const isEdited = editedRecords.has(record.id)
                        return (
                          <tr key={record.id}
                            style={{
                              borderBottom: rowIndex < records.length - 1 ? '1px solid #0f172a' : 'none',
                              background: isEdited ? '#6366f115' : 'transparent',
                            }}>
                            {columns.map((col) => (
                              <td key={col} className="px-4 py-2">
                                <input
                                  value={displayData[col] ?? ''}
                                  onChange={(e) => handleCellEdit(record.id, col, e.target.value)}
                                  className="w-full px-2 py-1 rounded-lg text-sm text-white outline-none transition-all min-w-24"
                                  style={{ background: 'transparent', border: '1px solid transparent' }}
                                  onFocus={(e) => {
                                    e.target.style.background = '#0f172a'
                                    e.target.style.borderColor = '#6366f1'
                                  }}
                                  onBlur={(e) => {
                                    e.target.style.background = 'transparent'
                                    e.target.style.borderColor = 'transparent'
                                  }}
                                />
                              </td>
                            ))}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Jobs History */}
          <div className="rounded-2xl overflow-hidden"
            style={{ background: '#1e293b', border: '1px solid #334155' }}>

            <div className="px-6 py-4" style={{ borderBottom: '1px solid #334155' }}>
              <h2 className="font-semibold text-white flex items-center gap-2">
                <GitBranch className="w-5 h-5" style={{ color: '#6366f1' }} />
                Job History ({jobs.length})
              </h2>
            </div>

            {jobs.length === 0 ? (
              <div className="text-center py-12">
                <GitBranch className="w-10 h-10 mx-auto mb-3" style={{ color: '#334155' }} />
                <p className="text-white font-medium mb-1">No jobs yet</p>
                <p className="text-sm" style={{ color: '#64748b' }}>
                  Create your first extraction job above.
                </p>
              </div>
            ) : (
              <div className="divide-y" style={{ borderColor: '#334155' }}>
                {jobs.map((job) => (
                  <div key={job.id}
                    className="flex items-center gap-4 px-6 py-4 transition-all hover:bg-white/5 cursor-pointer"
                    onClick={() => job.status === 'completed' && handleViewRecords(job)}>

                    <div className="flex-shrink-0">
                      {getStatusIcon(job.status)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-white truncate">{job.table_name}</p>
                        <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${getStatusColor(job.status)}`}>
                          {job.status}
                        </span>
                      </div>
                      <p className="text-xs mt-0.5" style={{ color: '#64748b' }}>
                        {job.records_count} records · Batch {job.batch_size} · {formatDate(job.created_at)}
                      </p>
                      {job.error_message && (
                        <p className="text-xs mt-1" style={{ color: '#ef4444' }}>{job.error_message}</p>
                      )}
                    </div>

                    {job.status === 'completed' && (
                      <div className="flex items-center gap-1 text-xs px-3 py-1 rounded-xl"
                        style={{ background: '#6366f120', color: '#6366f1' }}>
                        <Edit3 className="w-3 h-3" /> View & Edit
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}