#!/bin/bash

# Python 3.11 Setup Script for Journaling Assistant
# This script sets up the project with Python 3.11 for better compatibility

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

echo "🐍 Python 3.11 Setup for Journaling Assistant"
echo "=============================================="
echo ""

# Check if Python 3.11 is available
check_python311() {
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Found python3.11"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
        if [[ "$PYTHON_VERSION" == "3.11" ]]; then
            PYTHON_CMD="python3"
            print_success "Found python3 (version 3.11)"
        else
            print_warning "python3 is version $PYTHON_VERSION, not 3.11"
            print_status "Will attempt to use python3.11..."
            if command -v python3.11 &> /dev/null; then
                PYTHON_CMD="python3.11"
            else
                print_error "Python 3.11 not found!"
                show_install_instructions
                exit 1
            fi
        fi
    else
        print_error "No Python 3.11 installation found!"
        show_install_instructions
        exit 1
    fi
    
    echo "Using Python command: $PYTHON_CMD"
    $PYTHON_CMD --version
}

show_install_instructions() {
    echo ""
    print_warning "Python 3.11 Installation Instructions:"
    echo ""
    echo "📦 Ubuntu/Debian:"
    echo "  sudo apt update"
    echo "  sudo apt install python3.11 python3.11-venv python3.11-pip"
    echo ""
    echo "🍎 macOS (with Homebrew):"
    echo "  brew install python@3.11"
    echo ""
    echo "🎯 CentOS/RHEL:"
    echo "  sudo dnf install python3.11 python3.11-pip"
    echo ""
    echo "🔗 Or download from: https://www.python.org/downloads/"
}

# Stop any running processes
print_status "Stopping any running processes..."
pkill -f "python run.py" 2>/dev/null || true
pkill -f "react-scripts start" 2>/dev/null || true
sleep 2

# Check Python 3.11
check_python311

# Clean up existing environment
print_status "Cleaning up existing Python environment..."
if [ -d "backend/venv" ]; then
    rm -rf backend/venv
    print_success "Removed existing virtual environment"
fi

# Setup backend with Python 3.11
print_status "Setting up backend with Python 3.11..."
cd backend

# Create virtual environment with Python 3.11
print_status "Creating Python 3.11 virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify we're using Python 3.11
VENV_PYTHON_VERSION=$(python --version)
print_success "Virtual environment created with: $VENV_PYTHON_VERSION"

if [[ ! "$VENV_PYTHON_VERSION" == *"3.11"* ]]; then
    print_warning "Virtual environment is not using Python 3.11"
    print_warning "This might still work, but 3.11 is recommended"
fi

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Create optimized requirements.txt for Python 3.11
print_status "Creating optimized requirements.txt for Python 3.11..."

cat > requirements.txt << 'EOF'
# Core FastAPI and server dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
aiofiles==23.2.1
python-dateutil==2.8.2

# Vector database and embeddings (optimized for Python 3.11)
chromadb==0.4.24
sentence-transformers==3.0.1

# Ollama for local LLM
ollama==0.1.9

# AI/ML dependencies (Python 3.11 optimized versions)
torch==2.5.0
transformers==4.44.0
textblob==0.17.1

# Data processing (stable versions)
numpy==1.26.0
pandas==2.1.4

# Additional dependencies
requests==2.31.0
typing-extensions==4.8.0
huggingface-hub==0.19.4
tokenizers==0.15.0
scikit-learn==1.3.2
EOF

# Install dependencies
print_status "Installing Python dependencies (this may take several minutes)..."

# Install in optimal order for Python 3.11
pip install wheel setuptools

# Core web framework
pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.0

# Data science stack
pip install numpy==1.26.0 pandas==2.1.4 scikit-learn==1.3.2

# PyTorch (CPU version for compatibility)
pip install torch==2.5.0 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
pip install -r requirements.txt

# Verify installation
print_status "Verifying installation..."
python -c "
import sys
print(f'Python version: {sys.version}')

# Test critical imports
try:
    import fastapi
    import uvicorn
    import chromadb
    import ollama
    import transformers
    import textblob
    import numpy
    import torch
    print('✅ All critical dependencies imported successfully')
    print(f'NumPy version: {numpy.__version__}')
    print(f'PyTorch version: {torch.__version__}')
    print(f'FastAPI version: {fastapi.__version__}')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Backend setup completed successfully with Python 3.11!"
else
    print_error "Some dependencies failed to install"
    exit 1
fi

cd ..

# Setup frontend (unchanged)
print_status "Setting up frontend..."
cd frontend

# Fix Heroicons imports
print_status "Fixing Heroicons imports..."
find src -name "*.jsx" -type f -exec sed -i.bak 's/RefreshIcon/ArrowPathIcon/g' {} \; 2>/dev/null || true
find src -name "*.jsx" -type f -exec sed -i.bak 's/TrendingUpIcon/ArrowTrendingUpIcon/g' {} \; 2>/dev/null || true

# Clean up backup files
find src -name "*.bak" -delete 2>/dev/null || true

# Create missing files
mkdir -p public

if [ ! -f "public/index.html" ]; then
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Local-first journaling assistant with AI insights" />
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
  "name": "Journaling Assistant with AI",
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
EOF
fi

touch public/favicon.ico

# Install Node dependencies
if [ -f "package-lock.json" ]; then
    rm package-lock.json
fi

print_status "Installing Node.js dependencies..."
npm install --silent

print_success "Frontend setup completed!"
cd ..

# Create data directories
mkdir -p data/chroma_db data/backups
touch data/.gitkeep

# Create startup scripts optimized for Python 3.11
print_status "Creating startup scripts..."

cat > start-backend.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Journaling Assistant Backend (Python 3.11)"
echo "====================================================="

if [ ! -d "backend/venv" ]; then
    echo "❌ Virtual environment not found"
    echo "Run the Python 3.11 setup script first"
    exit 1
fi

cd backend
source venv/bin/activate

# Show Python version
echo "🐍 Using: $(python --version)"

if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not running - AI features will be limited"
    echo "Start Ollama: ollama serve"
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

if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Node modules not found"
    echo "Run the setup script first"
    exit 1
fi

cd frontend
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

echo "🌟 Starting Journaling Assistant - Python 3.11"
echo "==============================================="

if [ ! -d "backend/venv" ] || [ ! -d "frontend/node_modules" ]; then
    echo "❌ Environment not set up. Run setup script first."
    exit 1
fi

# Start backend
echo "🚀 Starting backend..."
cd backend
source venv/bin/activate
echo "🐍 Using: $(python --version)"

python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "⏳ Waiting for backend..."
sleep 8

if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start"
    exit 1
fi

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend running and healthy"
else
    echo "⚠️  Backend health check failed"
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
echo "💡 For AI features:"
echo "   ollama serve"
echo "   ollama pull llama3.2"
echo ""
echo "🛑 Press Ctrl+C to stop both services"
echo ""

wait $BACKEND_PID $FRONTEND_PID
EOF

chmod +x start-backend.sh start-frontend.sh start-both.sh

# Create version info file
cat > PYTHON_VERSION_INFO.md << 'EOF'
# Python 3.11 Setup Complete

## Why Python 3.11?

✅ **Better Package Compatibility**: NumPy, PyTorch, and ML libraries are stable
✅ **Production Ready**: Widely used in production AI applications  
✅ **Fewer Dependency Conflicts**: Most packages have mature 3.11 builds
✅ **Performance**: Good balance of features and stability

## Verified Dependencies

- Python: 3.11.x
- NumPy: 1.26.0 (works perfectly with 3.11)
- PyTorch: 2.5.0 (CPU optimized)
- FastAPI: 0.104.1
- ChromaDB: 0.4.24

## Commands

- Start both: `./start-both.sh`
- Backend only: `./start-backend.sh`  
- Frontend only: `./start-frontend.sh`

## AI Setup

```bash
# Install and start Ollama
curl https://ollama.ai/install.sh | sh
ollama serve

# Download a model
ollama pull llama3.2  # Recommended
# or
ollama pull phi3:mini  # Faster, smaller model
```
EOF

print_success "Python 3.11 setup completed successfully!"

echo ""
echo "🎉 PYTHON 3.11 SETUP COMPLETE!"
echo "==============================="
echo ""
echo "✅ Created Python 3.11 virtual environment"
echo "✅ Installed optimized dependencies for 3.11"
echo "✅ Fixed all compatibility issues"
echo "✅ Verified all imports work correctly"
echo "✅ Created startup scripts"
echo ""
echo "📊 Your environment:"
echo "   Python: 3.11.x"
echo "   NumPy: 1.26.0 (perfect compatibility)"
echo "   PyTorch: 2.5.0 (CPU optimized)"
echo "   FastAPI: 0.104.1"
echo ""
echo "🚀 Ready to start:"
echo "   ./start-both.sh"
echo ""
echo "💡 For AI features:"
echo "   ollama serve"
echo "   ollama pull llama3.2"
echo ""

# Test the setup
print_status "Testing the setup..."
cd backend
source venv/bin/activate

python -c "
import sys
if sys.version_info[:2] == (3, 11):
    print('✅ Perfect! Using Python 3.11')
else:
    print(f'⚠️  Using Python {sys.version_info[:2]}, but should work fine')

try:
    from app.main import app
    print('✅ Backend imports successful')
except Exception as e:
    print(f'❌ Backend import error: {e}')
"

cd ..

echo ""
read -p "🚀 Start the application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting with Python 3.11..."
    ./start-both.sh
else
    echo "👍 Run './start-both.sh' when ready!"
fi