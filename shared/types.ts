// Shared types for F1 Picks application

export interface User {
  id: string;
  email: string;
  name: string;
  photo_url?: string;
  created_at: Date;
}

export interface League {
  id: string;
  name: string;
  description?: string;
  is_global: boolean;
  created_at: Date;
}

export interface Event {
  id: string;
  name: string;
  circuit_id: string;
  start_time: Date;
  end_time: Date;
  type: 'race' | 'qualifying' | 'practice';
  status: 'upcoming' | 'live' | 'completed';
}

export interface Pick {
  id: string;
  user_id: string;
  event_id: string;
  prop_type: string;
  prop_value: string;
  created_at: Date;
}

export interface Score {
  id: string;
  pick_id: string;
  points: number;
  margin?: number;
  created_at: Date;
}

export interface LeaderboardEntry {
  user_id: string;
  user_name: string;
  total_points: number;
  total_picks: number;
  hit_rate: number;
  average_margin: number;
  rank: number;
}
