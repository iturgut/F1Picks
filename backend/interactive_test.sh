#!/bin/bash
# Interactive API Testing Script for F1Picks

set -e

API_URL="http://localhost:8000"
JWT_SECRET="test-secret-key-for-development-only"

echo "🏎️  F1Picks API Interactive Tester"
echo "=================================="
echo ""

# Check if server is running
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "❌ Error: API server is not running at $API_URL"
    echo "   Start it with: ./venv/bin/python -m uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ Server is running"
echo ""

# Generate test token
echo "📝 Generating test JWT token..."
TOKEN=$(./venv/bin/python3 -c "
import jwt
from datetime import datetime, timedelta
from uuid import uuid4

user_id = str(uuid4())
payload = {
    'sub': user_id,
    'email': 'test@example.com',
    'aud': 'authenticated',
    'role': 'authenticated',
    'iat': datetime.utcnow(),
    'exp': datetime.utcnow() + timedelta(hours=1),
}
token = jwt.encode(payload, '$JWT_SECRET', algorithm='HS256')
print(token)
print(f'USER_ID={user_id}', file=open('/tmp/f1picks_test_user.txt', 'w'))
")

USER_ID=$(grep USER_ID /tmp/f1picks_test_user.txt | cut -d= -f2)

echo "   User ID: $USER_ID"
echo "   Token: ${TOKEN:0:50}..."
echo ""

# Menu
while true; do
    echo "Choose a test:"
    echo "  1) Health Check"
    echo "  2) Database Health Check"
    echo "  3) Get User (without auth) - should fail"
    echo "  4) Get User (with auth) - will fail without DB"
    echo "  5) API Documentation (opens browser)"
    echo "  6) View Generated Token"
    echo "  7) Test with custom endpoint"
    echo "  0) Exit"
    echo ""
    read -p "Enter choice: " choice

    case $choice in
        1)
            echo ""
            echo "🔍 Testing: GET /health"
            curl -s "$API_URL/health" | python3 -m json.tool
            echo ""
            ;;
        2)
            echo ""
            echo "🔍 Testing: GET /health/db"
            curl -s "$API_URL/health/db" | python3 -m json.tool
            echo ""
            ;;
        3)
            echo ""
            echo "🔍 Testing: GET /api/users/me (no auth)"
            curl -s "$API_URL/api/users/me" | python3 -m json.tool
            echo ""
            ;;
        4)
            echo ""
            echo "🔍 Testing: GET /api/users/me (with auth)"
            curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/api/users/me"
            echo ""
            echo ""
            ;;
        5)
            echo ""
            echo "📖 Opening API documentation..."
            open "$API_URL/docs"
            ;;
        6)
            echo ""
            echo "🔑 Generated JWT Token:"
            echo "$TOKEN"
            echo ""
            echo "User ID: $USER_ID"
            echo ""
            echo "To use in curl:"
            echo "  curl -H \"Authorization: Bearer $TOKEN\" $API_URL/api/users/me"
            echo ""
            ;;
        7)
            echo ""
            read -p "Enter endpoint (e.g., /api/users/me): " endpoint
            read -p "Include auth header? (y/n): " use_auth
            
            if [ "$use_auth" = "y" ]; then
                echo "🔍 Testing: GET $endpoint (with auth)"
                curl -s -H "Authorization: Bearer $TOKEN" "$API_URL$endpoint" | python3 -m json.tool || echo ""
            else
                echo "🔍 Testing: GET $endpoint (no auth)"
                curl -s "$API_URL$endpoint" | python3 -m json.tool || echo ""
            fi
            echo ""
            ;;
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            ;;
    esac
    
    echo ""
    echo "---"
    echo ""
done
