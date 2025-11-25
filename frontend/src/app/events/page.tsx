'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { fetchEvents, EventListResponse } from '@/lib/api'
import EventCard from '@/components/EventCard'
import Link from 'next/link'

export default function EventsPage() {
  const { user, getAccessToken } = useAuth()
  const [events, setEvents] = useState<EventListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'live' | 'completed'>('upcoming')
  
  useEffect(() => {
    async function loadEvents() {
      try {
        setLoading(true)
        setError(null)
        
        const params: any = {
          page_size: 50,
        }
        
        // Apply filters
        if (filter === 'upcoming') {
          params.upcoming_only = true
          params.status = 'scheduled'
        } else if (filter === 'live') {
          params.status = 'live'
        } else if (filter === 'completed') {
          params.status = 'completed'
        }
        
        // Add auth token if available
        const token = await getAccessToken()
        if (token) {
          params.token = token
        }
        
        const data = await fetchEvents(params)
        setEvents(data)
      } catch (err) {
        console.error('Error loading events:', err)
        setError(err instanceof Error ? err.message : 'Failed to load events')
      } finally {
        setLoading(false)
      }
    }
    
    loadEvents()
  }, [filter, getAccessToken])
  
  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Sign In Required</h2>
          <p className="text-gray-600 mb-6">
            Please sign in to view and make predictions for F1 events.
          </p>
          <Link
            href="/login"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">F1 Events</h1>
          <p className="mt-2 text-sm text-gray-600">
            Browse upcoming races and make your predictions
          </p>
        </div>
      </div>
      
      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex space-x-2 overflow-x-auto pb-2">
          <button
            onClick={() => setFilter('upcoming')}
            className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              filter === 'upcoming'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Upcoming
          </button>
          <button
            onClick={() => setFilter('live')}
            className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              filter === 'live'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Live
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              filter === 'completed'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            All Events
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        
        {!loading && !error && events && events.events.length === 0 && (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-600">No events found for the selected filter.</p>
          </div>
        )}
        
        {!loading && !error && events && events.events.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
