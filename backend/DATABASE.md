# F1 Picks Database Schema

This document describes the database schema and setup for the F1 Picks application.

## Overview

The F1 Picks application uses PostgreSQL as its database, managed through Supabase. The schema supports:

- User management (integrated with Supabase Auth)
- League organization (global and private leagues)
- F1 event tracking (races, qualifying, practice sessions)
- User predictions (picks) for various F1 outcomes
- Result ingestion from FastF1 API
- Scoring system with audit trails

## Database Setup

### Local Development

1. **Start Supabase locally:**
   ```bash
   cd backend/supabase
   supabase start
   ```

2. **Apply migrations:**
   ```bash
   # Apply Supabase migrations
   supabase db reset
   
   # Or apply Alembic migrations
   cd backend
   source venv/bin/activate
   python -m alembic upgrade head
   ```

3. **Seed development data:**
   ```bash
   supabase db reset --with-seed
   ```

### Production Setup

Production uses Supabase cloud instance. Migrations are applied automatically via CI/CD.

## Schema Overview

### Core Tables

#### `users`
- Stores user profile information
- Links to Supabase Auth via UUID
- Fields: id, email, name, photo_url, timestamps

#### `leagues`
- Competition groups for users
- Global league auto-created for all users
- Fields: id, name, description, is_global, timestamps

#### `league_members`
- Many-to-many relationship between users and leagues
- Fields: id, user_id, league_id, joined_at

#### `events`
- F1 sessions (practice, qualifying, race)
- Fields: id, name, circuit info, session_type, timing, status

#### `picks`
- User predictions for events
- Flexible prop_type system for different prediction types
- Fields: id, user_id, event_id, prop_type, prop_value, metadata

#### `results`
- Actual outcomes ingested from FastF1
- Fields: id, event_id, prop_type, actual_value, source info

#### `scores`
- Calculated points for user predictions
- Fields: id, pick_id, user_id, points, margin, exact_match

#### `audit`
- Change tracking for all operations
- Fields: id, entity_type, entity_id, action, metadata, performed_by

### Enums

- `event_type`: practice_1, practice_2, practice_3, sprint_qualifying, sprint, qualifying, race
- `event_status`: scheduled, live, completed, cancelled
- `prop_type`: race_winner, podium_p1, podium_p2, podium_p3, fastest_lap, etc.
- `result_source`: fastf1, manual, fia_timing
- `entity_type`: user, league, event, pick, result, score
- `audit_action`: create, update, delete, score_calculated, etc.

## Key Features

### Prediction Types (`prop_type`)

The system supports various prediction types:

- **Position predictions**: race_winner, podium_p1, podium_p2, podium_p3, pole_position
- **Performance predictions**: fastest_lap, first_retirement
- **Race events**: safety_car, total_pit_stops
- **Timing predictions**: lap_time_prediction, sector_time_prediction
- **Strategy predictions**: pit_window_start, pit_window_end

### Scoring System

- **Exact matches**: 10 points
- **Near matches**: 1-5 points based on margin
- **Time-based predictions**: Points based on percentage accuracy
- **Audit trail**: All scoring operations logged

### Supabase Integration

- **Authentication**: Uses Supabase Auth for user management
- **Real-time**: Supabase real-time for live updates
- **Row Level Security**: Will be implemented for data access control
- **Storage**: Profile photos stored in Supabase Storage

## Migration Strategy

### Dual Migration System

We use both Alembic and Supabase migrations:

- **Alembic**: For SQLAlchemy model changes and local development
- **Supabase**: For production deployments and Supabase-specific features

### Migration Files

- `alembic/versions/`: SQLAlchemy-generated migrations
- `supabase/migrations/`: Hand-written SQL migrations for Supabase
- `supabase/seed.sql`: Development seed data

## Development Workflow

1. **Make model changes** in `app/models/`
2. **Generate Alembic migration**: `python scripts/migrate.py generate "description"`
3. **Create corresponding Supabase migration** in `supabase/migrations/`
4. **Test locally** with `python scripts/migrate.py upgrade`
5. **Deploy** via CI/CD pipeline

### Migration Helper Scripts

Use the provided helper scripts for easier migration management:

```bash
# Check current migration status
python scripts/migrate.py status

# Upgrade to latest migration
python scripts/migrate.py upgrade

# Generate new migration from model changes
python scripts/migrate.py generate "Add new field to User model"

# Downgrade one migration
python scripts/migrate.py downgrade

# Reset database (careful - deletes all data!)
python scripts/migrate.py reset

# Show migration history
python scripts/migrate.py history

# Check if migrations are up to date
python scripts/migrate.py check

# Seed development data
python scripts/seed_dev_data.py
```

## Environment Variables

```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres

# Production (Supabase cloud)
DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:[port]/[database]

# Supabase configuration
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

## Performance Considerations

### Indexes

All frequently queried columns have indexes:
- User email (unique)
- Event timing and status
- Pick and result prop_types
- Audit timestamps and entity references

### Query Optimization

- Use async SQLAlchemy for non-blocking database operations
- Connection pooling configured for serverless environments
- JSONB columns for flexible metadata storage

### Scaling

- Supabase handles connection pooling and read replicas
- Audit table partitioning may be needed for high volume
- Consider materialized views for complex leaderboard queries

## Security

### Row Level Security (RLS)

Will be implemented for:
- Users can only see their own data
- League members can only see league-specific data
- Public data (events, results) accessible to all authenticated users

### Data Privacy

- User emails stored securely
- Audit logs track all data changes
- Soft deletes for user data retention compliance
