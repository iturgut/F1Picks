/**
 * Environment variable validation and defaults
 */

export const env = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
}

// Validate required environment variables (only in browser/runtime, not during build)
if (typeof window !== 'undefined') {
  const requiredEnvVars = [
    'NEXT_PUBLIC_SUPABASE_URL',
    'NEXT_PUBLIC_SUPABASE_ANON_KEY',
  ] as const

  for (const envVar of requiredEnvVars) {
    if (!env[envVar]) {
      console.error(`Missing required environment variable: ${envVar}`)
    }
  }
}
