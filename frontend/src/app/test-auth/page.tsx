'use client'

/**
 * Test page for Supabase Authentication
 * 
 * This page demonstrates the auth functionality and can be used
 * to verify that Supabase integration is working correctly.
 */

import { useAuth } from '@/contexts/AuthContext'
import { useState } from 'react'

export default function TestAuthPage() {
  const { user, loading, signIn, signUp, signOut, signInWithGoogle } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    try {
      await signIn(email, password)
      setSuccess('Signed in successfully!')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    try {
      await signUp(email, password)
      setSuccess('Signed up successfully! Check your email for confirmation.')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleSignOut = async () => {
    setError(null)
    setSuccess(null)
    try {
      await signOut()
      setSuccess('Signed out successfully!')
    } catch (err) {
      setError((err as Error).message)
    }
  }

  const handleGoogleSignIn = async () => {
    setError(null)
    setSuccess(null)
    try {
      await signInWithGoogle()
    } catch (err) {
      setError((err as Error).message)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-md mx-auto">
        <h1 className="text-3xl font-bold mb-8">Auth Test Page</h1>

        {/* User Status */}
        <div className="mb-8 p-4 bg-gray-100 rounded">
          <h2 className="font-bold mb-2">Current User:</h2>
          {user ? (
            <div>
              <p className="text-sm">ID: {user.id}</p>
              <p className="text-sm">Email: {user.email}</p>
              <p className="text-sm">Created: {new Date(user.created_at).toLocaleString()}</p>
              <button
                onClick={handleSignOut}
                className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-600">Not signed in</p>
          )}
        </div>

        {/* Messages */}
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            {success}
          </div>
        )}

        {/* Auth Forms */}
        {!user && (
          <div className="space-y-6">
            <form onSubmit={handleSignIn} className="space-y-4">
              <h2 className="text-xl font-bold">Sign In</h2>
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 border rounded"
                required
              />
              <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Sign In
              </button>
            </form>

            <form onSubmit={handleSignUp} className="space-y-4">
              <h2 className="text-xl font-bold">Sign Up</h2>
              <button
                type="submit"
                className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                Sign Up (use email/password above)
              </button>
            </form>

            <div className="space-y-4">
              <h2 className="text-xl font-bold">Social Login</h2>
              <button
                onClick={handleGoogleSignIn}
                className="w-full px-4 py-2 bg-white border border-gray-300 rounded hover:bg-gray-50 flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign in with Google
              </button>
            </div>
          </div>
        )}

        {/* Environment Info */}
        <div className="mt-8 p-4 bg-gray-100 rounded text-xs">
          <h3 className="font-bold mb-2">Environment:</h3>
          <p>Supabase URL: {process.env.NEXT_PUBLIC_SUPABASE_URL?.substring(0, 30)}...</p>
          <p>Anon Key: {process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.substring(0, 30)}...</p>
        </div>
      </div>
    </div>
  )
}
