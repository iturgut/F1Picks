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
  const response = await fetch(`${API_BASE_URL}/api/users/me`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to sync user profile')
  }
  
  return response.json()
}
