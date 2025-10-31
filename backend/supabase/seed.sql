-- Seed data for F1 Picks development environment
-- This file contains sample data for testing and development

-- Sample users (these would normally be created via Supabase Auth)
INSERT INTO users (id, email, name, photo_url) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'alice@example.com', 'Alice Johnson', 'https://example.com/alice.jpg'),
    ('550e8400-e29b-41d4-a716-446655440002', 'bob@example.com', 'Bob Smith', 'https://example.com/bob.jpg'),
    ('550e8400-e29b-41d4-a716-446655440003', 'charlie@example.com', 'Charlie Brown', NULL)
ON CONFLICT (id) DO NOTHING;

-- Add users to global league
INSERT INTO league_members (user_id, league_id)
SELECT u.id, l.id 
FROM users u, leagues l 
WHERE l.is_global = TRUE
ON CONFLICT (user_id, league_id) DO NOTHING;

-- Sample private league
INSERT INTO leagues (id, name, description, is_global) VALUES
    ('660e8400-e29b-41d4-a716-446655440001', 'Friends League', 'Private league for friends', FALSE)
ON CONFLICT (id) DO NOTHING;

-- Add some users to private league
INSERT INTO league_members (user_id, league_id) VALUES
    ('550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001'),
    ('550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001')
ON CONFLICT (user_id, league_id) DO NOTHING;

-- Sample F1 events for 2024 season (upcoming races)
INSERT INTO events (id, name, circuit_id, circuit_name, session_type, round_number, year, start_time, end_time, status) VALUES
    ('770e8400-e29b-41d4-a716-446655440001', 'Las Vegas Grand Prix - Qualifying', 'las_vegas', 'Las Vegas Street Circuit', 'qualifying', 22, 2024, '2024-11-23 06:00:00+00', '2024-11-23 07:00:00+00', 'scheduled'),
    ('770e8400-e29b-41d4-a716-446655440002', 'Las Vegas Grand Prix - Race', 'las_vegas', 'Las Vegas Street Circuit', 'race', 22, 2024, '2024-11-24 06:00:00+00', '2024-11-24 08:00:00+00', 'scheduled'),
    ('770e8400-e29b-41d4-a716-446655440003', 'Qatar Grand Prix - Qualifying', 'qatar', 'Lusail International Circuit', 'qualifying', 23, 2024, '2024-12-01 17:00:00+00', '2024-12-01 18:00:00+00', 'scheduled'),
    ('770e8400-e29b-41d4-a716-446655440004', 'Qatar Grand Prix - Race', 'qatar', 'Lusail International Circuit', 'race', 23, 2024, '2024-12-01 20:00:00+00', '2024-12-01 22:00:00+00', 'scheduled'),
    ('770e8400-e29b-41d4-a716-446655440005', 'Abu Dhabi Grand Prix - Qualifying', 'abu_dhabi', 'Yas Marina Circuit', 'qualifying', 24, 2024, '2024-12-08 14:00:00+00', '2024-12-08 15:00:00+00', 'scheduled'),
    ('770e8400-e29b-41d4-a716-446655440006', 'Abu Dhabi Grand Prix - Race', 'abu_dhabi', 'Yas Marina Circuit', 'race', 24, 2024, '2024-12-08 17:00:00+00', '2024-12-08 19:00:00+00', 'scheduled')
ON CONFLICT (id) DO NOTHING;

-- Sample picks for upcoming events
INSERT INTO picks (user_id, event_id, prop_type, prop_value, metadata) VALUES
    -- Alice's picks for Las Vegas GP Race
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'race_winner', 'Max Verstappen', '{"confidence": 0.8}'),
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'podium_p2', 'Charles Leclerc', '{"confidence": 0.6}'),
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'podium_p3', 'Lando Norris', '{"confidence": 0.7}'),
    
    -- Bob's picks for Las Vegas GP Race
    ('550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440002', 'race_winner', 'Charles Leclerc', '{"confidence": 0.9}'),
    ('550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440002', 'podium_p2', 'Max Verstappen', '{"confidence": 0.8}'),
    ('550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440002', 'fastest_lap', 'Max Verstappen', '{"confidence": 0.7}'),
    
    -- Charlie's picks for Qatar GP Race
    ('550e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440004', 'race_winner', 'Lando Norris', '{"confidence": 0.6}'),
    ('550e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440004', 'podium_p2', 'Oscar Piastri', '{"confidence": 0.5}')
ON CONFLICT (user_id, event_id, prop_type) DO NOTHING;

-- Sample completed event with results (for testing scoring)
INSERT INTO events (id, name, circuit_id, circuit_name, session_type, round_number, year, start_time, end_time, status) VALUES
    ('770e8400-e29b-41d4-a716-446655440007', 'Brazilian Grand Prix - Race', 'interlagos', 'Autódromo José Carlos Pace', 'race', 21, 2024, '2024-11-03 18:00:00+00', '2024-11-03 20:00:00+00', 'completed')
ON CONFLICT (id) DO NOTHING;

-- Sample results for completed event
INSERT INTO results (event_id, prop_type, actual_value, source, metadata) VALUES
    ('770e8400-e29b-41d4-a716-446655440007', 'race_winner', 'Max Verstappen', 'fastf1', '{"position": 1, "time": "2:06:54.430"}'),
    ('770e8400-e29b-41d4-a716-446655440007', 'podium_p2', 'Esteban Ocon', 'fastf1', '{"position": 2, "gap": "+19.477"}'),
    ('770e8400-e29b-41d4-a716-446655440007', 'podium_p3', 'Pierre Gasly', 'fastf1', '{"position": 3, "gap": "+22.532"}'),
    ('770e8400-e29b-41d4-a716-446655440007', 'fastest_lap', 'Max Verstappen', 'fastf1', '{"lap": 43, "time": "1:10.540"}')
ON CONFLICT (event_id, prop_type) DO NOTHING;

-- Sample picks for completed event
INSERT INTO picks (user_id, event_id, prop_type, prop_value, metadata) VALUES
    -- Alice's picks for Brazilian GP (some correct, some wrong)
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440007', 'race_winner', 'Max Verstappen', '{"confidence": 0.9}'),
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440007', 'podium_p2', 'Charles Leclerc', '{"confidence": 0.7}'),
    ('550e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440007', 'fastest_lap', 'Max Verstappen', '{"confidence": 0.8}'),
    
    -- Bob's picks for Brazilian GP
    ('550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440007', 'race_winner', 'Charles Leclerc', '{"confidence": 0.8}'),
    ('550e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440007', 'podium_p2', 'Esteban Ocon', '{"confidence": 0.4}')
ON CONFLICT (user_id, event_id, prop_type) DO NOTHING;

-- Sample scores for completed event picks
INSERT INTO scores (pick_id, user_id, points, margin, exact_match, metadata)
SELECT p.id, p.user_id,
    CASE 
        WHEN p.prop_value = r.actual_value THEN 10  -- Exact match
        ELSE 0  -- Wrong prediction
    END as points,
    0 as margin,
    (p.prop_value = r.actual_value) as exact_match,
    jsonb_build_object('predicted', p.prop_value, 'actual', r.actual_value) as metadata
FROM picks p
JOIN results r ON p.event_id = r.event_id AND p.prop_type = r.prop_type
WHERE p.event_id = '770e8400-e29b-41d4-a716-446655440007'
ON CONFLICT (pick_id) DO NOTHING;
