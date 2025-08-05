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
echo "============================="

# Show help if requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  redis      Start Redis only (for when PostgreSQL runs on host)"
    echo "  redis-dev  Start Redis with Redis Commander GUI"
    echo "  db         Start PostgreSQL + Redis"
    echo "  dev        Start PostgreSQL + Redis + GUI tools"
    echo "  app        Start full application stack"
    echo "  all        Start PostgreSQL + Redis (default)"
    echo ""
    echo "Examples:"
    echo "  $0 redis     # Just Redis (host PostgreSQL)"
    echo "  $0 db        # Both databases"
    echo "  $0 dev       # Databases + GUI tools"
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
case "${1:-all}" in
    "redis")
        print_info "Starting Redis only..."
        $DOCKER_COMPOSE_CMD up -d redis
        ;;
    "redis-dev")
        print_info "Starting Redis with GUI tools..."
        $DOCKER_COMPOSE_CMD --profile dev up -d redis redis-commander
        ;;
    "db")
        print_info "Starting database services only..."
        $DOCKER_COMPOSE_CMD up -d postgres redis
        ;;
    "dev")
        print_info "Starting database services with dev tools..."
        $DOCKER_COMPOSE_CMD --profile dev up -d postgres redis redis-commander pgadmin
        ;;
    "app")
        print_info "Starting full application stack..."
        $DOCKER_COMPOSE_CMD --profile app --profile dev up -d
        ;;
    "all"|*)
        print_info "Starting database services..."
        $DOCKER_COMPOSE_CMD up -d postgres redis
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

# Show running services
echo ""
print_info "Running services:"
$DOCKER_COMPOSE_CMD ps

echo ""
print_info "Useful commands:"
echo "  🔴 Redis only:          ./docker-setup.sh redis"
echo "  🔴 Redis + GUI:         ./docker-setup.sh redis-dev"
echo "  📊 View logs:           $DOCKER_COMPOSE_CMD logs -f redis"
echo "  🛑 Stop services:       $DOCKER_COMPOSE_CMD down"
echo "  🗑️  Remove data:         $DOCKER_COMPOSE_CMD down -v"
echo "  🔧 Redis GUI:           http://localhost:8081 (with redis-dev or dev)"
echo "  🐘 pgAdmin:             http://localhost:8080 (with dev mode)"
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
fi

print_status "Setup complete! 🎉"
