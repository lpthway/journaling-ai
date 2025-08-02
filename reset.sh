#!/bin/bash

# Reset Development Environment Script
# This will clean up and reset the development environment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔄 Reset Journaling Assistant Development Environment"
echo "===================================================="
echo ""
print_warning "This will:"
print_warning "  - Remove Python virtual environment"
print_warning "  - Remove Node.js node_modules"
print_warning "  - Remove generated scripts"
print_warning "  - Keep your data directory intact"
echo ""

read -p "Are you sure you want to reset? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Reset cancelled"
    exit 0
fi

echo ""
echo "🧹 Cleaning up development environment..."

# Remove Python virtual environment
if [ -d "backend/venv" ]; then
    print_warning "Removing Python virtual environment..."
    rm -rf backend/venv
    print_success "Python virtual environment removed"
fi

# Remove Node modules
if [ -d "frontend/node_modules" ]; then
    print_warning "Removing Node.js modules..."
    rm -rf frontend/node_modules
    print_success "Node modules removed"
fi

# Remove package-lock.json
if [ -f "frontend/package-lock.json" ]; then
    rm frontend/package-lock.json
    print_success "package-lock.json removed"
fi

# Remove generated scripts
for script in start-backend.sh start-frontend.sh start-both.sh; do
    if [ -f "$script" ]; then
        rm "$script"
        print_success "Removed $script"
    fi
done

# Remove build directories
if [ -d "frontend/build" ]; then
    rm -rf frontend/build
    print_success "Frontend build directory removed"
fi

# Remove Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

print_success "🎉 Reset completed!"
echo ""
echo "🚀 To set up again, run: ./start.sh"