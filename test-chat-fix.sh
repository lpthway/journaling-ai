#!/bin/bash

echo "🧪 Testing Chat Fix"
echo "=================="

# Check if files exist
echo "Checking chat component files..."

if [ -f "frontend/src/components/chat/ChatMessage.jsx" ]; then
    echo "✅ ChatMessage.jsx exists"
else
    echo "❌ ChatMessage.jsx missing"
fi

if [ -f "frontend/src/components/chat/ChatInput.jsx" ]; then
    echo "✅ ChatInput.jsx exists"
else
    echo "❌ ChatInput.jsx missing"
fi

if [ -f "frontend/src/components/chat/ChatInterface.jsx" ]; then
    echo "✅ ChatInterface.jsx exists"
else
    echo "❌ ChatInterface.jsx missing"
fi

echo ""
echo "🔍 Looking for potential issues in ChatMessage component..."

if grep -q "message?.role" frontend/src/components/chat/ChatMessage.jsx; then
    echo "✅ Uses optional chaining for message.role"
else
    echo "⚠️  Check message.role access pattern"
fi

if grep -q "!message && !isTyping" frontend/src/components/chat/ChatMessage.jsx; then
    echo "✅ Has proper null checking"
else
    echo "⚠️  May need better null checking"
fi

echo ""
echo "💡 If you still get errors, try using the debug version:"
echo "   Replace ChatMessage with ChatMessageDebug in ChatInterface.jsx"
echo ""
echo "🚀 Restart your development server after these fixes:"
echo "   npm start (in frontend directory)"
