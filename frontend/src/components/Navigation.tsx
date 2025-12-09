'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

export default function Navigation() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  // Don't show navigation on auth pages
  if (pathname === '/login' || pathname === '/signup') {
    return null;
  }

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + '/');
  };

  const navLinkClass = (path: string) => `
    px-4 py-2 rounded-lg font-medium transition-colors
    ${
      isActive(path)
        ? 'bg-red-600 text-white'
        : 'text-gray-700 hover:bg-gray-100'
    }
  `;

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and main nav */}
          <div className="flex items-center space-x-8">
            <Link href="/" className="flex items-center">
              <span className="text-2xl font-bold text-red-600">🏎️ F1Picks</span>
            </Link>

            {user && (
              <div className="flex space-x-2">
                <Link href="/events" className={navLinkClass('/events')}>
                  Events
                </Link>
                <Link href="/my-picks" className={navLinkClass('/my-picks')}>
                  My Picks
                </Link>
                <Link href="/leaderboard" className={navLinkClass('/leaderboard')}>
                  Leaderboard
                </Link>
                <Link href="/leagues" className={navLinkClass('/leagues')}>
                  Leagues
                </Link>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link
                  href={`/profile/${user.id}`}
                  className="flex items-center space-x-2 text-gray-700 hover:text-gray-900"
                >
                  <div className="h-8 w-8 bg-gradient-to-br from-red-500 to-red-700 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-bold">
                      {user.email?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <span className="hidden md:inline font-medium">Profile</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="px-4 py-2 text-gray-700 hover:text-gray-900 font-medium"
                >
                  Login
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>

      </div>
    </nav>
  );
}
