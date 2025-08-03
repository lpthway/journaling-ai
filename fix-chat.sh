#!/bin/bash

echo "🔧 Comprehensive Import Path Fix"
echo "================================"
echo ""
echo "This script fixes common import path issues that cause:"
echo "- Module not found errors"
echo "- Case sensitivity problems"
echo "- Incorrect relative paths"
echo ""

# Check if we're in the right directory
if [ ! -d "frontend/src" ]; then
    echo "❌ Please run this from the project root directory"
    echo "Expected structure: frontend/src/"
    exit 1
fi

# Create backup directory
BACKUP_DIR="frontend/src_backup_$(date +%Y%m%d_%H%M%S)"
echo "📦 Creating backup at: $BACKUP_DIR"
cp -r frontend/src "$BACKUP_DIR"

# 1. Fix main import issue in Chat.jsx
echo ""
echo "🔧 Fixing main import issues..."

if [ -f "frontend/src/pages/Chat.jsx" ]; then
    echo "  📝 Fixing Chat.jsx import path..."
    
    # Fix the ChatInterface import
    sed -i.tmp 's|import ChatInterface from '\''\.\/ChatInterface'\''|import ChatInterface from '\''../components/chat/ChatInterface'\''|g' frontend/src/pages/Chat.jsx
    
    # Also fix any other incorrect imports in Chat.jsx
    sed -i.tmp 's|from '\''\.\/components\/|from '\''../components/|g' frontend/src/pages/Chat.jsx
    
    # Remove temp file
    rm -f frontend/src/pages/Chat.jsx.tmp
    
    echo "  ✅ Chat.jsx imports fixed"
else
    echo "  ⚠️  Chat.jsx not found"
fi

# 2. Check and fix case sensitivity in component names
echo ""
echo "🔧 Checking case sensitivity issues..."

# Check if chat directory exists with correct case
if [ ! -d "frontend/src/components/chat" ]; then
    echo "  ❌ Chat components directory not found!"
    echo "  Looking for alternative cases..."
    
    if [ -d "frontend/src/components/Chat" ]; then
        echo "  📁 Found Chat/ (uppercase) - renaming to chat/"
        mv frontend/src/components/Chat frontend/src/components/chat
        echo "  ✅ Directory renamed"
    else
        echo "  ❌ No chat components directory found at all"
        echo "  Creating required directory structure..."
        mkdir -p frontend/src/components/chat
    fi
fi

# 3. Verify all required chat components exist
echo ""
echo "🔧 Verifying chat components..."

REQUIRED_COMPONENTS=(
    "ChatInterface.jsx"
    "ChatMessage.jsx"
    "ChatInput.jsx"
    "SessionTypeSelector.jsx"
)

MISSING_COMPONENTS=()

for component in "${REQUIRED_COMPONENTS[@]}"; do
    if [ -f "frontend/src/components/chat/$component" ]; then
        echo "  ✅ $component"
    else
        echo "  ❌ $component MISSING"
        MISSING_COMPONENTS+=("$component")
    fi
done

# 4. Fix common case sensitivity issues in imports throughout the project
echo ""
echo "🔧 Scanning for case sensitivity issues in imports..."

# Find all .jsx and .js files and check their imports
find frontend/src -name "*.jsx" -o -name "*.js" | while read file; do
    # Skip node_modules and other non-source files
    if [[ "$file" == *node_modules* ]] || [[ "$file" == *build* ]]; then
        continue
    fi
    
    # Check for potential case issues
    if grep -q "from.*[A-Z].*/" "$file" 2>/dev/null; then
        echo "  🔍 Checking: $file"
        
        # Fix common case issues
        sed -i.tmp 's|from '\''\.\.\/Common\/|from '\''../Common/|g' "$file"
        sed -i.tmp 's|from '\''\.\.\/components\/Chat\/|from '\''../components/chat/|g' "$file"
        sed -i.tmp 's|from '\''\.\/Chat\/|from '\''./chat/|g' "$file"
        
        # Remove temp file
        rm -f "$file.tmp"
    fi
done

# 5. Fix any remaining import path issues
echo ""
echo "🔧 Fixing additional import path patterns..."

# Common import fixes
find frontend/src -name "*.jsx" -o -name "*.js" | while read file; do
    if [[ "$file" == *node_modules* ]] || [[ "$file" == *build* ]]; then
        continue
    fi
    
    # Fix imports that go up too many directories
    sed -i.tmp 's|from '\''\.\.\/\.\.\/components/|from '\''../components/|g' "$file"
    sed -i.tmp 's|from '\''\.\.\/\.\.\/\.\.\/components/|from '\''../../components/|g' "$file"
    
    # Fix imports missing file extensions (if needed)
    # sed -i.tmp 's|from '\''\.\/\([^'\'']*\)'\''|from '\''.\/\1.jsx'\''|g' "$file"
    
    rm -f "$file.tmp"
done

# 6. Create an index file for chat components if missing
if [ ! -f "frontend/src/components/chat/index.js" ]; then
    echo ""
    echo "📝 Creating chat components index file..."
    
    cat > frontend/src/components/chat/index.js << 'EOF'
// frontend/src/components/chat/index.js
// Central exports for all chat components

export { default as ChatInterface } from './ChatInterface';
export { default as ChatMessage } from './ChatMessage';
export { default as ChatInput } from './ChatInput';
export { default as SessionTypeSelector } from './SessionTypeSelector';
EOF
    
    echo "  ✅ Created index.js for chat components"
fi

# 7. Validate all imports
echo ""
echo "🔍 Validating fixed imports..."

# Check if Chat.jsx has the correct import now
if [ -f "frontend/src/pages/Chat.jsx" ]; then
    if grep -q "from '../components/chat/ChatInterface'" frontend/src/pages/Chat.jsx; then
        echo "  ✅ Chat.jsx: ChatInterface import fixed"
    else
        echo "  ❌ Chat.jsx: ChatInterface import still incorrect"
        echo "  Current import:"
        grep "ChatInterface" frontend/src/pages/Chat.jsx || echo "  No ChatInterface import found"
    fi
fi

# 8. Check for circular dependencies
echo ""
echo "🔄 Checking for potential circular dependencies..."

# Simple check for obvious circular imports
if find frontend/src -name "*.jsx" -o -name "*.js" | xargs grep -l "from.*\.\./\.\./.*" | head -1 >/dev/null; then
    echo "  ⚠️  Found some complex relative imports - check for circular dependencies"
else
    echo "  ✅ No obvious circular dependency patterns found"
fi

# 9. Summary and next steps
echo ""
echo "📊 IMPORT FIX SUMMARY"
echo "===================="

if [ ${#MISSING_COMPONENTS[@]} -eq 0 ]; then
    echo "✅ All required chat components found"
else
    echo "❌ Missing components:"
    for component in "${MISSING_COMPONENTS[@]}"; do
        echo "   - $component"
    done
    echo ""
    echo "💡 These components need to be created or moved to frontend/src/components/chat/"
fi

echo ""
echo "🚀 NEXT STEPS:"
echo "=============="
echo "1. Restart your development server:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "2. If you still get errors, check the browser console for specifics"
echo ""
echo "3. Backup location (in case you need to revert):"
echo "   $BACKUP_DIR"
echo ""

if [ ${#MISSING_COMPONENTS[@]} -gt 0 ]; then
    echo "⚠️  IMPORTANT: You still have missing components!"
    echo "   The app won't work until these are created."
    echo ""
    echo "💡 Quick fix: Check if these files exist elsewhere:"
    for component in "${MISSING_COMPONENTS[@]}"; do
        echo "   find . -name '$component' -type f"
    done
fi

echo ""
echo "✨ Import path fixes completed!"