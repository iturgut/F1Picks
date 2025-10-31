-- Initial F1 Picks Database Schema
-- This migration creates all the core tables for the F1 prediction game

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types/enums
CREATE TYPE event_type AS ENUM (
    'practice_1',
    'practice_2', 
    'practice_3',
    'sprint_qualifying',
    'sprint',
    'qualifying',
    'race'
);

CREATE TYPE event_status AS ENUM (
    'scheduled',
    'live',
    'completed',
    'cancelled'
);

CREATE TYPE prop_type AS ENUM (
    'race_winner',
    'podium_p1',
    'podium_p2',
    'podium_p3',
    'fastest_lap',
    'pole_position',
    'first_retirement',
    'safety_car',
    'lap_time_prediction',
    'sector_time_prediction',
    'pit_window_start',
    'pit_window_end',
    'total_pit_stops'
);

CREATE TYPE result_source AS ENUM (
    'fastf1',
    'manual',
    'fia_timing'
);

CREATE TYPE entity_type AS ENUM (
    'user',
    'league',
    'event',
    'pick',
    'result',
    'score'
);

CREATE TYPE audit_action AS ENUM (
    'create',
    'update',
    'delete',
    'score_calculated',
    'score_overridden',
    'data_ingested'
);

-- Users table (extends Supabase auth.users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    photo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for users
CREATE INDEX idx_users_email ON users(email);

-- Leagues table
CREATE TABLE leagues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_global BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for leagues
CREATE INDEX idx_leagues_is_global ON leagues(is_global);

-- League members association table
CREATE TABLE league_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    league_id UUID NOT NULL REFERENCES leagues(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, league_id)
);

-- Events table (F1 sessions)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    circuit_id VARCHAR(50) NOT NULL,
    circuit_name VARCHAR(100) NOT NULL,
    session_type event_type NOT NULL,
    round_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status event_status DEFAULT 'scheduled' NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for events
CREATE INDEX idx_events_circuit_id ON events(circuit_id);
CREATE INDEX idx_events_session_type ON events(session_type);
CREATE INDEX idx_events_round_number ON events(round_number);
CREATE INDEX idx_events_year ON events(year);
CREATE INDEX idx_events_start_time ON events(start_time);
CREATE INDEX idx_events_status ON events(status);

-- Picks table (user predictions)
CREATE TABLE picks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    prop_type prop_type NOT NULL,
    prop_value TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, event_id, prop_type)
);

-- Create indexes for picks
CREATE INDEX idx_picks_prop_type ON picks(prop_type);
CREATE INDEX idx_picks_user_id ON picks(user_id);
CREATE INDEX idx_picks_event_id ON picks(event_id);

-- Results table (actual outcomes)
CREATE TABLE results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    prop_type prop_type NOT NULL,
    actual_value TEXT NOT NULL,
    metadata JSONB,
    source result_source DEFAULT 'fastf1' NOT NULL,
    source_reference VARCHAR(200),
    ingested_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(event_id, prop_type)
);

-- Create indexes for results
CREATE INDEX idx_results_prop_type ON results(prop_type);
CREATE INDEX idx_results_event_id ON results(event_id);

-- Scores table (calculated points)
CREATE TABLE scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pick_id UUID UNIQUE NOT NULL REFERENCES picks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER DEFAULT 0 NOT NULL,
    margin FLOAT,
    exact_match BOOLEAN DEFAULT FALSE NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for scores
CREATE INDEX idx_scores_user_id ON scores(user_id);
CREATE INDEX idx_scores_points ON scores(points);

-- Audit table (change tracking)
CREATE TABLE audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    action audit_action NOT NULL,
    metadata JSONB,
    performed_by UUID,
    performed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for audit
CREATE INDEX idx_audit_entity_type ON audit(entity_type);
CREATE INDEX idx_audit_entity_id ON audit(entity_id);
CREATE INDEX idx_audit_action ON audit(action);
CREATE INDEX idx_audit_performed_at ON audit(performed_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leagues_updated_at BEFORE UPDATE ON leagues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_picks_updated_at BEFORE UPDATE ON picks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_results_updated_at BEFORE UPDATE ON results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scores_updated_at BEFORE UPDATE ON scores FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert global league
INSERT INTO leagues (name, description, is_global) 
VALUES ('Global League', 'The main F1 Picks league for all users', TRUE);

-- RLS (Row Level Security) policies will be added in a separate migration
-- after Supabase Auth integration is complete
