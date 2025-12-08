'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

interface UserProfile {
  id: string;
  email: string;
  name: string;
  photo_url: string | null;
  created_at: string;
}

interface UserStatistics {
  user_id: string;
  season: number;
  total_points: number;
  total_picks: number;
  scored_picks: number;
  exact_matches: number;
  hit_rate: number;
  average_points: number;
  average_margin: number;
  rank: number | null;
  total_users: number;
}

export default function ProfilePage() {
  const params = useParams();
  const userId = params.userId as string;
  const { user: currentUser } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [statistics, setStatistics] = useState<UserStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [season, setSeason] = useState(new Date().getFullYear());

  const isOwnProfile = currentUser && currentUser.id === userId;

  useEffect(() => {
    fetchProfileData();
  }, [userId, season]);

  const fetchProfileData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch user profile
      const profileResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${userId}`
      );

      if (!profileResponse.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const profileData = await profileResponse.json();
      setProfile(profileData);

      // Fetch user statistics
      const statsResponse = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${userId}/statistics?season=${season}`
      );

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatistics(statsData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">❌ {error || 'Profile not found'}</p>
          <Link
            href="/leaderboard"
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 inline-block"
          >
            Back to Leaderboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Back Button */}
        <Link
          href="/leaderboard"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Leaderboard
        </Link>

        {/* Profile Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center">
            <div className="flex-shrink-0 h-20 w-20 bg-gradient-to-br from-red-500 to-red-700 rounded-full flex items-center justify-center mr-6">
              {profile.photo_url ? (
                <img
                  src={profile.photo_url}
                  alt={profile.name}
                  className="h-20 w-20 rounded-full object-cover"
                />
              ) : (
                <span className="text-white text-3xl font-bold">
                  {profile.name.charAt(0).toUpperCase()}
                </span>
              )}
            </div>
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900">
                {profile.name}
                {isOwnProfile && (
                  <span className="ml-3 text-sm bg-red-100 text-red-800 px-3 py-1 rounded-full">
                    Your Profile
                  </span>
                )}
              </h1>
              <p className="text-gray-600 mt-1">
                Member since {new Date(profile.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Season Selector */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
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

        {/* Statistics */}
        {statistics ? (
          <>
            {/* Key Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  Total Points
                </div>
                <div className="text-3xl font-bold text-gray-900">
                  {statistics.total_points}
                </div>
                {statistics.rank && (
                  <div className="text-sm text-gray-600 mt-2">
                    Rank #{statistics.rank} of {statistics.total_users}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  Hit Rate
                </div>
                <div className="text-3xl font-bold text-gray-900">
                  {statistics.hit_rate.toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-2">
                  {statistics.exact_matches} exact matches
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm p-6">
                <div className="text-sm font-medium text-gray-500 mb-1">
                  Avg Points/Pick
                </div>
                <div className="text-3xl font-bold text-gray-900">
                  {statistics.average_points.toFixed(1)}
                </div>
                <div className="text-sm text-gray-600 mt-2">
                  {statistics.scored_picks} picks scored
                </div>
              </div>
            </div>

            {/* Detailed Stats */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Season {season} Statistics
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-gray-500">Total Picks</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {statistics.total_picks}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Scored Picks</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {statistics.scored_picks}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Exact Matches</div>
                  <div className="text-2xl font-bold text-green-600">
                    {statistics.exact_matches}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Avg Margin</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {statistics.average_margin.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>

            {/* Performance Indicator */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Performance Level
              </h2>
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-red-600 bg-red-200">
                      {statistics.hit_rate >= 50
                        ? '🏆 Expert'
                        : statistics.hit_rate >= 30
                        ? '⭐ Advanced'
                        : statistics.hit_rate >= 15
                        ? '📈 Intermediate'
                        : '🌱 Beginner'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold inline-block text-red-600">
                      {statistics.hit_rate.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-red-200">
                  <div
                    style={{ width: `${Math.min(statistics.hit_rate, 100)}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-red-600 transition-all duration-500"
                  ></div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-500">No statistics available for this season</p>
            <p className="text-sm text-gray-400 mt-2">
              Make some predictions to see your stats!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
