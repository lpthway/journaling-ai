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
