'use client'

import { useEffect, useState } from 'react'
import { calculateTimeUntil } from '@/lib/time-utils'

interface CountdownTimerProps {
  targetTime: string
  onExpire?: () => void
}

export default function CountdownTimer({ targetTime, onExpire }: CountdownTimerProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('')
  
  useEffect(() => {
    // Initial calculation
    const updateTime = () => {
      const remaining = calculateTimeUntil(targetTime)
      setTimeRemaining(remaining)
      
      if (remaining === 'Started' && onExpire) {
        onExpire()
      }
    }
    
    updateTime()
    
    // Update every minute
    const interval = setInterval(updateTime, 60000)
    
    return () => clearInterval(interval)
  }, [targetTime, onExpire])
  
  if (!timeRemaining) {
    return <span className="text-sm text-gray-500">Loading...</span>
  }
  
  if (timeRemaining === 'Started') {
    return <span className="text-sm font-medium text-red-600">Started</span>
  }
  
  return (
    <span className="text-sm font-medium text-gray-900">
      {timeRemaining}
    </span>
  )
}
