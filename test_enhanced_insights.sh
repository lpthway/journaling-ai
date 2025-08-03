#!/bin/bash

echo "🧪 Testing Enhanced Insights Integration"
echo "======================================="

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend not running. Start it first:"
    echo "   cd backend && source venv/bin/activate && python run.py"
    exit 1
fi

echo "✅ Backend is running"

# Test enhanced insights endpoints
echo ""
echo "🔧 Testing enhanced insights endpoints..."

# Test 1: Check if enhanced service is available
echo "1. Testing enhanced coaching endpoint..."
COACHING_RESPONSE=$(curl -s "http://localhost:8000/api/v1/insights/coaching")
if echo "$COACHING_RESPONSE" | grep -q "suggestions"; then
    echo "   ✅ Enhanced coaching endpoint working"
else
    echo "   ❌ Enhanced coaching endpoint failed"
    echo "   Response: $COACHING_RESPONSE"
fi

# Test 2: Check chat insights
echo "2. Testing chat insights endpoint..."
CHAT_RESPONSE=$(curl -s "http://localhost:8000/api/v1/insights/chat-insights")
if echo "$CHAT_RESPONSE" | grep -q "conversations\|message"; then
    echo "   ✅ Chat insights endpoint working"
else
    echo "   ❌ Chat insights endpoint failed"
    echo "   Response: $CHAT_RESPONSE"
fi

# Test 3: Check enhanced patterns
echo "3. Testing enhanced patterns endpoint..."
PATTERNS_RESPONSE=$(curl -s "http://localhost:8000/api/v1/insights/patterns-enhanced")
if echo "$PATTERNS_RESPONSE" | grep -q "mood_analysis\|conversation_patterns"; then
    echo "   ✅ Enhanced patterns endpoint working"
else
    echo "   ❌ Enhanced patterns endpoint failed"
    echo "   Response: $PATTERNS_RESPONSE"
fi

# Test 4: Test ask question with sample
echo "4. Testing enhanced ask endpoint..."
ASK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/insights/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "what was our last conversation?"}' 2>/dev/null || \
  curl -s "http://localhost:8000/api/v1/insights/ask?question=what%20was%20our%20last%20conversation")

if echo "$ASK_RESPONSE" | grep -q "answer\|question"; then
    echo "   ✅ Enhanced ask endpoint working"
else
    echo "   ❌ Enhanced ask endpoint failed"
    echo "   Response: $ASK_RESPONSE"
fi

# Test 5: Check comprehensive mood analysis
echo "5. Testing comprehensive mood analysis..."
MOOD_RESPONSE=$(curl -s "http://localhost:8000/api/v1/insights/mood-analysis-comprehensive")
if echo "$MOOD_RESPONSE" | grep -q "sources\|mood"; then
    echo "   ✅ Comprehensive mood analysis working"
else
    echo "   ❌ Comprehensive mood analysis failed"
    echo "   Response: $MOOD_RESPONSE"
fi

echo ""
echo "🎯 INTEGRATION TEST SUMMARY"
echo "=========================="

# Count working endpoints
WORKING=0
if echo "$COACHING_RESPONSE" | grep -q "suggestions"; then ((WORKING++)); fi
if echo "$CHAT_RESPONSE" | grep -q "conversations\|message"; then ((WORKING++)); fi
if echo "$PATTERNS_RESPONSE" | grep -q "mood_analysis\|conversation_patterns"; then ((WORKING++)); fi
if echo "$ASK_RESPONSE" | grep -q "answer\|question"; then ((WORKING++)); fi
if echo "$MOOD_RESPONSE" | grep -q "sources\|mood"; then ((WORKING++)); fi

echo "Working endpoints: $WORKING/5"

if [ $WORKING -eq 5 ]; then
    echo "🎉 ALL ENHANCED FEATURES WORKING!"
    echo ""
    echo "✨ Your insights now include both:"
    echo "   📔 Journal entries"
    echo "   💬 Chat conversations"
    echo ""
    echo "🚀 Try asking questions like:"
    echo "   - 'How do my conversations complement my journal writing?'"
    echo "   - 'What patterns do you see across all my reflections?'"
    echo "   - 'How has my communication evolved over time?'"
    echo ""
    echo "🌐 Test in browser:"
    echo "   http://localhost:3000 → Insights → Ask AI"
    
elif [ $WORKING -gt 2 ]; then
    echo "⚠️  PARTIAL INTEGRATION - $WORKING/5 endpoints working"
    echo "The basic functionality is available, some advanced features may be limited."
    
else
    echo "❌ INTEGRATION ISSUES - Only $WORKING/5 endpoints working"
    echo ""
    echo "🔧 Troubleshooting steps:"
    echo "1. Check backend logs for errors"
    echo "2. Verify all services are imported correctly"
    echo "3. Restart the backend:"
    echo "   cd backend && source venv/bin/activate && python run.py"
fi

echo ""
echo "📊 Sample Responses (first 200 chars):"
echo "======================================="
echo "Coaching: $(echo "$COACHING_RESPONSE" | head -c 200)..."
echo ""
echo "Chat Insights: $(echo "$CHAT_RESPONSE" | head -c 200)..."
echo ""
echo "Enhanced Ask: $(echo "$ASK_RESPONSE" | head -c 200)..."
echo ""

# Test frontend integration if available
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "🌐 Frontend is also running at: http://localhost:3000"
    echo "✨ Enhanced insights available in the Insights section!"
else
    echo "💡 Start frontend to test enhanced UI:"
    echo "   cd frontend && npm start"
fi