#!/bin/bash

# Start Backend Only Script

set -e

echo "🚀 Starting Journaling Assistant Backend"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Please run './start.sh' first to set up the environment"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Warning: Ollama is not running at localhost:11434"
    echo "The AI features will not work without Ollama"
    echo "Start Ollama: ollama serve"
    echo ""
fi

cd backend
echo "📡 Activating virtual environment..."
source venv/bin/activate

echo "🌟 Starting backend server..."
echo "📍 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

python run.py