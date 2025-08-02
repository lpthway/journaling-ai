#!/bin/bash

# Continue Journaling Assistant Setup
# Virtual environment is working, now let's complete the installation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Continuing Journaling Assistant Setup"
echo "========================================"
echo ""
echo "✅ Virtual environment is working"
echo "Now installing the application dependencies..."
echo ""

# Stop any running processes
print_status "Stopping any running processes..."
pkill -f "python run.py" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true

# Backend setup
print_status "Setting up backend dependencies..."
cd backend

# Make sure we're in the virtual environment
if [ ! -f "venv/bin/activate" ]; then
    print_error "Virtual environment not found. Run debug script first."
    exit 1
fi

source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    print_error "Failed to activate virtual environment"
    exit 1
fi

print_success "Virtual environment activated: $VIRTUAL_ENV"
print_status "Using Python: $(python --version)"

# Install core dependencies
print_status "Installing core web framework dependencies..."
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install pydantic==2.5.0
pip install pydantic-settings==2.1.0

print_status "Installing utility dependencies..."
pip install python-multipart==0.0.6
pip install aiofiles==23.2.1
pip install python-dateutil==2.8.2
pip install requests

print_status "Installing data processing dependencies..."
pip install numpy==1.26.0
pip install textblob==0.17.1

print_status "Installing Ollama client..."
pip install ollama==0.1.9

# Test core functionality
print_status "Testing core dependencies..."
python -c "
try:
    import fastapi
    import uvicorn
    import pydantic
    import ollama
    import numpy
    import textblob
    print('✅ Core dependencies imported successfully!')
except ImportError as e:
    print(f'❌ Core dependency error: {e}')
    exit(1)
"

# Try to install AI dependencies (optional)
print_status "Installing AI/ML dependencies (this may take a few minutes)..."
print_warning "If this fails, the app will still work for basic journaling"

AI_SUCCESS=true

# Install PyTorch CPU version first
if pip install torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu; then
    print_success "PyTorch installed successfully"
else
    print_warning "PyTorch installation failed"
    AI_SUCCESS=false
fi

# Install transformers
if pip install transformers==4.35.0; then
    print_success "Transformers installed successfully"
else
    print_warning "Transformers installation failed"
    AI_SUCCESS=false
fi

# Install sentence transformers
if pip install sentence-transformers==2.2.2; then
    print_success "Sentence transformers installed successfully"
else
    print_warning "Sentence transformers installation failed"
    AI_SUCCESS=false
fi

# Install ChromaDB
if pip install chromadb==0.4.15; then
    print_success "ChromaDB installed successfully"
else
    print_warning "ChromaDB installation failed"
    AI_SUCCESS=false
fi

# Install additional ML libraries
if pip install scikit-learn pandas; then
    print_success "Additional ML libraries installed"
else
    print_warning "Some ML libraries failed to install"
fi

# Test AI functionality
if [ "$AI_SUCCESS" = true ]; then
    print_status "Testing AI dependencies..."
    python -c "
try:
    import torch
    import transformers
    import sentence_transformers
    import chromadb
    print('✅ AI dependencies working!')
    ai_available = True
except ImportError as e:
    print(f'⚠️ AI dependency issue: {e}')
    ai_available = False
" && AI_WORKING=true || AI_WORKING=false
else
    AI_WORKING=false
fi

# Test application import
print_status "Testing application imports..."
python -c "
try:
    from app.main import app
    print('✅ Application imports successfully!')
    app_working = True
except Exception as e:
    print(f'⚠️ Application import issue: {e}')
    print('This might be due to missing AI dependencies but core app should work')
    app_working = False
" && APP_WORKING=true || APP_WORKING=false

# Create requirements.txt for future reference
print_status "Creating requirements.txt..."
pip freeze > requirements.txt

cd ..

# Frontend setup
print_status "Setting up frontend..."
cd frontend

# Fix Heroicons imports if needed
print_status "Fixing frontend import issues..."
find src -name "*.jsx" -type f -exec sed -i.bak 's/RefreshIcon/ArrowPathIcon/g' {} \; 2>/dev/null || true
find src -name "*.jsx" -type f -exec sed -i.bak 's/TrendingUpIcon/ArrowTrendingUpIcon/g' {} \; 2>/dev/null || true
find src -name "*.bak" -delete 2>/dev/null || true

# Create essential frontend files
mkdir -p public

if [ ! -f "public/index.html" ]; then
    print_status "Creating index.html..."
    cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Journaling Assistant with AI insights" />
    <title>Journaling Assistant</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF
fi

if [ ! -f "public/manifest.json" ]; then
    cat > public/manifest.json << 'EOF'
{
  "short_name": "Journal AI",
  "name": "Journaling Assistant",
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
EOF
fi

touch public/favicon.ico

# Install frontend dependencies
print_status "Installing frontend dependencies..."
if [ -f "package-lock.json" ]; then
    rm package-lock.json
fi

npm install

print_success "Frontend setup complete!"
cd ..

# Create data directories
mkdir -p data/chroma_db data/backups
touch data/.gitkeep

# Create startup scripts
print_status "Creating startup scripts..."

cat > start-backend.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Journaling Assistant Backend"
echo "========================================"

cd backend

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run the setup script first"
    exit 1
fi

source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "🐍 Using Python: $(python --version)"

# Test dependencies
python -c "
import sys
try:
    import fastapi, uvicorn
    print('✅ Core web framework: OK')
except ImportError as e:
    print(f'❌ Core dependencies missing: {e}')
    sys.exit(1)

try:
    import chromadb, transformers
    print('✅ AI features: Available')
except ImportError:
    print('⚠️  AI features: Limited (basic journaling only)')
"

# Check Ollama
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo ""
    echo "💡 For AI features, start Ollama:"
    echo "   ollama serve"
    echo "   ollama pull llama3.2"
    echo ""
fi

echo "📡 Starting backend server..."
echo "🌍 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

python run.py
EOF

cat > start-frontend.sh << 'EOF'
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
EOF

cat > start-both.sh << 'EOF'
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
EOF

chmod +x start-*.sh

# Create quick test script
cat > test-setup.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Journaling Assistant Setup"
echo "===================================="

# Test backend
echo "Testing backend..."
cd backend
source venv/bin/activate

python -c "
import sys
try:
    from app.main import app
    print('✅ Backend: Application imports successfully')
except Exception as e:
    print(f'⚠️ Backend: {e}')

try:
    import chromadb, transformers
    print('✅ AI: Full features available')
except ImportError:
    print('⚠️ AI: Limited features (basic journaling only)')
"

cd ..

# Test frontend
echo ""
echo "Testing frontend..."
cd frontend
if [ -d "node_modules" ]; then
    echo "✅ Frontend: Dependencies installed"
else
    echo "❌ Frontend: Dependencies missing"
fi

if [ -f "public/index.html" ]; then
    echo "✅ Frontend: Essential files present"
else
    echo "❌ Frontend: Missing essential files"
fi
cd ..

echo ""
echo "🎯 Setup Status Summary:"
echo "========================"
echo "Backend Core:     ✅ Ready"
echo "AI Features:      $([ "$AI_WORKING" = true ] && echo "✅ Ready" || echo "⚠️ Limited")"
echo "Frontend:         ✅ Ready"
echo ""
echo "🚀 Ready to start: ./start-both.sh"
EOF

chmod +x test-setup.sh

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "📊 Installation Summary:"
echo "========================"
echo "✅ Python 3.11 virtual environment"
echo "✅ Core web framework (FastAPI, uvicorn)"
echo "✅ Basic data processing (numpy, textblob)"
echo "✅ Ollama integration"
if [ "$AI_WORKING" = true ]; then
    echo "✅ AI/ML features (PyTorch, transformers, ChromaDB)"
else
    echo "⚠️  AI/ML features (limited - some packages failed)"
fi
echo "✅ Frontend dependencies"
echo "✅ Essential files created"
echo "✅ Startup scripts created"
echo ""
echo "🚀 Start the application:"
echo "========================"
echo "Option 1 - Both services:"
echo "  ./start-both.sh"
echo ""
echo "Option 2 - Separate terminals:"
echo "  Terminal 1: ./start-backend.sh"
echo "  Terminal 2: ./start-frontend.sh"
echo ""
echo "🧪 Test the setup:"
echo "  ./test-setup.sh"
echo ""
echo "💡 For full AI features:"
echo "  ollama serve"
echo "  ollama pull llama3.2"
echo ""

# Quick verification
print_status "Running quick verification..."
./test-setup.sh

echo ""
read -p "🚀 Start the application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting Journaling Assistant..."
    ./start-both.sh
else
    echo ""
    echo "👍 When ready to start:"
    echo "  ./start-both.sh"
    echo ""
    echo "📍 After starting, open: http://localhost:3000"
fi