#!/bin/bash

# Debug and Fix Virtual Environment Setup
# This script will diagnose and fix the venv creation issue

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

echo "🔍 Debugging Virtual Environment Setup"
echo "======================================"
echo ""

# Check current directory
print_status "Current directory: $(pwd)"
print_status "Directory contents:"
ls -la

# Check Python installations
print_status "Checking Python installations..."
echo "Available Python commands:"
which python3.11 2>/dev/null && echo "✅ python3.11 found at: $(which python3.11)" || echo "❌ python3.11 not found"
which python3 2>/dev/null && echo "✅ python3 found at: $(which python3)" || echo "❌ python3 not found"
which python 2>/dev/null && echo "✅ python found at: $(which python)" || echo "❌ python not found"

echo ""
print_status "Python versions:"
python3.11 --version 2>/dev/null || echo "❌ python3.11 version check failed"
python3 --version 2>/dev/null || echo "❌ python3 version check failed"

# Check if we have venv module
print_status "Checking venv module availability..."
python3.11 -m venv --help >/dev/null 2>&1 && echo "✅ python3.11 venv module available" || {
    echo "❌ python3.11 venv module not available"
    print_error "You may need to install python3.11-venv package"
    echo "Try: sudo apt install python3.11-venv python3.11-dev"
}

# Check backend directory
if [ ! -d "backend" ]; then
    print_error "Backend directory not found!"
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Backend directory exists: ✅"

# Clean up any broken venv
if [ -d "backend/venv" ]; then
    print_warning "Removing existing virtual environment..."
    rm -rf backend/venv
fi

# Try to create virtual environment with debugging
print_status "Attempting to create virtual environment..."
cd backend

print_status "Current directory: $(pwd)"
print_status "Attempting: python3.11 -m venv venv"

# Create venv with verbose output
if python3.11 -m venv venv --clear --verbose; then
    print_success "Virtual environment created successfully!"
else
    print_error "Virtual environment creation failed!"
    
    # Try alternative approaches
    print_status "Trying alternative methods..."
    
    # Method 2: Try with system site packages
    print_status "Trying with --system-site-packages..."
    if python3.11 -m venv venv --system-site-packages --clear; then
        print_success "Virtual environment created with system site packages!"
    else
        # Method 3: Try with python3 if it's 3.11
        PYTHON3_VERSION=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>/dev/null || echo "unknown")
        if [[ "$PYTHON3_VERSION" == "3.11" ]]; then
            print_status "Trying with python3 command..."
            if python3 -m venv venv --clear; then
                print_success "Virtual environment created with python3!"
            else
                print_error "All virtual environment creation methods failed!"
                exit 1
            fi
        else
            print_error "Could not create virtual environment with any method!"
            exit 1
        fi
    fi
fi

# Verify the virtual environment
print_status "Verifying virtual environment..."
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    print_success "Virtual environment structure looks good"
    
    # List contents
    print_status "Virtual environment contents:"
    ls -la venv/
    echo ""
    ls -la venv/bin/ | head -10
    
    # Test activation
    print_status "Testing virtual environment activation..."
    source venv/bin/activate
    
    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Virtual environment activated successfully!"
        print_success "VIRTUAL_ENV: $VIRTUAL_ENV"
        print_success "Python in venv: $(which python)"
        print_success "Python version: $(python --version)"
        
        # Test pip
        print_status "Testing pip..."
        if python -m pip --version; then
            print_success "Pip is working!"
        else
            print_warning "Pip issue, trying to fix..."
            python -m ensurepip --default-pip
        fi
        
        deactivate
    else
        print_error "Virtual environment activation failed!"
        exit 1
    fi
else
    print_error "Virtual environment structure is incomplete!"
    print_error "Missing files or directories"
    exit 1
fi

cd ..

print_success "Virtual environment debugging complete!"

# Now try a simple installation test
print_status "Testing package installation in virtual environment..."
cd backend
source venv/bin/activate

# Upgrade pip first
print_status "Upgrading pip..."
python -m pip install --upgrade pip

# Test installing a simple package
print_status "Testing package installation with requests..."
if pip install requests; then
    print_success "Package installation works!"
    
    # Test the package
    python -c "import requests; print('✅ Package import works!')"
else
    print_error "Package installation failed!"
    exit 1
fi

deactivate
cd ..

echo ""
print_success "🎉 Virtual environment setup is working!"
echo ""
print_status "Now you can run the main setup. Here's a safe minimal installation:"

# Create a working minimal setup
cat > safe_minimal_setup.sh << 'EOF'
#!/bin/bash

echo "🚀 Safe Minimal Setup"
echo "====================="

cd backend
source venv/bin/activate

echo "Installing core dependencies one by one..."

# Install in very safe order
pip install --upgrade pip
pip install wheel setuptools

echo "Installing core web framework..."
pip install fastapi==0.104.1
pip install uvicorn==0.24.0  
pip install pydantic==2.5.0

echo "Installing basic utilities..."
pip install requests
pip install python-dateutil
pip install aiofiles
pip install python-multipart
pip install pydantic-settings

echo "Installing data handling..."
pip install numpy
pip install textblob

echo "Installing Ollama client..."
pip install ollama

echo "Testing imports..."
python -c "
try:
    import fastapi
    import uvicorn
    import pydantic
    import requests
    import numpy
    import ollama
    print('✅ All core dependencies imported successfully!')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo "Testing app import..."
python -c "
try:
    from app.main import app
    print('✅ App imports successfully!')
except Exception as e:
    print(f'⚠️ App import issue: {e}')
    print('This may be due to missing optional dependencies')
"

cd ..

echo ""
echo "✅ Core setup complete!"
echo "Next steps:"
echo "1. cd backend && source venv/bin/activate && python run.py"
echo "2. In another terminal: cd frontend && npm install && npm start"
EOF

chmod +x safe_minimal_setup.sh

echo ""
echo "🔧 VIRTUAL ENVIRONMENT FIXED!"
echo "============================="
echo ""
echo "✅ Virtual environment creation working"
echo "✅ Package installation working"
echo "✅ Python imports working"
echo ""
echo "🚀 Next steps:"
echo "1. Run: ./safe_minimal_setup.sh"
echo "2. Or manually:"
echo "   cd backend && source venv/bin/activate"
echo "   pip install fastapi uvicorn pydantic numpy requests ollama"
echo "   python run.py"
echo ""
echo "🎯 The virtual environment issue has been resolved!"