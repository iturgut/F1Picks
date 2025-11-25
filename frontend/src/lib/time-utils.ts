/**
 * Time utility functions for event display and countdown timers
 */

/**
 * Format a date to local time string
 */
export function formatToLocalTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  })
}

/**
 * Calculate time remaining until a future date
 * Returns a human-readable string like "2d 5h 30m" or "5h 30m" or "30m"
 */
export function calculateTimeUntil(dateString: string): string {
  const now = new Date()
  const target = new Date(dateString)
  const diff = target.getTime() - now.getTime()
  
  if (diff <= 0) {
    return 'Started'
  }
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  const parts: string[] = []
  
  if (days > 0) {
    parts.push(`${days}d`)
  }
  if (hours > 0 || days > 0) {
    parts.push(`${hours}h`)
  }
  if (minutes > 0 || (days === 0 && hours === 0)) {
    parts.push(`${minutes}m`)
  }
  
  return parts.join(' ')
}

/**
 * Get a status badge color based on event status
 */
export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'scheduled':
      return 'bg-blue-100 text-blue-800'
    case 'live':
      return 'bg-red-100 text-red-800'
    case 'completed':
      return 'bg-green-100 text-green-800'
    case 'cancelled':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

/**
 * Format session type for display
 */
export function formatSessionType(sessionType: string): string {
  return sessionType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/**
 * Check if an event is upcoming (hasn't started yet)
 */
export function isUpcoming(startTime: string): boolean {
  return new Date(startTime) > new Date()
}

/**
 * Check if an event is currently live
 */
export function isLive(startTime: string, endTime: string): boolean {
  const now = new Date()
  return new Date(startTime) <= now && now <= new Date(endTime)
}

/**
 * Check if an event is completed
 */
export function isCompleted(endTime: string): boolean {
  return new Date(endTime) < new Date()
}
