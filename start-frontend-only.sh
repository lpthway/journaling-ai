#!/bin/bash

# Start Frontend Only Script

set -e

echo "🌐 Starting Journaling Assistant Frontend"
echo "========================================="

# Check if node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Node modules not found"
    echo "Please run './start.sh' first to set up the environment"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend is not running at localhost:8000"
    echo "Start the backend first: ./start-backend-only.sh"
    echo ""
fi

cd frontend
echo "📱 Starting frontend development server..."
echo "🌍 Frontend will be available at: http://localhost:3000"
echo "🔄 Hot reload is enabled for development"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

npm start