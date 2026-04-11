import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

// Utility function to combine Tailwind classes without conflicts
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format a date string to a readable format
export function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Get a color based on status
export function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    completed: 'text-green-400 bg-green-400/10',
    running: 'text-blue-400 bg-blue-400/10',
    pending: 'text-yellow-400 bg-yellow-400/10',
    failed: 'text-red-400 bg-red-400/10',
  }
  return colors[status] || 'text-gray-400 bg-gray-400/10'
}

// Get a color based on database type
export function getDbTypeColor(dbType: string) {
  const colors: Record<string, string> = {
    postgresql: 'text-blue-400 bg-blue-400/10',
    mysql: 'text-orange-400 bg-orange-400/10',
    mongodb: 'text-green-400 bg-green-400/10',
    clickhouse: 'text-yellow-400 bg-yellow-400/10',
  }
  return colors[dbType] || 'text-gray-400 bg-gray-400/10'
}