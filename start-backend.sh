#!/bin/bash
echo "🚀 Starting Journaling Assistant Backend..."
cd backend
source venv/bin/activate
echo "📡 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🛑 Press Ctrl+C to stop"
echo ""
python run.py
