'use client'

/**
 * Authentication Context Provider
 * 
 * Manages authentication state and provides auth methods throughout the app.
 * Automatically syncs with Supabase auth state changes.
 */

import { createContext, useContext, useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthContextType {
  user: User | null
  loading: boolean
  getAccessToken: () => Promise<string | null>
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, metadata?: { name?: string }) => Promise<void>
  signInWithGoogle: () => Promise<void>
  signInWithApple: () => Promise<void>
  signOut: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [supabase] = useState(() => createClient())

  useEffect(() => {
    console.log('🚀 AuthProvider initializing...')
    
    // Set a timeout to prevent infinite loading
    const timeout = setTimeout(() => {
      console.warn('⏱️ Auth initialization timeout - setting loading to false')
      setLoading(false)
    }, 5000) // 5 second timeout

    // Get initial session
    supabase.auth.getSession()
      .then(async ({ data: { session }, error }) => {
        console.log('📡 Session check complete:', { 
          hasSession: !!session, 
          hasError: !!error,
          user: session?.user?.email 
        })
        
        if (error) {
          console.error('❌ Error getting session:', error)
        }
        setUser(session?.user ?? null)
        clearTimeout(timeout)
        setLoading(false)
        
        // Sync user profile with backend if authenticated (non-blocking, client-side only)
        if (session?.access_token && typeof window !== 'undefined') {
          try {
            const { syncUserProfile } = await import('@/lib/api')
            await syncUserProfile(session.access_token)
          } catch (error) {
            console.error('Failed to sync user profile:', error)
          }
        }
      })
      .catch((error) => {
        console.error('💥 Fatal error in auth initialization:', error)
        clearTimeout(timeout)
        setLoading(false)
      })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      console.log('🔄 Auth state changed:', _event)
      setUser(session?.user ?? null)
      
      // Sync user profile with backend if authenticated (client-side only)
      if (session?.access_token && typeof window !== 'undefined') {
        try {
          const { syncUserProfile } = await import('@/lib/api')
          await syncUserProfile(session.access_token)
        } catch (error) {
          console.error('Failed to sync user profile:', error)
        }
      }
    })

    return () => {
      console.log('🧹 AuthProvider cleanup')
      clearTimeout(timeout)
      subscription.unsubscribe()
    }
  }, [])

  const getAccessToken = async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token ?? null
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
  }

  const signUp = async (
    email: string,
    password: string,
    metadata?: { name?: string }
  ) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: metadata,
      },
    })
    if (error) throw error
  }

  const signInWithGoogle = async () => {
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${siteUrl}/auth/callback`,
      },
    })
    if (error) throw error
  }

  const signInWithApple = async () => {
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'apple',
      options: {
        redirectTo: `${siteUrl}/auth/callback`,
      },
    })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  const resetPassword = async (email: string) => {
    const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || window.location.origin
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${siteUrl}/auth/reset-password`,
    })
    if (error) throw error
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        getAccessToken,
        signIn,
        signUp,
        signInWithGoogle,
        signInWithApple,
        signOut,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access auth context
 * 
 * @throws Error if used outside AuthProvider
 * @returns Auth context with user state and auth methods
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/**
 * Hook to get current user
 * 
 * Convenience hook that returns just the user object
 * 
 * @returns Current user or null
 */
export function useUser() {
  const { user } = useAuth()
  return user
}
