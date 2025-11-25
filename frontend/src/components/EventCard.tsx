'use client'

import Link from 'next/link'
import { Event } from '@/lib/api'
import { formatToLocalTime, formatSessionType } from '@/lib/time-utils'
import CountdownTimer from './CountdownTimer'
import StatusBadge from './StatusBadge'

interface EventCardProps {
  event: Event
}

export default function EventCard({ event }: EventCardProps) {
  const localStartTime = formatToLocalTime(event.start_time)
  const isPredictionLocked = event.is_locked
  
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-bold text-gray-900 mb-1">
            {event.name}
          </h3>
          <p className="text-sm text-gray-600">{event.circuit_name}</p>
        </div>
        <StatusBadge status={event.status} />
      </div>
      
      {/* Session Info */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-700">
          <span className="font-medium mr-2">Session:</span>
          <span>{formatSessionType(event.session_type)}</span>
        </div>
        <div className="flex items-center text-sm text-gray-700">
          <span className="font-medium mr-2">Round:</span>
          <span>{event.round_number} • {event.year}</span>
        </div>
        <div className="flex items-center text-sm text-gray-700">
          <span className="font-medium mr-2">Start Time:</span>
          <span>{localStartTime}</span>
        </div>
      </div>
      
      {/* Countdown and Action */}
      {event.status === 'scheduled' && (
        <div className="border-t pt-4 mt-4">
          <div className="flex justify-between items-center">
            <div>
              <p className="text-xs text-gray-500 mb-1">
                {isPredictionLocked ? 'Predictions locked' : 'Locks in:'}
              </p>
              {!isPredictionLocked && (
                <CountdownTimer targetTime={event.start_time} />
              )}
              {isPredictionLocked && (
                <span className="text-sm font-medium text-gray-500">Event started</span>
              )}
            </div>
            <Link
              href={`/events/${event.id}/predict`}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                isPredictionLocked
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
              aria-disabled={isPredictionLocked}
              onClick={(e) => {
                if (isPredictionLocked) {
                  e.preventDefault()
                }
              }}
            >
              {isPredictionLocked ? 'Locked' : 'Make Predictions'}
            </Link>
          </div>
        </div>
      )}
      
      {/* Completed Event */}
      {event.status === 'completed' && (
        <div className="border-t pt-4 mt-4">
          <Link
            href={`/events/${event.id}/results`}
            className="block w-full px-4 py-2 bg-green-600 text-white text-center rounded-md text-sm font-medium hover:bg-green-700 transition-colors"
          >
            View Results
          </Link>
        </div>
      )}
      
      {/* Live Event */}
      {event.status === 'live' && (
        <div className="border-t pt-4 mt-4">
          <div className="flex items-center justify-center">
            <span className="relative flex h-3 w-3 mr-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
            <span className="text-sm font-medium text-red-600">Live Now</span>
          </div>
        </div>
      )}
    </div>
  )
}
