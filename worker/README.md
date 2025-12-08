# FastF1 Integration Worker

This worker service fetches and ingests Formula 1 data using the FastF1 library.

## Features

- **Season Schedule Ingestion**: Automatically fetches and stores the complete F1 season schedule
- **Results Polling**: Polls for race and qualifying results after sessions complete
- **Automatic Status Updates**: Updates event statuses (scheduled → live → completed)
- **Idempotent Operations**: Safe to retry without duplicating data
- **Structured Logging**: JSON or console logging for monitoring
- **GitHub Actions Integration**: Automated twice-daily syncing

## Quick Start

### Local Development

```bash
cd worker
uv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
uv pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the worker directory:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
FASTF1_CACHE_DIR=./cache/fastf1
LOG_LEVEL=INFO
```

### Run Data Ingestion

```bash
# Ingest everything (schedule + results)
python ingest_all.py

# Only fetch new results (skip schedule)
python ingest_all.py --skip-schedule

# Only update schedule (skip results)
python ingest_all.py --skip-results

# Ingest specific year
python ingest_all.py --year 2024
```

## Automated Syncing

### GitHub Actions

The workflow automatically runs twice daily at 6 AM and 6 PM UTC.

**Setup:**
1. Add `DATABASE_URL` to GitHub Secrets
2. Push to GitHub
3. Done! Automatic syncing is enabled

**Manual trigger:**
1. Go to Actions → "F1 Data Sync"
2. Click "Run workflow"
3. Configure options if needed

## Architecture

### Components

- **`ingest_all.py`**: Master ingestion script (schedule + results)
- **`app/fastf1_client.py`**: Wrapper around FastF1 library
- **`app/transformers.py`**: Converts FastF1 data to database schema
- **`app/ingestion.py`**: Handles database operations
- **`app/models.py`**: Database models (Event, Result, etc.)

### Data Flow

```
FastF1 API → FastF1Client → Transformer → IngestionService → Database
```

### What Gets Ingested

**Events:**
- ✅ Qualifying sessions
- ✅ Race sessions
- ✅ Sprint sessions
- ❌ Practice sessions (skipped)

**Results:**
- Race: Winner (P1), P2, P3
- Qualifying: Pole position (P1)

## Development

### Testing Locally

```bash
# Run ingestion
python ingest_all.py

# Check what was ingested
python -c "from app.database import *; import asyncio; asyncio.run(init_db())"
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)
  ```
  postgresql+asyncpg://user:password@host:port/database
  ```
- `FASTF1_CACHE_DIR`: Directory for FastF1 cache files (default: `./cache/fastf1`)
- `LOG_LEVEL`: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)

## Troubleshooting

### No Results Found

**Cause:** FastF1 data typically becomes available 30-120 minutes after a session ends.

**Solution:** Wait and run again, or let GitHub Actions handle it automatically.

### Database Connection Errors

**Cause:** Incorrect `DATABASE_URL` or network issues.

**Solution:**
1. Verify `DATABASE_URL` in `.env`
2. Ensure database is accessible
3. Use `postgresql+asyncpg://` prefix (not `postgresql://`)

### Enum Type Errors

**Cause:** Worker models don't match backend schema.

**Solution:** Ensure `app/models.py` enums match backend exactly.

## Performance

- **Schedule ingestion:** ~5-10 seconds for full season
- **Results ingestion:** ~30-60 seconds per event (FastF1 download time)
- **Total for 20 events:** ~15-20 minutes

## License

Part of the F1 Picks application.
