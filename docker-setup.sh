#!/bin/bash
# Journaling AI Docker Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🚀 Journaling AI Docker Setup"
echo "============================================"

# Detect GPU availability
GPU_AVAILABLE=false
if command -v nvidia-smi >/dev/null 2>&1; then
    if nvidia-smi >/dev/null 2>&1; then
        GPU_AVAILABLE=true
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits | head -1)
        print_status "GPU detected: $GPU_INFO"
    fi
fi

if [ "$GPU_AVAILABLE" = false ]; then
    print_warning "No GPU detected or NVIDIA drivers not available"
    print_info "Will use CPU-only mode"
fi
echo "============================="

# Show help if requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [MODE] [OPTIONS]"
    echo ""
    echo "MODES:"
    echo "  redis         Start Redis only (for when PostgreSQL runs on host)"
    echo "  redis-dev     Start Redis with Redis Commander GUI"
    echo "  redis-celery  Start Redis + Celery workers (for background processing)"
    echo "  db            Start PostgreSQL + Redis"
    echo "  dev           Start PostgreSQL + Redis + GUI tools"
    echo "  celery        Start Redis + Celery workers + Flower dashboard"
    echo "  app           Start full application stack"
    echo "  all           Start PostgreSQL + Redis (default)"
    echo ""
    echo "OPTIONS:"
    echo "  --gpu         Force GPU mode (requires NVIDIA GPU + Docker GPU support)"
    echo "  --cpu         Force CPU-only mode"
    echo "  --auto        Auto-detect GPU (default)"
    echo ""
    echo "Examples:"
    echo "  $0 redis --gpu           # Redis with GPU backend"
    echo "  $0 celery --cpu          # Celery with CPU-only processing"
    echo "  $0 app --auto            # Full stack with auto GPU detection"
    echo "  all           Start PostgreSQL + Redis (default)"
    echo ""
    echo "Examples:"
    echo "  $0 redis         # Just Redis (host PostgreSQL)"
    echo "  $0 redis-celery  # Redis + Celery workers"
    echo "  $0 celery        # Full Celery stack with monitoring"
    echo "  $0 db            # Both databases"
    echo "  $0 dev           # Databases + GUI tools"
    echo ""
    exit 0
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running"

# Check for Docker Compose
DOCKER_COMPOSE_CMD=""
if command -v docker-compose >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    print_error "Docker Compose not found. Please install Docker Compose."
    print_info "Install with: sudo apt-get install docker-compose-plugin"
    exit 1
fi

print_status "Docker Compose found: $DOCKER_COMPOSE_CMD"

# Parse arguments for GPU mode
MODE="$1"
GPU_MODE="auto"

# Process GPU options
for arg in "$@"; do
    case $arg in
        --gpu)
            GPU_MODE="force"
            shift
            ;;
        --cpu)
            GPU_MODE="disable"
            shift
            ;;
        --auto)
            GPU_MODE="auto"
            shift
            ;;
    esac
done

# Determine final GPU usage
USE_GPU=false
COMPOSE_FILE="docker-compose.yml"

case $GPU_MODE in
    "force")
        if [ "$GPU_AVAILABLE" = true ]; then
            USE_GPU=true
            COMPOSE_FILE="docker-compose.gpu.yml"
            print_status "Forcing GPU mode"
        else
            print_error "GPU forced but not available. Please install NVIDIA drivers and nvidia-docker"
            exit 1
        fi
        ;;
    "disable")
        USE_GPU=false
        print_info "CPU-only mode forced"
        ;;
    "auto")
        if [ "$GPU_AVAILABLE" = true ]; then
            USE_GPU=true
            COMPOSE_FILE="docker-compose.gpu.yml"
            print_status "Auto-detected GPU, using GPU mode"
        else
            USE_GPU=false
            print_info "Auto-detected CPU-only mode"
        fi
        ;;
esac

# Create necessary directories
mkdir -p data/chroma_db
mkdir -p data/psychology_db
mkdir -p data/backups

print_status "Created data directories"

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_info "Created .env file from .env.example"
        print_warning "Please review and update .env file with your settings"
    else
        print_warning ".env.example not found, using default settings"
    fi
fi

# Start services based on arguments
PROFILE_GPU=""
PROFILE_CPU=""
if [ "$USE_GPU" = true ]; then
    PROFILE_GPU="--profile gpu"
    BACKEND_SERVICE="backend"
    CELERY_SERVICE="celery-worker"
else
    PROFILE_CPU="--profile cpu"
    BACKEND_SERVICE="backend-cpu"
    CELERY_SERVICE="celery-worker-cpu"
fi

case "$MODE" in
    "redis")
        print_info "Starting Redis only..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d redis
        ;;
    "redis-dev")
        print_info "Starting Redis with GUI tools..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE --profile monitoring up -d redis redis-commander
        ;;
    "redis-celery")
        print_info "Starting Redis + Celery workers..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE $PROFILE_GPU $PROFILE_CPU --profile celery up -d redis $CELERY_SERVICE
        ;;
    "db")
        print_info "Starting database services only..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d postgres redis
        ;;
    "dev")
        print_info "Starting database services with dev tools..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE --profile monitoring up -d postgres redis redis-commander
        ;;
    "celery")
        print_info "Starting full Celery stack with monitoring..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE $PROFILE_GPU $PROFILE_CPU --profile celery --profile monitoring up -d redis $CELERY_SERVICE celery-beat flower redis-commander
        ;;
    "app")
        print_info "Starting full application stack..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE $PROFILE_GPU $PROFILE_CPU --profile monitoring up -d
        ;;
    "all"|*)
        print_info "Starting database services..."
        $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d postgres redis
        ;;
esac

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 5

# Check service health
print_info "Checking service health..."

if $DOCKER_COMPOSE_CMD ps postgres | grep -q "Up" 2>/dev/null; then
    print_status "PostgreSQL is running on localhost:5432"
    print_info "  Database: journaling_ai"
    print_info "  Username: postgres"
    print_info "  Password: password"
elif [ "${1}" != "redis" ] && [ "${1}" != "redis-dev" ]; then
    print_error "PostgreSQL failed to start"
fi

if $DOCKER_COMPOSE_CMD ps redis | grep -q "Up"; then
    print_status "Redis is running on localhost:6379"
    print_info "  Password: password"
    print_info "  Database: 0"
else
    print_error "Redis failed to start"
fi

# Check Celery services if running
if $DOCKER_COMPOSE_CMD ps celery-worker | grep -q "Up" 2>/dev/null; then
    print_status "Celery Worker is running"
fi

if $DOCKER_COMPOSE_CMD ps celery-beat | grep -q "Up" 2>/dev/null; then
    print_status "Celery Beat scheduler is running"
fi

if $DOCKER_COMPOSE_CMD ps flower | grep -q "Up" 2>/dev/null; then
    print_status "Flower monitoring is running on localhost:5555"
fi

# Show running services
echo ""
print_info "Running services:"
$DOCKER_COMPOSE_CMD ps

echo ""
print_info "Useful commands:"
echo "  🔴 Redis only:          ./docker-setup.sh redis"
echo "  🔴 Redis + GUI:         ./docker-setup.sh redis-dev"
echo "  ⚡ Redis + Celery:      ./docker-setup.sh redis-celery"
echo "  � Full Celery stack:   ./docker-setup.sh celery"
echo "  �📊 View logs:           $DOCKER_COMPOSE_CMD logs -f redis"
echo "  📊 View Celery logs:    $DOCKER_COMPOSE_CMD logs -f celery-worker"
echo "  🛑 Stop services:       $DOCKER_COMPOSE_CMD down"
echo "  🗑️  Remove data:         $DOCKER_COMPOSE_CMD down -v"
echo "  🔧 Redis GUI:           http://localhost:8081 (with redis-dev or dev)"
echo "  🐘 pgAdmin:             http://localhost:8080 (with dev mode)"
echo "  🌸 Flower Dashboard:    http://localhost:5555 (with celery mode)"
echo "  🏃 Run backend:         cd backend && python -m app.main"

if [ "${1}" = "dev" ]; then
    echo ""
    print_status "Development tools available:"
    echo "  🔧 Redis Commander: http://localhost:8081"
    echo "  🐘 pgAdmin:         http://localhost:8080 (admin@journaling.ai / admin)"
elif [ "${1}" = "redis-dev" ]; then
    echo ""
    print_status "Redis development tools available:"
    echo "  🔧 Redis Commander: http://localhost:8081"
elif [ "${1}" = "celery" ]; then
    echo ""
    print_status "Celery services available:"
    echo "  🌸 Flower Dashboard: http://localhost:5555"
    echo "  🔧 Redis Commander: http://localhost:8081"
    echo "  ⚡ Celery Worker:     Background task processing"
    echo "  ⏰ Celery Beat:       Scheduled task execution"
elif [ "${1}" = "redis-celery" ]; then
    echo ""
    print_status "Redis + Celery services available:"
    echo "  ⚡ Celery Worker:     Background task processing"
fi

print_status "Setup complete! 🎉"
