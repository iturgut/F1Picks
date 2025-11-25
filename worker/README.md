# FastF1 Integration Worker

This worker service fetches and ingests Formula 1 data using the FastF1 library.

## Features

- **Season Schedule Ingestion**: Automatically fetches and stores the complete F1 season schedule
- **Results Polling**: Polls for race and qualifying results after sessions complete
- **Automatic Status Updates**: Updates event statuses (scheduled → live → completed)
- **Idempotent Operations**: Safe to retry without duplicating data
- **Structured Logging**: JSON or console logging for monitoring
- **Scheduler**: Periodic polling with configurable intervals

## Installation

```bash
cd worker
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the worker directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/f1picks
FASTF1_CACHE_DIR=./cache/fastf1
POLL_INTERVAL_MINUTES=30
LOG_LEVEL=INFO
LOG_FORMAT=console
ENABLE_SCHEDULER=true
```

## Usage

### CLI Commands

```bash
# Show configuration
python cli.py config

# Ingest season schedule
python cli.py ingest-schedule --year 2024

# Ingest results for a specific event
python cli.py ingest-results <event-id>

# Run the worker service
python cli.py run
```

### Running as a Service

```bash
# Start the worker
python -m app.main

# Or use the CLI
python cli.py run
```

The worker will:
1. Connect to the database
2. Start the scheduler
3. Poll for completed events every 30 minutes (configurable)
4. Update event statuses every 5 minutes
5. Ingest results when available

## Architecture

### Components

- **`fastf1_client.py`**: Wrapper around FastF1 library for fetching F1 data
- **`transformers.py`**: Converts FastF1 data to database schema
- **`ingestion.py`**: Handles database operations for storing data
- **`scheduler.py`**: APScheduler-based periodic task execution
- **`main.py`**: Main worker service entry point
- **`cli.py`**: Command-line interface for manual operations

### Data Flow

```
FastF1 API → FastF1Client → Transformer → IngestionService → Database
                ↓
            Scheduler (polls periodically)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Manual Testing

```bash
# Test schedule ingestion
python cli.py ingest-schedule --year 2024

# Check logs
tail -f logs/worker.log
```

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "app.main"]
```

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `FASTF1_CACHE_DIR`: Directory for FastF1 cache files
- `POLL_INTERVAL_MINUTES`: How often to poll for new data (default: 30)
- `POST_SESSION_DELAY_MINUTES`: Wait time after session ends (default: 30)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FORMAT`: Log format (json, console)
- `ENABLE_SCHEDULER`: Enable/disable automatic polling (default: true)

## Monitoring

The worker logs structured JSON (in production) or console output (in development) with:

- Event ingestion status
- Polling attempts and results
- Error conditions
- Performance metrics

## Troubleshooting

### FastF1 Data Not Available

FastF1 data typically becomes available 30-120 minutes after a session ends. The worker will automatically retry.

### Database Connection Issues

Check the `DATABASE_URL` environment variable and ensure PostgreSQL is running.

### Cache Issues

Clear the FastF1 cache if data seems stale:

```bash
rm -rf cache/fastf1/*
```

## License

Part of the F1 Picks application.
