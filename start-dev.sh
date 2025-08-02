#!/bin/bash

# Quick Development Start Script
# For when you've already set up the environment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if setup has been done
check_setup() {
    if [ ! -d "backend/venv" ]; then
        echo "❌ Backend virtual environment not found"
        echo "Please run './start.sh' first to set up the development environment"
        exit 1
    fi
    
    if [ ! -d "frontend/node_modules" ]; then
        echo "❌ Frontend dependencies not found"
        echo "Please run './start.sh' first to set up the development environment"
        exit 1
    fi
}

# Function to cleanup background processes
cleanup() {
    echo ""
    print_status "Shutting down services..."
    kill $(jobs -p) 2>/dev/null || true
    print_success "Cleanup completed"
    exit 0
}

# Set up signal trap
trap cleanup SIGINT SIGTERM

echo "🚀 Quick Start - Journaling Assistant"
echo "====================================="

check_setup

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    print_warning "Ollama is not running at localhost:11434"
    print_warning "Start Ollama in another terminal: ollama serve"
    echo ""
fi

print_status "Starting backend..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

print_status "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
print_success "🎉 Services started!"
echo "📱 Frontend: http://localhost:3000"
echo "📡 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID