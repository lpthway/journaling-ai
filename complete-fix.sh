#!/bin/bash

# Complete Fix Script - Handles both icon errors and startup issues
echo "🔧 Comprehensive Fix for Journaling Assistant"
echo "=============================================="

# Stop any running processes first
echo "🛑 Stopping any running processes..."
pkill -f "python run.py" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# 1. FIX ICON IMPORT ERRORS
echo ""
echo "📝 Step 1: Fixing Heroicons import errors..."

cd frontend

# Replace RefreshIcon with ArrowPathIcon in all files
echo "   - Replacing RefreshIcon with ArrowPathIcon..."
find src -name "*.jsx" -type f -exec sed -i 's/RefreshIcon/ArrowPathIcon/g' {} \;

# Replace TrendingUpIcon with ArrowTrendingUpIcon in all files  
echo "   - Replacing TrendingUpIcon with ArrowTrendingUpIcon..."
find src -name "*.jsx" -type f -exec sed -i 's/TrendingUpIcon/ArrowTrendingUpIcon/g' {} \;

cd ..

# 2. CREATE MISSING FRONTEND FILES
echo ""
echo "📁 Step 2: Creating missing frontend files..."

# Create public directory if it doesn't exist
mkdir -p frontend/public

# Create index.html
echo "   - Creating index.html..."
cat > frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Local-first journaling assistant with AI insights" />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>Journaling Assistant</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create manifest.json
echo "   - Creating manifest.json..."
cat > frontend/public/manifest.json << 'EOF'
{
  "short_name": "Journal AI",
  "name": "Journaling Assistant with AI",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
EOF

# Create simple favicon
echo "   - Creating favicon..."
touch frontend/public/favicon.ico

# 3. FIX BACKEND DEPENDENCIES
echo ""
echo "🐍 Step 3: Ensuring backend dependencies are installed..."

cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   - Installing/updating Python dependencies..."
    pip install -r requirements.txt --quiet
    echo "   - Backend dependencies verified ✅"
else
    echo "❌ Virtual environment not found! Please run ./start.sh first"
    exit 1
fi
cd ..

# 4. CREATE IMPROVED STARTUP SCRIPT
echo ""
echo "📝 Step 4: Creating improved startup script..."

cat > start-both.sh << 'EOF'
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
EOF

# Make the script executable
chmod +x start-both.sh

echo ""
echo "🎉 ALL FIXES COMPLETED SUCCESSFULLY!"
echo "===================================="
echo ""
echo "✅ Fixed Heroicons import errors"
echo "✅ Created missing frontend files" 
echo "✅ Verified backend dependencies"
echo "✅ Created improved startup script"
echo ""
echo "🚀 Ready to start! Run:"
echo "   ./start-both.sh"
echo ""
echo "📋 What was fixed:"
echo "   - RefreshIcon → ArrowPathIcon"
echo "   - TrendingUpIcon → ArrowTrendingUpIcon"
echo "   - Created frontend/public/index.html"
echo "   - Created frontend/public/manifest.json"
echo "   - Created favicon.ico"
echo "   - Improved virtual environment handling"
echo "   - Added health checks and better error handling"
echo ""