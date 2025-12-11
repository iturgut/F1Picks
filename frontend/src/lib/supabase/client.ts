/**
 * Supabase Client for Browser/Client-Side Usage
 * 
 * This client is used in client components and browser contexts.
 * It handles authentication state and provides access to Supabase services.
 */

import { createBrowserClient } from '@supabase/ssr'
import { env } from '@/lib/env'

/**
 * Creates a Supabase client for browser usage.
 * 
 * This client automatically manages cookies and session state.
 * Use this in client components (components with 'use client' directive).
 * 
 * @returns Supabase client instance
 */
export function createClient() {
  if (typeof window !== 'undefined') {
    console.log('🔧 Creating Supabase client with:', {
      url: env.NEXT_PUBLIC_SUPABASE_URL ? 'Set' : 'Missing',
      key: env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Missing'
    })
  }
  
  return createBrowserClient(
    env.NEXT_PUBLIC_SUPABASE_URL,
    env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  )
}
