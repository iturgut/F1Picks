'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { deleteLeague, kickMember, searchUsers, inviteUserToLeague, type UserProfile } from '@/lib/api'

interface League {
  id: string
  name: string
  description?: string
  is_global: boolean
  owner_id?: string
  created_at: string
  member_count?: number
}

interface LeagueMember {
  id: string
  user_id: string
  league_id: string
  role: string
  joined_at: string
  user_name?: string
  user_email?: string
}

export default function LeagueDetailPage() {
  const params = useParams()
  const router = useRouter()
  const leagueId = params.leagueId as string
  const { user, loading: authLoading, getAccessToken } = useAuth()
  const [league, setLeague] = useState<League | null>(null)
  const [members, setMembers] = useState<LeagueMember[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [memberToKick, setMemberToKick] = useState<LeagueMember | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'members'>('leaderboard')
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [inviteLinkCopied, setInviteLinkCopied] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<UserProfile[]>([])
  const [searching, setSearching] = useState(false)
  const [inviting, setInviting] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    } else if (user) {
      loadLeagueData()
    }
  }, [user, authLoading, leagueId])

  const loadLeagueData = async () => {
    if (typeof window === 'undefined') return

    try {
      const token = await getAccessToken()
      if (!token) return

      // Fetch league details
      const leagueResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/leagues/${leagueId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (!leagueResponse.ok) {
        throw new Error('Failed to fetch league')
      }

      const leagueData = await leagueResponse.json()
      setLeague(leagueData)

      // Fetch league members
      const membersResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/leagues/${leagueId}/members`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (membersResponse.ok) {
        const membersData = await membersResponse.json()
        setMembers(membersData)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteLeague = async () => {
    setActionLoading(true)
    try {
      const token = await getAccessToken()
      if (!token) return

      await deleteLeague(token, leagueId)
      router.push('/leagues')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete league')
    } finally {
      setActionLoading(false)
      setShowDeleteModal(false)
    }
  }

  const handleKickMember = async (member: LeagueMember) => {
    if (!confirm(`Are you sure you want to kick ${member.user_name}?`)) return

    setActionLoading(true)
    try {
      const token = await getAccessToken()
      if (!token) return

      await kickMember(token, leagueId, member.user_id)
      await loadLeagueData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to kick member')
    } finally {
      setActionLoading(false)
    }
  }

  const isOwner = user && league && league.owner_id === user.id
  
  // Debug logging
  console.log('Owner check:', { 
    userId: user?.id, 
    leagueOwnerId: league?.owner_id, 
    isOwner 
  })

  const handleCopyInviteLink = async () => {
    const inviteLink = `${window.location.origin}/leagues/${leagueId}/join`
    try {
      await navigator.clipboard.writeText(inviteLink)
      setInviteLinkCopied(true)
      setTimeout(() => setInviteLinkCopied(false), 3000)
    } catch (err) {
      alert('Failed to copy link')
    }
  }

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    
    if (query.trim().length < 2) {
      setSearchResults([])
      return
    }

    setSearching(true)
    try {
      const token = await getAccessToken()
      if (!token) return

      const results = await searchUsers(token, query)
      // Filter out users who are already members AND the current user
      const memberIds = new Set(members.map(m => m.user_id))
      console.log('Search filtering:', {
        currentUserId: user?.id,
        memberIds: Array.from(memberIds),
        resultsBeforeFilter: results.map(u => ({ id: u.id, name: u.name })),
      })
      const filteredResults = results.filter(u => {
        const isNotMember = !memberIds.has(u.id)
        const isNotCurrentUser = u.id !== user?.id
        console.log(`User ${u.name}: isNotMember=${isNotMember}, isNotCurrentUser=${isNotCurrentUser}`)
        return isNotMember && isNotCurrentUser
      })
      console.log('Filtered results:', filteredResults.map(u => ({ id: u.id, name: u.name })))
      setSearchResults(filteredResults)
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      setSearching(false)
    }
  }

  const handleInviteUser = async (userId: string) => {
    setInviting(userId)
    try {
      const token = await getAccessToken()
      if (!token) return

      await inviteUserToLeague(token, leagueId, userId)
      
      // Reload members and clear search
      await loadLeagueData()
      setSearchQuery('')
      setSearchResults([])
      
      alert('User invited successfully!')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to invite user')
    } finally {
      setInviting(null)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading league...</p>
        </div>
      </div>
    )
  }

  if (error || !league) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">❌ {error || 'League not found'}</p>
          <Link
            href="/leagues"
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 inline-block"
          >
            Back to Leagues
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link
          href="/leagues"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Leagues
        </Link>

        {/* League Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900">{league.name}</h1>
                {league.is_global && (
                  <span className="px-3 py-1 text-sm font-medium bg-blue-100 text-blue-800 rounded-full">
                    Global
                  </span>
                )}
                {isOwner && (
                  <span className="px-3 py-1 text-sm font-medium bg-green-100 text-green-800 rounded-full">
                    Owner
                  </span>
                )}
              </div>
              {league.description && (
                <p className="text-gray-600">{league.description}</p>
              )}
            </div>
            {isOwner && (
              <button
                onClick={() => setShowDeleteModal(true)}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
              >
                Delete League
              </button>
            )}
          </div>

          <div className="flex items-center gap-6 text-sm text-gray-500">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              {league.member_count || members.length} {(league.member_count || members.length) === 1 ? 'member' : 'members'}
            </div>
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Created {new Date(league.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('leaderboard')}
                className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                  activeTab === 'leaderboard'
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Leaderboard
              </button>
              <button
                onClick={() => setActiveTab('members')}
                className={`border-b-2 py-4 px-1 text-sm font-medium transition-colors ${
                  activeTab === 'members'
                    ? 'border-red-600 text-red-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Members ({members.length})
              </button>
            </nav>
          </div>
        </div>

        {/* Leaderboard Tab */}
        {activeTab === 'leaderboard' && (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">League Standings</h2>
            </div>
            <div className="p-6">
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🏆</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Leaderboard Coming Soon
                </h3>
                <p className="text-gray-600">
                  League standings and rankings will be displayed here.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Members Tab */}
        {activeTab === 'members' && (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Members ({members.length})
              </h2>
              {isOwner && (
                <button
                  onClick={() => setShowInviteModal(true)}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md transition-colors"
                >
                  Invite Members
                </button>
              )}
            </div>
            {members.length > 0 ? (
              <ul className="divide-y divide-gray-200">
                {members.map((member) => (
                  <li key={member.id} className="px-6 py-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="h-12 w-12 rounded-full bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center text-white font-bold text-lg">
                          {member.user_name?.charAt(0).toUpperCase() || '?'}
                        </div>
                        <div className="ml-4">
                          <div className="flex items-center gap-2">
                            <p className="text-base font-medium text-gray-900">
                              {member.user_name || 'Unknown User'}
                            </p>
                            {member.role === 'owner' && (
                              <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">
                                Owner
                              </span>
                            )}
                            {member.user_id === user?.id && (
                              <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                                You
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">
                            Joined {new Date(member.joined_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      {isOwner && member.user_id !== user?.id && (
                        <button
                          onClick={() => handleKickMember(member)}
                          disabled={actionLoading}
                          className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-12 text-center">
                <p className="text-gray-500">No members yet</p>
              </div>
            )}
          </div>
        )}

        {/* Invite Members Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Invite Members</h2>
                <button
                  onClick={() => {
                    setShowInviteModal(false)
                    setInviteLinkCopied(false)
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-6">
                {/* Shareable Link Section */}
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Share Invite Link</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Anyone with this link can join your league
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      readOnly
                      value={`${typeof window !== 'undefined' ? window.location.origin : ''}/leagues/${leagueId}/join`}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm"
                    />
                    <button
                      onClick={handleCopyInviteLink}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm font-medium"
                    >
                      {inviteLinkCopied ? (
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Copied!
                        </span>
                      ) : (
                        'Copy'
                      )}
                    </button>
                  </div>
                </div>

                {/* Divider */}
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300"></div>
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">or</span>
                  </div>
                </div>

                {/* Search Section */}
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">Search by Username</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Find and invite specific users
                  </p>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search for users..."
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-red-500 focus:border-transparent"
                    />
                    <svg
                      className="absolute left-3 top-2.5 w-5 h-5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    {searching && (
                      <div className="absolute right-3 top-2.5">
                        <div className="animate-spin h-5 w-5 border-2 border-red-600 border-t-transparent rounded-full"></div>
                      </div>
                    )}
                  </div>

                  {/* Search Results */}
                  {searchResults.length > 0 && (
                    <div className="mt-3 max-h-60 overflow-y-auto border border-gray-200 rounded-md">
                      {searchResults.map((searchUser) => (
                        <div
                          key={searchUser.id}
                          className="flex items-center justify-between p-3 hover:bg-gray-50 border-b last:border-b-0"
                        >
                          <div className="flex items-center min-w-0">
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                              {searchUser.name.charAt(0).toUpperCase()}
                            </div>
                            <div className="ml-3 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {searchUser.name}
                              </p>
                              <p className="text-xs text-gray-500 truncate">
                                {searchUser.email}
                              </p>
                            </div>
                          </div>
                          <button
                            onClick={() => handleInviteUser(searchUser.id)}
                            disabled={inviting === searchUser.id}
                            className="ml-3 px-3 py-1 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md disabled:opacity-50 flex-shrink-0"
                          >
                            {inviting === searchUser.id ? 'Inviting...' : 'Invite'}
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {searchQuery.length >= 2 && searchResults.length === 0 && !searching && (
                    <p className="mt-3 text-sm text-gray-500 text-center">No users found</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-md w-full p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Delete League?</h2>
              <p className="text-gray-600 mb-6">
                Are you sure you want to delete "{league?.name}"? This action cannot be undone and will remove all members.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowDeleteModal(false)}
                  disabled={actionLoading}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeleteLeague}
                  disabled={actionLoading}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                >
                  {actionLoading ? 'Deleting...' : 'Delete League'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
