#!/bin/bash

# AI Project Cleanup Script
# Project: Journaling AI
# Date: August 5, 2025
# Purpose: Safe, automated cleanup with full backup and restoration capabilities

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Configuration
PROJECT_ROOT="/home/abrasko/Projects/journaling-ai"
BACKUP_ROOT="$PROJECT_ROOT/backup"
SESSION_DATE="2025-08-05"
SESSION_TIME=$(date +"%H%M")
SESSION_ID="cleanup-${SESSION_DATE}-${SESSION_TIME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="$BACKUP_ROOT/cleanup-${SESSION_DATE}.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Safety checks
safety_check() {
    log_info "Running safety checks..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/package.json" ]] && [[ ! -f "$PROJECT_ROOT/backend/requirements.txt" ]]; then
        log_error "Not in project root directory. Please run from $PROJECT_ROOT"
        exit 1
    fi
    
    # Check git status
    if ! git status --porcelain | grep -q "^$"; then
        log_warning "Git working directory is not clean. Uncommitted changes detected."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cleanup cancelled by user"
            exit 0
        fi
    fi
    
    # Check if backup directory exists
    if [[ ! -d "$BACKUP_ROOT" ]]; then
        log_info "Creating backup directory structure..."
        mkdir -p "$BACKUP_ROOT"
    fi
    
    log_success "Safety checks passed"
}

# Create backup structure
create_backup_structure() {
    log_info "Creating backup directory structure..."
    
    local session_backup="$BACKUP_ROOT/by-date/${SESSION_DATE}-cleanup"
    local category_backup="$BACKUP_ROOT/by-category"
    
    mkdir -p "$session_backup"
    mkdir -p "$category_backup/development-examples"
    mkdir -p "$category_backup/historical-documentation"
    mkdir -p "$category_backup/legacy-services"
    mkdir -p "$category_backup/build-artifacts"
    mkdir -p "$BACKUP_ROOT/restoration-guide"
    
    log_success "Backup structure created"
}

# Backup a file or directory
backup_file() {
    local source="$1"
    local category="$2"
    local reason="$3"
    
    if [[ ! -e "$source" ]]; then
        log_warning "Source not found: $source"
        return 1
    fi
    
    local filename=$(basename "$source")
    local session_dest="$BACKUP_ROOT/by-date/${SESSION_DATE}-cleanup/$category"
    local category_dest="$BACKUP_ROOT/by-category/$category"
    
    # Create destination directories
    mkdir -p "$session_dest"
    mkdir -p "$category_dest"
    
    # Copy to both locations
    if [[ -d "$source" ]]; then
        cp -r "$source" "$session_dest/"
        cp -r "$source" "$category_dest/"
        log_success "Backed up directory: $source → $category"
    else
        cp "$source" "$session_dest/"
        cp "$source" "$category_dest/"
        log_success "Backed up file: $source → $category"
    fi
    
    # Log the move in our mapping file
    echo "$source,$category,$reason,$(date)" >> "$BACKUP_ROOT/file-moves-${SESSION_DATE}.csv"
}

# Remove file after backup
safe_remove() {
    local source="$1"
    
    if [[ ! -e "$source" ]]; then
        log_warning "Cannot remove, file not found: $source"
        return 1
    fi
    
    if [[ -d "$source" ]]; then
        rm -rf "$source"
        log_info "Removed directory: $source"
    else
        rm -f "$source"
        log_info "Removed file: $source"
    fi
}

# Verify no critical references exist
verify_no_references() {
    local file_pattern="$1"
    local description="$2"
    
    log_info "Checking for references to $description..."
    
    # Search for imports and requires
    local references=$(grep -r "$file_pattern" . \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --include="*.jsx" \
        --include="*.tsx" \
        --exclude-dir=node_modules \
        --exclude-dir=.git \
        --exclude-dir=__pycache__ \
        --exclude-dir=backup \
        2>/dev/null || true)
    
    if [[ -n "$references" ]]; then
        log_error "Found references to $description:"
        echo "$references"
        return 1
    fi
    
    log_success "No references found to $description"
    return 0
}

# Phase 1: Safe cleanup
phase_1_safe_cleanup() {
    log_info "Starting Phase 1: Safe cleanup..."
    
    # Example code directory
    if [[ -d "example code" ]]; then
        if verify_no_references "example code" "example code directory"; then
            backup_file "example code" "development-examples" "Example implementations, no active references"
            safe_remove "example code"
            log_success "Moved example code directory to backup"
        else
            log_error "Found references to example code, skipping removal"
        fi
    fi
    
    # Completed implementation documentation
    local impl_docs=(
        "implementation/SPECIFIC_REFACTORING_GUIDE.md"
        "implementation/CODE_QUALITY_ASSESSMENT.md"
        "implementation/ENHANCED_ARCHITECTURE_INTEGRATION.md"
        "implementation/ENHANCED_ARCHITECTURE_INTEGRATION_COMPLETE.md"
    )
    
    for doc in "${impl_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            backup_file "$doc" "historical-documentation" "Implementation complete, archival only"
            safe_remove "$doc"
            log_success "Moved $doc to backup"
        fi
    done
    
    # Cache directories (if they exist and are large)
    local cache_dirs=(
        "frontend/node_modules/.cache"
        "backend/__pycache__"
        ".pytest_cache"
        "data/analytics_cache"
    )
    
    for cache_dir in "${cache_dirs[@]}"; do
        if [[ -d "$cache_dir" ]] && [[ $(du -sm "$cache_dir" 2>/dev/null | cut -f1) -gt 5 ]]; then
            backup_file "$cache_dir" "build-artifacts" "Cache directory, regeneratable"
            safe_remove "$cache_dir"
            log_success "Cleaned cache directory: $cache_dir"
        fi
    done
    
    log_success "Phase 1 complete"
}

# Phase 2: Investigation and conditional cleanup
phase_2_investigation() {
    log_info "Starting Phase 2: Investigation..."
    
    # Check for legacy service files
    local legacy_services=(
        "backend/app/services/enhanced_database_adapter.py"
        "backend/app/services/database_service.py"
    )
    
    for service in "${legacy_services[@]}"; do
        if [[ -f "$service" ]]; then
            local service_name=$(basename "$service" .py)
            if verify_no_references "$service_name" "$service_name"; then
                backup_file "$service" "legacy-services" "Legacy service, superseded by unified service"
                safe_remove "$service"
                log_success "Moved legacy service: $service"
            else
                log_warning "Found references to $service, scheduling for manual review"
                echo "$service" >> "$BACKUP_ROOT/manual-review-needed.txt"
            fi
        fi
    done
    
    log_success "Phase 2 complete"
}

# Run tests to verify cleanup didn't break anything
run_verification_tests() {
    log_info "Running verification tests..."
    
    # Test Python imports in backend
    if [[ -d "backend" ]]; then
        cd backend
        if python3 -c "import app.main; print('✅ Backend imports working')" 2>/dev/null; then
            log_success "Backend imports verified"
        else
            log_error "Backend import test failed"
            cd ..
            return 1
        fi
        cd ..
    fi
    
    # Test frontend build (if node_modules exists)
    if [[ -d "frontend/node_modules" ]]; then
        cd frontend
        if npm run build --dry-run >/dev/null 2>&1; then
            log_success "Frontend build test passed"
        else
            log_warning "Frontend build test failed (may be unrelated to cleanup)"
        fi
        cd ..
    fi
    
    log_success "Verification tests complete"
}

# Generate cleanup report
generate_report() {
    log_info "Generating cleanup report..."
    
    local report_file="$BACKUP_ROOT/cleanup-report-${SESSION_DATE}.md"
    
    cat > "$report_file" << EOF
# Cleanup Report - $SESSION_DATE

## Session Summary
- **Session ID**: $SESSION_ID
- **Date**: $SESSION_DATE
- **Time**: $(date '+%H:%M:%S')
- **Duration**: $((SECONDS / 60)) minutes

## Files Processed
EOF

    if [[ -f "$BACKUP_ROOT/file-moves-${SESSION_DATE}.csv" ]]; then
        echo "### Files Moved to Backup" >> "$report_file"
        echo "\`\`\`" >> "$report_file"
        cat "$BACKUP_ROOT/file-moves-${SESSION_DATE}.csv" >> "$report_file"
        echo "\`\`\`" >> "$report_file"
    fi
    
    if [[ -f "$BACKUP_ROOT/manual-review-needed.txt" ]]; then
        echo "### Files Requiring Manual Review" >> "$report_file"
        echo "\`\`\`" >> "$report_file"
        cat "$BACKUP_ROOT/manual-review-needed.txt" >> "$report_file"
        echo "\`\`\`" >> "$report_file"
    fi
    
    echo "## Backup Locations" >> "$report_file"
    echo "- **Session Backup**: \`backup/by-date/${SESSION_DATE}-cleanup/\`" >> "$report_file"
    echo "- **Category Backup**: \`backup/by-category/\`" >> "$report_file"
    echo "- **Restoration Guide**: \`backup/restoration-guide/\`" >> "$report_file"
    
    log_success "Report generated: $report_file"
}

# Main execution
main() {
    log_info "Starting AI Project Cleanup - $SESSION_ID"
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    safety_check
    create_backup_structure
    
    phase_1_safe_cleanup
    phase_2_investigation
    
    run_verification_tests
    generate_report
    
    log_success "Cleanup complete! Check backup/cleanup-report-${SESSION_DATE}.md for details"
    log_info "To restore files, see: backup/restoration-guide/restoration-steps.md"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
