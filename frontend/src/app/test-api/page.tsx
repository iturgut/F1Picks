'use client';

import { useEffect, useState } from 'react';

export default function TestAPIPage() {
  const [apiUrl, setApiUrl] = useState('');
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [leaderboardData, setLeaderboardData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setApiUrl(process.env.NEXT_PUBLIC_API_URL || 'NOT SET');
    testAPI();
  }, []);

  const testAPI = async () => {
    try {
      setError(null);
      
      // Test 1: Health check
      console.log('Testing health endpoint...');
      const healthResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/health`);
      const healthData = await healthResponse.json();
      setHealthStatus(healthData);
      console.log('Health check:', healthData);

      // Test 2: Leaderboard
      console.log('Testing leaderboard endpoint...');
      const leaderboardResponse = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/scores/leaderboard/season/2025?limit=10`
      );
      const leaderboardResult = await leaderboardResponse.json();
      setLeaderboardData(leaderboardResult);
      console.log('Leaderboard:', leaderboardResult);
    } catch (err) {
      console.error('API Test Error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">API Connection Test</h1>

        <div className="space-y-4">
          {/* API URL */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-bold mb-2">API URL</h2>
            <code className="text-sm bg-gray-100 p-2 rounded block">
              {apiUrl}
            </code>
          </div>

          {/* Health Status */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-bold mb-2">Health Check</h2>
            {healthStatus ? (
              <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
                {JSON.stringify(healthStatus, null, 2)}
              </pre>
            ) : (
              <p className="text-gray-500">Loading...</p>
            )}
          </div>

          {/* Leaderboard Data */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="font-bold mb-2">Leaderboard Data</h2>
            {leaderboardData ? (
              <pre className="text-sm bg-gray-100 p-2 rounded overflow-auto">
                {JSON.stringify(leaderboardData, null, 2)}
              </pre>
            ) : (
              <p className="text-gray-500">Loading...</p>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
              <h2 className="font-bold text-red-800 mb-2">Error</h2>
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Retry Button */}
          <button
            onClick={testAPI}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry Tests
          </button>
        </div>
      </div>
    </div>
  );
}
