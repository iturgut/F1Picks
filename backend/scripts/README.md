# Backend Scripts

Utility scripts for testing and development.

## Available Scripts

### test_scoring.py

Complete integration test for the scoring system.

**Usage:**
```bash
cd backend
python -m scripts.test_scoring
```

**What it does:**
1. Creates a test user
2. Creates a completed test event
3. Creates 8 different prediction types
4. Creates corresponding results
5. Runs the scoring service
6. Displays detailed scores
7. Optionally cleans up test data

**Expected output:**
- Total points: 65
- 8 picks scored
- Detailed breakdown of each prediction

**Requirements:**
- Database must be running
- `.env` file must be configured
- Backend dependencies installed

### Future Scripts

Additional scripts to be added:
- `seed_dev_data.py` - Seed database with development data
- `migrate.py` - Run database migrations
- `create_test_picks.py` - Create bulk test predictions
- `benchmark_scoring.py` - Performance testing

## Running Tests

See [TESTING_SCORING.md](../TESTING_SCORING.md) for comprehensive testing guide.

### Quick Test

```bash
# Unit tests
pytest tests/test_scoring_algorithms.py -v

# Integration test
python -m scripts.test_scoring
```
