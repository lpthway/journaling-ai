#!/bin/bash

# Journaling Assistant - Project Cleanup Script
# This script removes unnecessary files, temporary scripts, and cleans up the project structure

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

echo "🧹 Journaling Assistant - Project Cleanup"
echo "========================================="
echo ""
print_warning "This script will remove:"
print_warning "  ✗ Temporary bash scripts"
print_warning "  ✗ Backup files"
print_warning "  ✗ Duplicate/unused components"
print_warning "  ✗ Debug files"
print_warning "  ✗ Build artifacts"
print_warning "  ✗ Cache files"
echo ""
print_status "The following will be PRESERVED:"
print_status "  ✓ Core application files"
print_status "  ✓ Data directory"
print_status "  ✓ Configuration files"
print_status "  ✓ Main startup scripts"
echo ""

read -p "🤔 Continue with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo ""
print_status "Starting cleanup process..."

# Create backup list of what we're removing
CLEANUP_LOG="cleanup_$(date +%Y%m%d_%H%M%S).log"
echo "# Journaling Assistant Cleanup Log - $(date)" > "$CLEANUP_LOG"
echo "# Files removed during cleanup process" >> "$CLEANUP_LOG"
echo "" >> "$CLEANUP_LOG"

# Function to safely remove file/directory and log it
safe_remove() {
    local item="$1"
    local description="$2"
    
    if [ -e "$item" ]; then
        echo "Removing: $item ($description)" >> "$CLEANUP_LOG"
        rm -rf "$item"
        print_success "Removed: $item"
        return 0
    else
        return 1
    fi
}

# 1. Remove temporary bash scripts
echo ""
print_status "🔧 Removing temporary bash scripts..."

# Setup and fix scripts
safe_remove "complete-fix.sh" "Comprehensive fix script"
safe_remove "continue_setup.sh" "Setup continuation script"
safe_remove "debug_venv_setup.sh" "Virtual environment debug script"
safe_remove "fix-chat.sh" "Chat import fix script"
safe_remove "fix-journaling-app.sh" "App fix script"
safe_remove "minimal_python311_setup.sh" "Minimal Python setup script"
safe_remove "pytorch_cuda_setup.sh" "PyTorch CUDA setup script"
safe_remove "quick-fix.sh" "Quick fix script"
safe_remove "reset.sh" "Environment reset script"
safe_remove "safe_minimal_setup.sh" "Safe minimal setup script"

# Testing scripts
safe_remove "test-chat-fix.sh" "Chat fix test script"
safe_remove "test-setup.sh" "Setup test script"
safe_remove "test_enhanced_insights.sh" "Enhanced insights test script"

# Integration scripts
safe_remove "integrate_chat_insights_script.sh" "Chat insights integration script"

# 2. Remove backup and duplicate files
echo ""
print_status "📦 Removing backup and duplicate files..."

# Backend backups
safe_remove "backend/app/api/insights_original.py" "Original insights API backup"
safe_remove "backend_backup_*" "Backend backup directories"

# Frontend backups
safe_remove "frontend/src/Entry/EnhancedEntryEditor.jsx" "Misplaced entry editor"
safe_remove "frontend/src/components/chat/backup/" "Chat component backups"
safe_remove "frontend/src/components/chat/ChatMessageDebug.jsx" "Debug chat message component"

# Generic backup files
find . -name "*.backup" -type f | while read file; do
    safe_remove "$file" "Backup file"
done

find . -name "*.bak" -type f | while read file; do
    safe_remove "$file" "Backup file"
done

# 3. Remove Python cache and build artifacts
echo ""
print_status "🐍 Cleaning Python cache and build artifacts..."

# Python cache directories
find . -type d -name "__pycache__" | while read dir; do
    safe_remove "$dir" "Python cache directory"
done

# Python compiled files
find . -name "*.pyc" -type f | while read file; do
    safe_remove "$file" "Python compiled file"
done

find . -name "*.pyo" -type f | while read file; do
    safe_remove "$file" "Python optimized file"
done

# Python egg info
find . -name "*.egg-info" -type d | while read dir; do
    safe_remove "$dir" "Python egg info directory"
done

# 4. Remove Node.js artifacts
echo ""
print_status "📦 Cleaning Node.js artifacts..."

# Remove any secondary package-lock files
find . -name "package-lock.json.backup" -type f | while read file; do
    safe_remove "$file" "Package lock backup"
done

# Remove any npm debug logs
find . -name "npm-debug.log*" -type f | while read file; do
    safe_remove "$file" "NPM debug log"
done

find . -name "yarn-debug.log*" -type f | while read file; do
    safe_remove "$file" "Yarn debug log"
done

find . -name "yarn-error.log*" -type f | while read file; do
    safe_remove "$file" "Yarn error log"
done

# 5. Remove temporary and OS files
echo ""
print_status "🗂️ Removing temporary and OS files..."

# OS generated files
find . -name ".DS_Store" -type f | while read file; do
    safe_remove "$file" "macOS metadata file"
done

find . -name "Thumbs.db" -type f | while read file; do
    safe_remove "$file" "Windows thumbnail cache"
done

find . -name "desktop.ini" -type f | while read file; do
    safe_remove "$file" "Windows desktop configuration"
done

# Temporary files
find . -name "*.tmp" -type f | while read file; do
    safe_remove "$file" "Temporary file"
done

find . -name "*.temp" -type f | while read file; do
    safe_remove "$file" "Temporary file"
done

# 6. Clean up any remaining fix/debug scripts
echo ""
print_status "🔍 Removing any remaining fix/debug files..."

# Additional temporary scripts that might exist
for script in fix-*.sh debug-*.sh test-*.sh setup-*.sh *-fix.sh *-debug.sh *-test.sh; do
    if [ -f "$script" ] && [[ ! "$script" =~ ^(start-|test-setup\.sh)$ ]]; then
        safe_remove "$script" "Temporary script"
    fi
done

# 7. Remove empty directories (except important ones)
echo ""
print_status "📁 Removing empty directories..."

# Find and remove empty directories, but preserve important structure
find . -type d -empty | grep -v -E "(data|\.git|node_modules|venv|build|dist)" | while read dir; do
    if [ "$dir" != "." ]; then
        safe_remove "$dir" "Empty directory"
    fi
done

# 8. Clean up package.json scripts artifacts if any
echo ""
print_status "📋 Cleaning package.json artifacts..."

# Remove any backup package.json files
safe_remove "frontend/package.json.backup" "Package.json backup"
safe_remove "frontend/package.json.bak" "Package.json backup"

# 9. Remove any residual requirements files
echo ""
print_status "📄 Cleaning up requirements files..."

safe_remove "backend/requirements-core.txt" "Core requirements file"
safe_remove "backend/requirements-ai.txt" "AI requirements file"

# 10. Organize remaining scripts
echo ""
print_status "📚 Organizing remaining scripts..."

# Create scripts directory for essential scripts
mkdir -p scripts

# Move essential scripts to scripts directory
for script in start-backend-only.sh start-frontend-only.sh start-dev.sh add-ai-features.sh; do
    if [ -f "$script" ]; then
        mv "$script" scripts/
        print_success "Moved $script to scripts/"
    fi
done

# 11. Create final project structure summary
echo ""
print_status "📋 Creating project structure summary..."

cat > PROJECT_STRUCTURE.md << 'EOF'
# Journaling Assistant - Project Structure

## Core Application
```
├── backend/                 # Python FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/           # API routes
│   │   ├── models/        # Data models
│   │   ├── services/      # Business logic
│   │   └── core/          # Configuration
│   ├── venv/              # Python virtual environment
│   ├── requirements.txt   # Python dependencies
│   └── run.py            # Application entry point
│
├── frontend/               # React frontend
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── utils/         # Utilities
│   ├── public/            # Static files
│   ├── package.json       # Node.js dependencies
│   └── tailwind.config.js # Styling configuration
│
├── data/                   # Application data
│   ├── chroma_db/         # Vector database
│   └── backups/           # Data backups
│
└── scripts/               # Utility scripts
    ├── start-backend-only.sh
    ├── start-frontend-only.sh
    └── start-dev.sh
```

## Essential Scripts
- `start.sh` - Main setup and start script
- `start-both.sh` - Start both backend and frontend
- `start-backend.sh` - Start backend only
- `start-frontend.sh` - Start frontend only

## Data & Configuration
- `.gitignore` - Git ignore rules
- `PROJECT_STRUCTURE.md` - This file
- Backend uses local JSON files and ChromaDB
- All data persisted in `data/` directory

## Development
1. Run `./start.sh` for initial setup
2. Use `./start-both.sh` for development
3. Backend: http://localhost:8000
4. Frontend: http://localhost:3000
EOF

print_success "Created PROJECT_STRUCTURE.md"

# 12. Final summary and recommendations
echo ""
echo "🎉 CLEANUP COMPLETE!"
echo "==================="
echo ""

# Count removed items
REMOVED_COUNT=$(grep -c "Removing:" "$CLEANUP_LOG" 2>/dev/null || echo "0")

print_success "Removed $REMOVED_COUNT unnecessary files and directories"
print_success "Created PROJECT_STRUCTURE.md for reference"
print_success "Organized remaining scripts in scripts/ directory"

echo ""
print_status "📋 Cleanup Summary:"
echo "  ✅ Removed temporary bash scripts"
echo "  ✅ Removed backup and duplicate files"
echo "  ✅ Cleaned Python cache and artifacts"
echo "  ✅ Cleaned Node.js artifacts"
echo "  ✅ Removed OS-specific files"
echo "  ✅ Organized remaining scripts"
echo ""

print_status "📁 Current Project Structure:"
echo "  ✅ backend/ - Python FastAPI application"
echo "  ✅ frontend/ - React application"
echo "  ✅ data/ - Application data (preserved)"
echo "  ✅ scripts/ - Essential utility scripts"
echo "  ✅ Core startup scripts (start.sh, start-both.sh, etc.)"
echo ""

print_status "📜 Cleanup log saved to: $CLEANUP_LOG"

echo ""
print_status "🚀 Next Steps:"
echo "  1. Test the application: ./start-both.sh"
echo "  2. Review PROJECT_STRUCTURE.md for project overview"
echo "  3. Use scripts in scripts/ directory as needed"
echo ""

print_warning "💡 If you need any removed functionality:"
print_warning "  - Check $CLEANUP_LOG for what was removed"
print_warning "  - Essential scripts are preserved in scripts/"
print_warning "  - All core application functionality remains intact"

echo ""
print_success "🎊 Project cleanup completed successfully!"
print_success "Your journaling assistant is now clean and organized!"

# Optional: Show disk space saved
if command -v du &> /dev/null; then
    echo ""
    print_status "💾 Current project size:"
    du -sh . 2>/dev/null | cut -f1 | sed 's/^/  /'
fi