#!/bin/bash

echo "🌐 Starting Journaling Assistant Frontend"
echo "========================================"

cd frontend

if [ ! -d "node_modules" ]; then
    echo "❌ Frontend dependencies not installed"
    echo "Run: npm install"
    exit 1
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend not running - start it first:"
    echo "   ./start-backend.sh"
    echo ""
fi

echo "📱 Starting frontend server..."
echo "🌍 Frontend: http://localhost:3000"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

npm start
