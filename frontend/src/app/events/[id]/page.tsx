'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { fetchEvent, fetchEventLeaguePicks } from '@/lib/api'
import type { Event, PickWithUser } from '@/lib/api'

export default function EventDetailPage() {
  const params = useParams()
  const router = useRouter()
  const eventId = params.id as string
  const { user, getAccessToken } = useAuth()
  
  const [event, setEvent] = useState<Event | null>(null)
  const [picks, setPicks] = useState<PickWithUser[]>([])
  const [loading, setLoading] = useState(true)
  const [picksLoading, setPicksLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadEvent()
  }, [eventId])

  useEffect(() => {
    if (user && event) {
      loadPicks()
    }
  }, [user, event])

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

  const loadPicks = async () => {
    try {
      setPicksLoading(true)
      const token = await getAccessToken()
      if (!token) return
      
      const picksData = await fetchEventLeaguePicks(token, eventId)
      setPicks(picksData)
    } catch (err) {
      console.error('Error loading picks:', err)
      // Don't show error for picks, just log it
    } finally {
      setPicksLoading(false)
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
        <div className="bg-white shadow rounded-lg p-6 mb-6">
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

        {/* Predictions Section */}
        {user && picks.length > 0 && (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-red-600 to-red-700">
              <h2 className="text-lg font-semibold text-white">
                Predictions ({picks.length})
              </h2>
              <p className="text-sm text-red-100 mt-1">
                Your predictions and league members' picks
              </p>
            </div>
            
            {picksLoading ? (
              <div className="p-12 text-center">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
                <p className="mt-4 text-gray-600">Loading predictions...</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {/* Group picks by user */}
                {Object.entries(
                  picks.reduce((acc, pick) => {
                    if (!acc[pick.user_id]) {
                      acc[pick.user_id] = {
                        user_name: pick.user_name,
                        user_email: pick.user_email,
                        picks: []
                      }
                    }
                    acc[pick.user_id].picks.push(pick)
                    return acc
                  }, {} as Record<string, { user_name: string; user_email: string; picks: PickWithUser[] }>)
                ).map(([userId, { user_name, picks: userPicks }]) => (
                  <div key={userId} className="p-6 hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center text-white font-bold text-sm">
                          {user_name.charAt(0).toUpperCase()}
                        </div>
                        <div className="ml-3">
                          <p className="text-base font-semibold text-gray-900">
                            {user_name}
                            {userId === user?.id && (
                              <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                                You
                              </span>
                            )}
                          </p>
                          <p className="text-sm text-gray-500">
                            {userPicks.length} {userPicks.length === 1 ? 'prediction' : 'predictions'}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 ml-13">
                      {userPicks.map((pick) => (
                        <div
                          key={pick.id}
                          className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-blue-100 text-blue-800 uppercase">
                              {pick.prop_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-xs text-gray-500">
                              {new Date(pick.created_at).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric'
                              })}
                            </span>
                          </div>
                          <p className="text-lg font-bold text-gray-900 mt-2">
                            {pick.prop_value}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
