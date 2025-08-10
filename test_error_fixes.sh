#!/bin/bash
# Backend Error Fix Test Script

echo "🔧 Applying backend error fixes..."

# Stop current server
echo "1. Stopping current backend server..."
pkill -f "python.*uvicorn.*app.main" || true
sleep 3

# Start server with better error logging
echo "2. Starting backend server with fixes..."
cd /home/abrasko/Projects/journaling-ai/backend
source ../venv/bin/activate

# Clear old log
> server.log

# Start server in background
nohup python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level debug > server.log 2>&1 &
SERVER_PID=$!

echo "3. Server started with PID: $SERVER_PID"
echo "4. Waiting 10 seconds for startup..."
sleep 10

# Check if server is running
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server failed to start"
    echo "Last 20 lines of server.log:"
    tail -n 20 server.log
    exit 1
fi

echo "5. Testing with a simple API call..."
cd /home/abrasko/Projects/journaling-ai

# Test basic API functionality
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health)
if [ "$response" = "200" ]; then
    echo "✅ API health check passed"
else
    echo "⚠️ API health check returned: $response"
fi

echo "6. Testing populate script with 1 entry..."
source venv/bin/activate
timeout 30 python populate_data.py --journal-entries 1 --chat-sessions 0 || echo "⚠️ Populate test timed out or failed"

echo "7. Checking recent errors in log..."
echo "Recent ERROR/CUDA/Exception messages:"
tail -n 50 backend/server.log | grep -E "ERROR|CUDA|Exception|Failed|assert" | tail -n 10

echo ""
echo "🎯 Error Fix Test Complete!"
echo "Check the log output above for any remaining issues."
echo "Server is running with PID: $SERVER_PID"
echo "To monitor logs: tail -f backend/server.log"
