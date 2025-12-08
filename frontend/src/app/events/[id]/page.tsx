'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { fetchEvent } from '@/lib/api'
import type { Event } from '@/lib/api'

export default function EventDetailPage() {
  const params = useParams()
  const router = useRouter()
  const eventId = params.id as string
  
  const [event, setEvent] = useState<Event | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadEvent()
  }, [eventId])

  const loadEvent = async () => {
    try {
      setLoading(true)
      setError(null)
      const eventData = await fetchEvent(eventId)
      setEvent(eventData)
    } catch (err) {
      console.error('Error loading event:', err)
      setError('Failed to load event details')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading event...</p>
        </div>
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <p className="text-red-800 mb-4">{error || 'Event not found'}</p>
            <Link
              href="/events"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              ← Back to Events
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const eventDate = new Date(event.start_time)
  const isLocked = event.is_locked

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back button */}
        <div className="mb-6">
          <Link
            href="/events"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to Events
          </Link>
        </div>

        {/* Event Header */}
        <div className="bg-white shadow rounded-lg overflow-hidden mb-6">
          <div className="px-6 py-8">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">
                  {event.name}
                </h1>
                <div className="flex items-center space-x-4 text-gray-600">
                  <span className="flex items-center">
                    🏁 {event.circuit_name}
                  </span>
                  <span>•</span>
                  <span>{event.session_type.replace('_', ' ').toUpperCase()}</span>
                  <span>•</span>
                  <span>Round {event.round_number}</span>
                </div>
              </div>
              <div className="ml-4">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  event.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                  event.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                  event.status === 'completed' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {event.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Start Time</p>
                <p className="text-lg font-semibold text-gray-900">
                  {eventDate.toLocaleDateString()} {eventDate.toLocaleTimeString()}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Year</p>
                <p className="text-lg font-semibold text-gray-900">{event.year}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Predictions</p>
                <p className="text-lg font-semibold text-gray-900">
                  {isLocked ? '🔒 Locked' : '✅ Open'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-white shadow rounded-lg p-6">
          {isLocked ? (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🔒</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Predictions Locked
              </h3>
              <p className="text-gray-600 mb-6">
                This event has already started. Predictions are no longer accepted.
              </p>
              <Link
                href="/my-picks"
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
              >
                View My Picks
              </Link>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-6xl mb-4">🏎️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Make Your Predictions
              </h3>
              <p className="text-gray-600 mb-6">
                Predict the outcome of this event before it starts!
              </p>
              <Link
                href={`/events/${event.id}/predict`}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
              >
                Make Predictions →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
