'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  username: string;
  total_points: number;
  events_scored: number;
  average_points: number;
}

export default function LeaderboardPage() {
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [season, setSeason] = useState(new Date().getFullYear());
  const [timeFrame, setTimeFrame] = useState<'current' | 'season' | 'all-time'>('season');

  useEffect(() => {
    fetchLeaderboard();
  }, [season, timeFrame]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      setError(null);

      // For now, we'll use season leaderboard
      // TODO: Add support for all-time and current event leaderboards
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/scores/leaderboard/season/${season}?limit=50`,
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }

      const data = await response.json();
      setLeaderboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-gray-400';
    if (rank === 3) return 'text-amber-600';
    return 'text-gray-700';
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">❌ {error}</p>
          <button
            onClick={fetchLeaderboard}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🏆 Leaderboard</h1>
          <p className="text-gray-600">See how you stack up against other F1 prediction experts</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Season
              </label>
              <select
                value={season}
                onChange={(e) => setSeason(Number(e.target.value))}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              >
                <option value={2025}>2025</option>
                <option value={2024}>2024</option>
                <option value={2023}>2023</option>
              </select>
            </div>

            {/* Time frame selector (for future use) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Time Frame
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setTimeFrame('season')}
                  className={`px-4 py-2 rounded-lg font-medium ${
                    timeFrame === 'season'
                      ? 'bg-red-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Season
                </button>
                <button
                  onClick={() => setTimeFrame('all-time')}
                  disabled
                  className="px-4 py-2 rounded-lg font-medium bg-gray-100 text-gray-400 cursor-not-allowed"
                  title="Coming soon"
                >
                  All-Time
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Leaderboard Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          {leaderboard.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p className="text-lg mb-2">No scores yet for this season</p>
              <p className="text-sm">Be the first to make predictions!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total Points
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Events
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Points
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaderboard.map((entry) => {
                    const isCurrentUser = user && entry.user_id === user.id;
                    return (
                      <tr
                        key={entry.user_id}
                        className={`hover:bg-gray-50 transition-colors ${
                          isCurrentUser ? 'bg-red-50' : ''
                        }`}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`text-2xl font-bold ${getRankColor(entry.rank)}`}
                          >
                            {getRankBadge(entry.rank)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <Link
                            href={`/profile/${entry.user_id}`}
                            className="flex items-center hover:text-red-600"
                          >
                            <div className="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center mr-3">
                              <span className="text-gray-600 font-medium">
                                {entry.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {entry.username}
                                {isCurrentUser && (
                                  <span className="ml-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                                    You
                                  </span>
                                )}
                              </div>
                            </div>
                          </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <span className="text-lg font-bold text-gray-900">
                            {entry.total_points}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                          {entry.events_scored}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                          {entry.average_points.toFixed(1)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer Info */}
        {leaderboard.length > 0 && (
          <div className="mt-6 text-center text-sm text-gray-500">
            <p>Showing top {leaderboard.length} users for {season} season</p>
          </div>
        )}
      </div>
    </div>
  );
}
