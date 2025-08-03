#!/bin/bash

# Hardware-Adaptive AI Installation and Test Script

echo "🚀 Hardware-Adaptive AI System Setup"
echo "====================================="

# Check if we're in the right directory
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ Error: Please run this script from the journaling-ai root directory"
    exit 1
fi

echo "📦 Installing required dependencies..."

# Install psutil for hardware monitoring
pip install psutil

echo "✅ Dependencies installed successfully!"

echo ""
echo "🔍 Testing hardware detection..."

# Run the test script
cd backend
python test_adaptive_ai.py

echo ""
echo "🎯 Hardware-Adaptive AI Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Start the backend server: python backend/run.py"
echo "2. Test the API endpoints:"
echo "   curl http://localhost:8000/api/v1/adaptive-ai/health"
echo "   curl http://localhost:8000/api/v1/adaptive-ai/capabilities"
echo ""
echo "🔗 API Documentation: http://localhost:8000/docs"
echo "📚 Full documentation: backend/app/core/README_Hardware_Adaptive_AI.md"
