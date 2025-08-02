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
