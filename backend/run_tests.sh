#!/bin/bash

# F1 Picks Backend Test Runner
# Run all scoring tests

set -e

echo "=================================="
echo "F1 Picks Scoring System Tests"
echo "=================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Must be run from backend directory"
    exit 1
fi

# Check if pytest is installed
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov httpx
fi

echo "🧪 Running unit tests..."
echo ""
pytest tests/test_scoring_algorithms.py -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All unit tests passed!"
    echo ""
    echo "=================================="
    echo "Run integration test? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "🏁 Running integration test..."
        echo ""
        python -m scripts.test_scoring
    fi
else
    echo ""
    echo "❌ Unit tests failed"
    exit 1
fi
