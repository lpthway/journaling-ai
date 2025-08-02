#!/bin/bash

# Journaling Assistant - Development Start Script
# This script sets up and starts the development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if we're in the right directory
check_directory() {
    if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        print_error "Please run this script from the project root directory"
        print_error "Make sure you have both 'backend' and 'frontend' directories"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        print_error "Please install Python 3.11 or later"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is required but not installed"
        print_error "Please install Node.js 18 or later"
        exit 1
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_warning "Ollama is not running or not accessible at localhost:11434"
        print_warning "Please start Ollama first:"
        print_warning "  1. Install Ollama: curl https://ollama.ai/install.sh | sh"
        print_warning "  2. Start Ollama: ollama serve"
        print_warning "  3. Download a model: ollama pull llama3 (or phi3:mini for faster performance)"
        print_warning ""
        print_warning "Continuing anyway - you can start Ollama later..."
    fi
    
    print_success "System requirements check completed"
}

# Setup Python virtual environment and install dependencies
setup_backend() {
    print_status "Setting up Python backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip --quiet
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt --quiet
    
    print_success "Backend setup completed"
    cd ..
}

# Setup Node.js frontend and install dependencies
setup_frontend() {
    print_status "Setting up React frontend..."
    
    cd frontend
    
    # Install dependencies
    print_status "Installing Node.js dependencies..."
    npm install --silent
    
    print_success "Frontend setup completed"
    cd ..
}

# Create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Backend startup script
    cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Journaling Assistant Backend..."
cd backend
source venv/bin/activate
echo "📡 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop"
echo ""
python run.py
EOF
    
    # Frontend startup script
    cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "🌐 Starting Journaling Assistant Frontend..."
cd frontend
echo "📱 Frontend will be available at: http://localhost:3000"
echo "🛑 Press Ctrl+C to stop"
echo ""
npm start
EOF
    
    # Combined startup script
    cat > start-both.sh << 'EOF'
#!/bin/bash

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    echo "✅ Cleanup completed"
    exit 0
}

# Set up signal trap
trap cleanup SIGINT SIGTERM

echo "🌟 Starting Journaling Assistant - Full Stack"
echo "=============================================="

# Start backend in background
echo "🚀 Starting backend..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🌐 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started successfully!"
echo "📱 Frontend: http://localhost:3000"
echo "📡 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
EOF
    
    # Make scripts executable
    chmod +x start-backend.sh start-frontend.sh start-both.sh
    
    print_success "Startup scripts created"
}

# Create development environment file
create_env_files() {
    print_status "Creating environment configuration..."
    
    # Backend .env
    if [ ! -f "backend/.env" ]; then
        cat > backend/.env << 'EOF'
# Journaling Assistant - Backend Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
EMBEDDING_MODEL=multilingual-e5-large
SENTIMENT_MODEL=cardiffnlp/twitter-roberta-base-sentiment-latest
DEBUG=true
EOF
        print_success "Created backend/.env"
    else
        print_status "Backend .env file already exists"
    fi
    
    # Frontend .env
    if [ ! -f "frontend/.env" ]; then
        cat > frontend/.env << 'EOF'
# Journaling Assistant - Frontend Configuration
REACT_APP_API_URL=http://localhost:8000/api/v1
GENERATE_SOURCEMAP=false
EOF
        print_success "Created frontend/.env"
    else
        print_status "Frontend .env file already exists"
    fi
}

# Create data directory
setup_data_directory() {
    print_status "Setting up data directory..."
    
    mkdir -p data/chroma_db
    mkdir -p data/backups
    
    # Create .gitkeep files
    touch data/.gitkeep
    touch data/chroma_db/.gitkeep
    touch data/backups/.gitkeep
    
    print_success "Data directory created"
}

# Main execution
main() {
    echo "🌟 Journaling Assistant - Development Setup"
    echo "==========================================="
    echo ""
    
    check_directory
    check_requirements
    setup_data_directory
    create_env_files
    setup_backend
    setup_frontend
    create_startup_scripts
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "==============================="
    echo ""
    echo "🚀 How to start the application:"
    echo ""
    echo "Option 1 - Start both services together:"
    echo "  ./start-both.sh"
    echo ""
    echo "Option 2 - Start services separately:"
    echo "  Terminal 1: ./start-backend.sh"
    echo "  Terminal 2: ./start-frontend.sh"
    echo ""
    echo "Option 3 - Manual start:"
    echo "  Backend:  cd backend && source venv/bin/activate && python run.py"
    echo "  Frontend: cd frontend && npm start"
    echo ""
    echo "📱 Once started, open: http://localhost:3000"
    echo "📡 Backend API will be at: http://localhost:8000"
    echo ""
    echo "💡 Don't forget to start Ollama if you haven't already:"
    echo "  ollama serve"
    echo "  ollama pull llama3  # or phi3:mini for faster performance"
    echo ""
    
    # Ask if user wants to start now
    read -p "🚀 Would you like to start the application now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting application..."
        ./start-both.sh
    else
        echo "👍 Run './start-both.sh' when you're ready to start!"
    fi
}

# Run main function
main "$@"