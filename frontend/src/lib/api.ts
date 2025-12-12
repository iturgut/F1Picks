/**
 * API client for F1 Picks backend
 */

import { env } from './env'

const API_BASE_URL = env.NEXT_PUBLIC_BACKEND_URL

export interface Event {
  id: string
  name: string
  circuit_id: string
  circuit_name: string
  session_type: string
  round_number: number
  year: number
  start_time: string
  end_time: string
  status: string
  is_locked: boolean
  created_at: string
  updated_at: string
}

export interface EventListResponse {
  events: Event[]
  total: number
  page: number
  page_size: number
}

export interface Pick {
  id: string
  user_id: string
  event_id: string
  prop_type: string
  prop_value: string
  prop_metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PickWithUser extends Pick {
  user_name: string
  user_email: string
}

export interface Result {
  id: string
  event_id: string
  prop_type: string
  actual_value: string
  result_metadata?: Record<string, unknown>
  source: string
  ingested_at: string
  updated_at: string
}

export interface Score {
  id: string
  pick_id: string
  user_id: string
  points: number
  margin?: number
  exact_match: boolean
  scoring_metadata?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface PickListResponse {
  picks: Pick[]
  total: number
  page: number
  page_size: number
}

export interface CreatePickData {
  event_id: string
  prop_type: string
  prop_value: string
  prop_metadata?: Record<string, unknown>
}

export interface UpdatePickData {
  prop_value: string
  prop_metadata?: Record<string, unknown>
}

/**
 * Fetch events from the API
 */
export async function fetchEvents(params?: {
  status?: string
  session_type?: string
  year?: number
  upcoming_only?: boolean
  page?: number
  page_size?: number
  token?: string
}): Promise<EventListResponse> {
  const searchParams = new URLSearchParams()
  
  if (params?.status) searchParams.append('status', params.status)
  if (params?.session_type) searchParams.append('session_type', params.session_type)
  if (params?.year) searchParams.append('year', params.year.toString())
  if (params?.upcoming_only) searchParams.append('upcoming_only', 'true')
  if (params?.page) searchParams.append('page', params.page.toString())
  if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (params?.token) {
    headers['Authorization'] = `Bearer ${params.token}`
  }
  
  const response = await fetch(
    `${API_BASE_URL}/events?${searchParams.toString()}`,
    { headers }
  )
  
  if (!response.ok) {
    throw new Error(`Failed to fetch events: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Fetch a single event by ID
 */
export async function fetchEvent(eventId: string, token?: string): Promise<Event> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}/events/${eventId}`, { headers })
  
  if (!response.ok) {
    throw new Error(`Failed to fetch event: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Fetch user's picks
 */
export async function fetchPicks(
  token: string,
  params?: {
    event_id?: string
    prop_type?: string
    page?: number
    page_size?: number
  }
): Promise<PickListResponse> {
  const searchParams = new URLSearchParams()
  
  if (params?.event_id) searchParams.append('event_id', params.event_id)
  if (params?.prop_type) searchParams.append('prop_type', params.prop_type)
  if (params?.page) searchParams.append('page', params.page.toString())
  if (params?.page_size) searchParams.append('page_size', params.page_size.toString())
  
  const response = await fetch(
    `${API_BASE_URL}/picks?${searchParams.toString()}`,
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  )
  
  if (!response.ok) {
    throw new Error(`Failed to fetch picks: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Create a new pick
 */
export async function createPick(
  token: string,
  data: CreatePickData
): Promise<Pick> {
  const response = await fetch(`${API_BASE_URL}/picks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to create pick')
  }
  
  return response.json()
}

/**
 * Update an existing pick
 */
export async function updatePick(
  token: string,
  pickId: string,
  data: UpdatePickData
): Promise<Pick> {
  const response = await fetch(`${API_BASE_URL}/picks/${pickId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to update pick')
  }
  
  return response.json()
}

/**
 * Delete a pick
 */
export async function deletePick(token: string, pickId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/picks/${pickId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to delete pick')
  }
}

/**
 * Fetch picks for an event from league members
 */
export async function fetchEventLeaguePicks(
  token: string,
  eventId: string
): Promise<PickWithUser[]> {
  const response = await fetch(
    `${API_BASE_URL}/picks/events/${eventId}/league-picks`,
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  )
  
  if (!response.ok) {
    throw new Error(`Failed to fetch event league picks: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * User profile types
 */
export interface UserProfile {
  id: string
  email: string
  name: string
  photo_url?: string
  created_at: string
}

/**
 * Sync user profile with backend
 * This ensures the user exists in the backend database
 */
export async function syncUserProfile(token: string): Promise<UserProfile> {
  try {
    console.log('🔍 Syncing user profile to:', `${API_BASE_URL}/api/users/me`)
    const response = await fetch(`${API_BASE_URL}/api/users/me`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    })
    
    console.log('📡 Response status:', response.status)
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || 'Failed to sync user profile')
    }
    
    const data = await response.json()
    console.log('✅ User profile synced successfully')
    return data
  } catch (error) {
    console.error('❌ Sync error:', error)
    throw error
  }
}

// League types and functions
export interface League {
  id: string
  name: string
  description?: string
  is_global: boolean
  owner_id?: string
  created_at: string
  member_count?: number
}

export interface LeagueCreate {
  name: string
  description?: string
}

/**
 * Create a new league
 */
export async function createLeague(token: string, data: LeagueCreate): Promise<League> {
  const response = await fetch(`${API_BASE_URL}/api/leagues`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to create league')
  }
  
  return response.json()
}

/**
 * Get all leagues for the current user
 */
export async function fetchUserLeagues(token: string): Promise<League[]> {
  const response = await fetch(`${API_BASE_URL}/api/leagues`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch leagues')
  }
  
  return response.json()
}

/**
 * Delete a league (owner only)
 */
export async function deleteLeague(token: string, leagueId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/leagues/${leagueId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to delete league')
  }
}

/**
 * Kick a member from a league (owner only)
 */
export async function kickMember(token: string, leagueId: string, userId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/leagues/${leagueId}/members/${userId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to kick member')
  }
}

/**
 * Search for users by name or email
 */
export async function searchUsers(token: string, query: string): Promise<UserProfile[]> {
  const response = await fetch(`${API_BASE_URL}/api/users/search?q=${encodeURIComponent(query)}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to search users')
  }
  
  return response.json()
}

/**
 * Invite a user to a league (owner only)
 */
export async function inviteUserToLeague(token: string, leagueId: string, userId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/leagues/${leagueId}/invite/${userId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to invite user')
  }
}

/**
 * Fetch results for an event
 */
export async function fetchEventResults(eventId: string): Promise<Result[]> {
  const response = await fetch(`${API_BASE_URL}/results?event_id=${eventId}`, {
    headers: {
      'Content-Type': 'application/json',
    },
  })
  
  if (!response.ok) {
    throw new Error(`Failed to fetch results: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.results || []
}

/**
 * Fetch scores for user's picks
 */
export async function fetchPickScores(token: string, pickIds?: string[]): Promise<Score[]> {
  const params = new URLSearchParams()
  if (pickIds && pickIds.length > 0) {
    pickIds.forEach(id => params.append('pick_id', id))
  }
  
  const response = await fetch(
    `${API_BASE_URL}/scores?${params.toString()}`,
    {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    }
  )
  
  if (!response.ok) {
    throw new Error(`Failed to fetch scores: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.scores || []
}
