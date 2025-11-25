# Supabase Authentication Setup Guide

This guide explains how to set up Supabase authentication for the F1Picks application.

## Backend Setup (Completed ✅)

The backend authentication middleware has been implemented with the following components:

### Files Created

1. **`app/auth.py`** - Authentication middleware
   - `verify_jwt_token()` - Validates Supabase JWT tokens
   - `get_current_user()` - FastAPI dependency for protected routes
   - `get_current_user_optional()` - Optional auth for public/private routes
   - `get_user_id_from_token()` - Extract user ID without DB lookup

2. **`app/routers/users.py`** - User management endpoints
   - `GET /api/users/me` - Get current user profile
   - `POST /api/users/me` - Create/update user profile (auto-joins global league)
   - `PUT /api/users/me` - Update user profile
   - `GET /api/users/{user_id}` - Get user by ID

3. **Updated `app/main.py`** - Registered user router

### Environment Variables Required

Add these to your `.env` file (see `backend/.env.example`):

```bash
# Supabase JWT Secret - Get from Supabase Dashboard
# Settings > API > JWT Settings > JWT Secret
SUPABASE_JWT_SECRET=your_jwt_secret_here

# Optional: For direct Supabase API calls
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

### Dependencies Added

- `pyjwt==2.10.1` - JWT token validation

Install with:
```bash
cd backend
pip install -r requirements.txt
```

### How It Works

1. **Frontend sends request** with `Authorization: Bearer <supabase_jwt_token>` header
2. **Backend middleware** (`get_current_user`) validates the JWT token
3. **User lookup** - Extracts user ID from token and fetches from database
4. **Protected routes** - Use `current_user: User = Depends(get_current_user)`

### Example Usage

```python
from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.name}!"}

@router.get("/optional-auth")
async def optional_route(user: Optional[User] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user.name}!"}
    return {"message": "Hello guest!"}
```

## Frontend Setup (TODO - Next Step)

The frontend needs the following components:

### 1. Supabase Client Configuration

Create `frontend/src/lib/supabase/client.ts`:
```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

### 2. Server-Side Supabase Client

Create `frontend/src/lib/supabase/server.ts`:
```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

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
          cookiesToSet.forEach(({ name, value, options }) =>
            cookieStore.set(name, value, options)
          )
        },
      },
    }
  )
}
```

### 3. Auth Context Provider

Create `frontend/src/contexts/AuthContext.tsx`:
```typescript
'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { User } from '@supabase/supabase-js'
import { createClient } from '@/lib/supabase/client'

interface AuthContextType {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const supabase = createClient()

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
  }

  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (error) throw error
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
  }

  return (
    <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### 4. Environment Variables

Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 5. Middleware for Protected Routes

Create `frontend/src/middleware.ts`:
```typescript
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value)
          )
          response = NextResponse.next({
            request,
          })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  await supabase.auth.getUser()

  return response
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
```

## Supabase Project Setup

### Local Development (Supabase CLI)

1. Install Supabase CLI:
```bash
npm install -g supabase
```

2. Initialize Supabase:
```bash
supabase init
```

3. Start local Supabase:
```bash
supabase start
```

4. Get credentials:
```bash
supabase status
```

Copy the `anon key` and `service_role key` to your `.env` files.

### Production (Supabase Cloud)

1. Create project at https://app.supabase.com
2. Go to Settings > API
3. Copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL`
   - `anon` public key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - JWT Secret → `SUPABASE_JWT_SECRET` (backend only)
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (backend only, NEVER expose to frontend)

4. Enable authentication providers:
   - Settings > Authentication > Providers
   - Enable Email/Password
   - Configure Google OAuth (optional)
   - Configure Apple Sign In (optional)

## Testing the Setup

### 1. Start the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Test authentication endpoint:
```bash
# This should return 401 Unauthorized
curl http://localhost:8000/api/users/me

# With valid token (get from Supabase):
curl -H "Authorization: Bearer <your_supabase_jwt_token>" \
     http://localhost:8000/api/users/me
```

### 3. Health check:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

## Next Steps

1. ✅ Backend auth middleware - COMPLETE
2. ⏳ Frontend Supabase client setup - IN PROGRESS
3. ⏳ Login/signup UI components
4. ⏳ Protected route implementation
5. ⏳ User profile sync on first login

## Troubleshooting

### "Token has expired"
- Supabase tokens expire after 1 hour
- Frontend should automatically refresh tokens using `supabase.auth.onAuthStateChange`

### "Invalid token"
- Check that `SUPABASE_JWT_SECRET` matches your Supabase project
- Verify token is being sent in `Authorization: Bearer <token>` header

### "User not found"
- User must call `POST /api/users/me` after Supabase signup to create DB record
- Frontend should automatically do this after successful authentication
