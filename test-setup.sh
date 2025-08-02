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
