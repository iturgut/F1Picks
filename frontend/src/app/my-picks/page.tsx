'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { fetchPicks, fetchEvent, fetchEventResults, fetchPickScores } from '@/lib/api'
import type { Pick, Event, Result, Score } from '@/lib/api'

interface PickWithScore extends Pick {
  score?: Score
  result?: Result
  isCorrect?: boolean
}

interface GroupedPicks {
  [eventId: string]: {
    event: Event | null
    picks: PickWithScore[]
    results: Result[]
  }
}

export default function MyPicksPage() {
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const router = useRouter()
  const [groupedPicks, setGroupedPicks] = useState<GroupedPicks>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
      return
    }

    if (user) {
      loadPicks()
    }
  }, [user, authLoading, router])

  const loadPicks = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Get user's access token
      const token = await getAccessToken()
      
      if (!token) {
        setError('Please sign in to view your picks')
        return
      }

      const response = await fetchPicks(token, {
        page: 1,
        page_size: 50
      })
      
      // Group picks by event
      const grouped: GroupedPicks = {}
      
      // Fetch scores for all picks
      let scores: Score[] = []
      try {
        scores = await fetchPickScores(token, response.picks.map(p => p.id))
      } catch (err) {
        console.error('Failed to fetch scores:', err)
      }
      
      // Create score map for quick lookup
      const scoreMap = new Map(scores.map(s => [s.pick_id, s]))
      
      for (const pick of response.picks) {
        if (!grouped[pick.event_id]) {
          grouped[pick.event_id] = {
            event: null,
            picks: [],
            results: []
          }
          
          // Fetch event details
          try {
            const event = await fetchEvent(pick.event_id)
            grouped[pick.event_id].event = event
            
            // Fetch results if event is completed
            if (event.status === 'completed') {
              try {
                const results = await fetchEventResults(pick.event_id)
                grouped[pick.event_id].results = results
              } catch (err) {
                console.error(`Failed to fetch results for event ${pick.event_id}:`, err)
              }
            }
          } catch (err) {
            console.error(`Failed to fetch event ${pick.event_id}:`, err)
          }
        }
        
        // Attach score and result to pick
        const pickWithScore: PickWithScore = { ...pick }
        const score = scoreMap.get(pick.id)
        if (score) {
          pickWithScore.score = score
          pickWithScore.isCorrect = score.exact_match || score.points > 0
        }
        
        // Find matching result
        const result = grouped[pick.event_id].results.find(r => r.prop_type === pick.prop_type)
        if (result) {
          pickWithScore.result = result
          // If no score yet, determine correctness by comparing values
          if (!pickWithScore.isCorrect && pickWithScore.isCorrect !== false) {
            pickWithScore.isCorrect = pick.prop_value.toLowerCase() === result.actual_value.toLowerCase()
          }
        }
        
        grouped[pick.event_id].picks.push(pickWithScore)
      }
      
      // Sort picks within each event: correct first, then incorrect, then unscored
      for (const eventId in grouped) {
        grouped[eventId].picks.sort((a, b) => {
          // Correct picks first
          if (a.isCorrect && !b.isCorrect) return -1
          if (!a.isCorrect && b.isCorrect) return 1
          // Then by points (higher first)
          const aPoints = a.score?.points || 0
          const bPoints = b.score?.points || 0
          if (aPoints !== bPoints) return bPoints - aPoints
          // Finally by creation date (newer first)
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        })
      }
      
      setGroupedPicks(grouped)
    } catch (err) {
      console.error('Error loading picks:', err)
      setError('Failed to load your picks')
    } finally {
      setLoading(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading your picks...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Picks</h1>
          <p className="mt-2 text-gray-600">
            View and manage your predictions for upcoming events
          </p>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Picks List */}
        {Object.keys(groupedPicks).length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <div className="text-6xl mb-4">🏎️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No picks yet
            </h3>
            <p className="text-gray-600 mb-6">
              Start making predictions for upcoming events!
            </p>
            <Link
              href="/events"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
            >
              View Events
            </Link>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedPicks).map(([eventId, { event, picks }]) => (
              <div key={eventId} className="bg-white shadow rounded-lg overflow-hidden">
                {/* Event Header */}
                <div className="bg-gradient-to-r from-red-600 to-red-700 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-white">
                        {event?.name || 'Loading event...'}
                      </h3>
                      {event && (
                        <div className="flex items-center space-x-3 mt-1 text-red-100 text-sm">
                          <span>🏁 {event.circuit_name}</span>
                          <span>•</span>
                          <span>{new Date(event.start_time).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric',
                            year: 'numeric'
                          })}</span>
                          <span>•</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            event.is_locked 
                              ? 'bg-red-800 text-red-100' 
                              : 'bg-green-500 text-white'
                          }`}>
                            {event.is_locked ? '🔒 Locked' : '✅ Open'}
                          </span>
                        </div>
                      )}
                    </div>
                    <Link
                      href={`/events/${eventId}`}
                      className="ml-4 px-4 py-2 bg-white text-red-600 rounded-md text-sm font-medium hover:bg-red-50 transition-colors"
                    >
                      View Event
                    </Link>
                  </div>
                </div>

                {/* Picks for this event */}
                <div className="divide-y divide-gray-200">
                  {picks.map((pick) => (
                    <div key={pick.id} className={`p-6 transition-colors ${
                      pick.isCorrect === true ? 'bg-green-50 hover:bg-green-100' :
                      pick.isCorrect === false ? 'bg-red-50 hover:bg-red-100' :
                      'hover:bg-gray-50'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {/* Pick Type Badge and Status */}
                          <div className="flex items-center space-x-3 mb-3">
                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 uppercase">
                              {pick.prop_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-sm text-gray-500">
                              Predicted {new Date(pick.created_at).toLocaleDateString('en-US', { 
                                month: 'short', 
                                day: 'numeric'
                              })}
                            </span>
                            {/* Correctness Badge */}
                            {pick.isCorrect === true && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-green-600 text-white">
                                ✓ Correct
                              </span>
                            )}
                            {pick.isCorrect === false && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-red-600 text-white">
                                ✗ Incorrect
                              </span>
                            )}
                            {/* Points Badge */}
                            {pick.score && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-bold bg-yellow-100 text-yellow-800">
                                {pick.score.points} pts
                              </span>
                            )}
                          </div>
                          
                          {/* Pick Value and Result */}
                          <div className="space-y-2">
                            <div className="flex items-center space-x-2">
                              <span className="text-sm font-medium text-gray-600">Your Pick:</span>
                              <span className="text-2xl">🏁</span>
                              <p className="text-xl font-bold text-gray-900">
                                {pick.prop_value}
                              </p>
                            </div>
                            
                            {/* Actual Result */}
                            {pick.result && (
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-medium text-gray-600">Actual Result:</span>
                                <span className="text-2xl">🏆</span>
                                <p className={`text-xl font-bold ${
                                  pick.isCorrect ? 'text-green-700' : 'text-red-700'
                                }`}>
                                  {pick.result.actual_value}
                                </p>
                              </div>
                            )}
                          </div>
                          
                          {/* Metadata if exists */}
                          {pick.prop_metadata && Object.keys(pick.prop_metadata).length > 0 && (
                            <div className="mt-2 text-sm text-gray-600">
                              {Object.entries(pick.prop_metadata).map(([key, value]) => (
                                <span key={key} className="mr-3">
                                  <span className="font-medium">{key}:</span> {String(value)}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Footer with pick count and stats */}
                <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      {picks.length} {picks.length === 1 ? 'prediction' : 'predictions'} for this event
                    </p>
                    {event?.status === 'completed' && picks.some(p => p.score || p.result) ? (
                      <div className="flex items-center space-x-4 text-sm">
                        <span className="text-green-700 font-medium">
                          ✓ {picks.filter(p => p.isCorrect === true).length} Correct
                        </span>
                        <span className="text-red-700 font-medium">
                          ✗ {picks.filter(p => p.isCorrect === false).length} Incorrect
                        </span>
                        <span className="text-yellow-700 font-medium">
                          🏆 {picks.reduce((sum, p) => sum + (p.score?.points || 0), 0)} Total Points
                        </span>
                      </div>
                    ) : event?.status === 'completed' ? (
                      <span className="text-sm text-gray-500 italic">
                        ⏳ Results pending
                      </span>
                    ) : (
                      <span className="text-sm text-gray-500 italic">
                        Event not yet completed
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
