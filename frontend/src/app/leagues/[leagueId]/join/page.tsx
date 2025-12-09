'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export default function JoinLeaguePage() {
  const params = useParams()
  const router = useRouter()
  const leagueId = params.leagueId as string
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const [league, setLeague] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)

  useEffect(() => {
    if (!authLoading) {
      if (!user) {
        // Redirect to login with return URL
        router.push(`/login?redirect=/leagues/${leagueId}/join`)
      } else {
        loadLeague()
      }
    }
  }, [user, authLoading, leagueId])

  const loadLeague = async () => {
    try {
      const token = await getAccessToken()
      if (!token) return

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/leagues/${leagueId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const data = await response.json()
        setLeague(data)
        // If already a member, redirect to league page
        // For now, we'll just show the join button
      } else if (response.status === 403) {
        // Not a member yet, that's okay
        // Try to fetch basic league info without auth
        const publicResponse = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/leagues/${leagueId}`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
          }
        )
        if (publicResponse.ok) {
          const data = await publicResponse.json()
          setLeague(data)
        }
      } else {
        throw new Error('League not found')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load league')
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async () => {
    setJoining(true)
    setError(null)

    try {
      const token = await getAccessToken()
      if (!token) return

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/leagues/${leagueId}/join`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to join league' }))
        throw new Error(errorData.detail)
      }

      // Success! Redirect to league page
      router.push(`/leagues/${leagueId}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join league')
    } finally {
      setJoining(false)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (error && !league) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-4">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">League Not Found</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => router.push('/leagues')}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Go to My Leagues
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-lg shadow-lg p-8 text-center">
          <div className="text-6xl mb-4">🏆</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Join League
          </h1>
          {league && (
            <>
              <h2 className="text-xl font-semibold text-red-600 mb-4">
                {league.name}
              </h2>
              {league.description && (
                <p className="text-gray-600 mb-6">{league.description}</p>
              )}
              <div className="flex items-center justify-center gap-4 text-sm text-gray-500 mb-8">
                <div className="flex items-center">
                  <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  {league.member_count || 0} members
                </div>
              </div>
            </>
          )}

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={handleJoin}
              disabled={joining}
              className="w-full px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {joining ? 'Joining...' : 'Join League'}
            </button>
            <button
              onClick={() => router.push('/leagues')}
              className="w-full px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
