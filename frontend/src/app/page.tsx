'use client'

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

export default function Home() {
  const { user, loading, signOut } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-red-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">🏎️</span>
              <h1 className="text-2xl font-bold text-gray-900">F1 Picks</h1>
            </div>
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  <span className="text-sm text-gray-600">{user.email}</span>
                  <button
                    onClick={() => signOut()}
                    className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
                  >
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="rounded-md px-4 py-2 text-sm font-semibold text-gray-900 hover:bg-gray-100"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            Formula 1 Prediction Game
          </h2>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Make predictions for F1 races and compete with friends.
            Test your knowledge of Formula 1 and climb the leaderboard!
          </p>
          
          {user ? (
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/events"
                className="rounded-md bg-red-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
              >
                View Events
              </Link>
              <Link
                href="/leaderboard"
                className="text-base font-semibold leading-7 text-gray-900 hover:text-gray-700"
              >
                Leaderboard <span aria-hidden="true">→</span>
              </Link>
            </div>
          ) : (
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/signup"
                className="rounded-md bg-red-600 px-6 py-3 text-base font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
              >
                Get Started
              </Link>
              <Link
                href="/login"
                className="text-base font-semibold leading-7 text-gray-900 hover:text-gray-700"
              >
                Sign In <span aria-hidden="true">→</span>
              </Link>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
          <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
            <div className="flex flex-col">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                🏁 Make Predictions
              </dt>
              <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                <p className="flex-auto">Predict race winners, podium finishes, fastest laps, and more before each session.</p>
              </dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                📊 Track Your Score
              </dt>
              <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                <p className="flex-auto">Earn points based on accuracy and compete on the global leaderboard.</p>
              </dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-base font-semibold leading-7 text-gray-900">
                👥 Join Leagues
              </dt>
              <dd className="mt-1 flex flex-auto flex-col text-base leading-7 text-gray-600">
                <p className="flex-auto">Create private leagues with friends or join the global competition.</p>
              </dd>
            </div>
          </dl>
        </div>
      </main>
    </div>
  );
}
