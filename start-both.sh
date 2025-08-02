#!/bin/bash

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    pkill -f "python run.py" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    echo "✅ Cleanup completed"
    exit 0
}

# Set up signal trap
trap cleanup SIGINT SIGTERM

echo "🌟 Starting Journaling Assistant - Full Stack"
echo "=============================================="

# Check prerequisites
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend virtual environment not found"
    echo "Please run './start.sh' first to set up the environment"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not found"
    echo "Please run './start.sh' first to set up the environment"
    exit 1
fi

# Start backend with proper environment activation
echo "🚀 Starting backend..."
cd backend
source venv/bin/activate

# Verify activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Check if uvicorn is available
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "⚠️  Installing missing dependencies..."
    pip install -r requirements.txt
fi

# Start backend in background
echo "📡 Starting backend server..."
python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    echo "Check the backend logs above for errors"
    exit 1
fi

# Test backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running and healthy!"
else
    echo "⚠️  Backend started but health check failed"
fi

# Start frontend
echo "🌐 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "🎉 Services started successfully!"
echo "================================="
echo "📱 Frontend: http://localhost:3000"
echo "📡 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "💡 Tips:"
echo "   - Frontend may take 30-60 seconds to compile"
echo "   - Backend AI features require Ollama to be running"
echo "   - Use Ctrl+C to stop both services"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
