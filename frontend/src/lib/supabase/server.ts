/**
 * Supabase Client for Server-Side Usage
 * 
 * This client is used in server components, API routes, and middleware.
 * It properly handles cookies for authentication in server contexts.
 */

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

/**
 * Creates a Supabase client for server-side usage.
 * 
 * This client properly handles cookies in server contexts including:
 * - Server Components
 * - Server Actions
 * - Route Handlers
 * - Middleware
 * 
 * @returns Supabase client instance configured for server usage
 */
export async function createClient() {
  const cookieStore = await cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
}
