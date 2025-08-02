#!/bin/bash

cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    pkill -f "python run.py" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    echo "✅ Services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "🌟 Starting Journaling Assistant"
echo "================================"

# Check prerequisites
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend environment not set up"
    exit 1
fi

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed"
    exit 1
fi

# Start backend
echo "🚀 Starting backend..."
cd backend
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Virtual environment activation failed"
    exit 1
fi

python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "⏳ Waiting for backend to start..."
sleep 8

# Check backend health
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend running and healthy"
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
echo "📡 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
if [ "$AI_WORKING" != true ]; then
    echo "💡 AI features limited. For full functionality:"
    echo "   ollama serve"
    echo "   ollama pull llama3.2"
    echo ""
fi
echo "🛑 Press Ctrl+C to stop both services"
echo ""

wait $BACKEND_PID $FRONTEND_PID
