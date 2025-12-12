'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { fetchEvent, fetchPicks, createPick, updatePick, Event, Pick } from '@/lib/api'
import { formatToLocalTime, formatSessionType } from '@/lib/time-utils'
import Link from 'next/link'

const PROP_TYPES = [
  { value: 'race_winner', label: 'Race Winner' },
  { value: 'podium_p1', label: 'Podium P1' },
  { value: 'podium_p2', label: 'Podium P2' },
  { value: 'podium_p3', label: 'Podium P3' },
  { value: 'fastest_lap', label: 'Fastest Lap' },
  { value: 'pole_position', label: 'Pole Position' },
]

const DRIVERS = [
  // Red Bull Racing
  'Max Verstappen',
  'Liam Lawson',
  // Ferrari
  'Charles Leclerc',
  'Lewis Hamilton',
  // McLaren
  'Lando Norris',
  'Oscar Piastri',
  // Mercedes
  'George Russell',
  'Andrea Kimi Antonelli',
  // Aston Martin
  'Fernando Alonso',
  'Lance Stroll',
  // Alpine
  'Pierre Gasly',
  'Jack Doohan',
  // Williams
  'Alex Albon',
  'Carlos Sainz',
  // Visa Cash App RB
  'Yuki Tsunoda',
  'Isack Hadjar',
  // Kick Sauber
  'Nico Hulkenberg',
  'Gabriel Bortoleto',
  // Haas
  'Oliver Bearman',
  'Esteban Ocon',
]

export default function PredictPage() {
  const params = useParams()
  const router = useRouter()
  const { user, getAccessToken } = useAuth()
  const [event, setEvent] = useState<Event | null>(null)
  const [existingPicks, setExistingPicks] = useState<Pick[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  
  // Form state
  const [predictions, setPredictions] = useState<Record<string, string>>({})
  
  useEffect(() => {
    async function loadData() {
      if (!user) {
        router.push('/login')
        return
      }
      
      try {
        setLoading(true)
        const token = await getAccessToken()
        
        if (!token) {
          setError('Please log in to make predictions')
          setLoading(false)
          return
        }
        
        // Fetch event
        const eventData = await fetchEvent(params.id as string, token)
        setEvent(eventData)
        
        // Fetch existing picks
        try {
          const picksData = await fetchPicks(token, { event_id: params.id as string })
          setExistingPicks(picksData.picks)
          
          // Populate form with existing picks
          const existingPredictions: Record<string, string> = {}
          picksData.picks.forEach(pick => {
            existingPredictions[pick.prop_type] = pick.prop_value
          })
          setPredictions(existingPredictions)
        } catch (pickErr) {
          // If picks fetch fails, just log it and continue - user might not have picks yet
          console.log('No existing picks found or error fetching picks:', pickErr)
          setError(null) // Clear any error since this is not critical
        }
      } catch (err) {
        console.error('Error loading data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setLoading(false)
      }
    }
    
    loadData()
  }, [params.id, user, router, getAccessToken])
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!event || event.is_locked) {
      setError('Predictions are locked for this event')
      return
    }
    
    try {
      setSubmitting(true)
      setError(null)
      const token = await getAccessToken()
      
      if (!token) {
        throw new Error('Not authenticated')
      }
      
      // Submit each prediction
      for (const [propType, propValue] of Object.entries(predictions)) {
        if (!propValue) continue
        
        // Check if pick already exists
        const existingPick = existingPicks.find(p => p.prop_type === propType)
        
        if (existingPick) {
          // Update existing pick
          await updatePick(token, existingPick.id, { prop_value: propValue })
        } else {
          // Create new pick
          await createPick(token, {
            event_id: event.id,
            prop_type: propType,
            prop_value: propValue,
          })
        }
      }
      
      setSuccess(true)
      setTimeout(() => {
        router.push('/events')
      }, 2000)
    } catch (err) {
      console.error('Error submitting predictions:', err)
      setError(err instanceof Error ? err.message : 'Failed to submit predictions')
    } finally {
      setSubmitting(false)
    }
  }
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }
  
  if (!event) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Event Not Found</h2>
          <Link href="/events" className="text-blue-600 hover:text-blue-700">
            Back to Events
          </Link>
        </div>
      </div>
    )
  }
  
  if (event.is_locked) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Predictions Locked</h2>
          <p className="text-gray-600 mb-6">
            This event has already started. Predictions are no longer accepted.
          </p>
          <Link
            href="/events"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700"
          >
            Back to Events
          </Link>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <Link href="/events" className="text-blue-600 hover:text-blue-700 text-sm mb-4 inline-block">
            ← Back to Events
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{event.name}</h1>
          <p className="text-gray-600">{event.circuit_name}</p>
          <div className="mt-4 flex items-center gap-4 text-sm text-gray-700">
            <span><strong>Session:</strong> {formatSessionType(event.session_type)}</span>
            <span><strong>Start:</strong> {formatToLocalTime(event.start_time)}</span>
          </div>
        </div>
        
        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
            <p className="text-green-800 font-medium">✓ Predictions saved successfully!</p>
            <p className="text-green-700 text-sm mt-1">Redirecting to events...</p>
          </div>
        )}
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {/* Prediction Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Make Your Predictions</h2>
          
          <div className="space-y-6">
            {PROP_TYPES.map((propType) => (
              <div key={propType.value}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {propType.label}
                </label>
                <select
                  value={predictions[propType.value] || ''}
                  onChange={(e) => setPredictions({ ...predictions, [propType.value]: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                >
                  <option value="" className="text-gray-500">Select a driver</option>
                  {DRIVERS.map((driver) => (
                    <option key={driver} value={driver} className="text-gray-900">
                      {driver}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
          
          <div className="mt-8 flex gap-4">
            <button
              type="submit"
              disabled={submitting || Object.keys(predictions).length === 0}
              className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {submitting ? 'Saving...' : 'Save Predictions'}
            </button>
            <Link
              href="/events"
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md font-medium hover:bg-gray-300 transition-colors"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}
