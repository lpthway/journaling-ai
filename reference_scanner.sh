#!/bin/bash

# Reference Scanner for AI Project Cleanup
# Analyzes file dependencies and references to ensure safe cleanup

set -e

PROJECT_ROOT="/home/abrasko/Projects/journaling-ai"
ANALYSIS_OUTPUT="$PROJECT_ROOT/reference_analysis.json"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%H:%M:%S')] $1"
}

# Scan for Python imports
scan_python_imports() {
    log "Scanning Python imports..."
    
    find . -name "*.py" -not -path "./backup/*" -not -path "./.git/*" -not -path "./__pycache__/*" | while read file; do
        grep -n "^import\|^from.*import" "$file" 2>/dev/null | sed "s|^|$file:|" || true
    done > /tmp/python_imports.txt
    
    log "Found $(wc -l < /tmp/python_imports.txt) Python import statements"
}

# Scan for JavaScript/TypeScript imports
scan_js_imports() {
    log "Scanning JavaScript/TypeScript imports..."
    
    find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | grep -v node_modules | grep -v backup | while read file; do
        grep -n "import.*from\|require(" "$file" 2>/dev/null | sed "s|^|$file:|" || true
    done > /tmp/js_imports.txt
    
    log "Found $(wc -l < /tmp/js_imports.txt) JavaScript import statements"
}

# Scan for file references in configuration
scan_config_references() {
    log "Scanning configuration file references..."
    
    # Check package.json files
    find . -name "package.json" -not -path "./backup/*" | while read file; do
        grep -n "\"main\"\|\"entry\"\|\"src\"\|\"files\"" "$file" 2>/dev/null | sed "s|^|$file:|" || true
    done > /tmp/config_refs.txt
    
    # Check Docker files
    find . -name "Dockerfile" -o -name "docker-compose.yml" -not -path "./backup/*" | while read file; do
        grep -n "COPY\|ADD\|WORKDIR" "$file" 2>/dev/null | sed "s|^|$file:|" || true
    done >> /tmp/config_refs.txt
    
    # Check Python setup/requirements
    find . -name "requirements.txt" -o -name "setup.py" -o -name "pyproject.toml" -not -path "./backup/*" | while read file; do
        cat "$file" | sed "s|^|$file:1:|" || true
    done >> /tmp/config_refs.txt
    
    log "Found $(wc -l < /tmp/config_refs.txt) configuration references"
}

# Scan for asset references
scan_asset_references() {
    log "Scanning asset references..."
    
    # HTML/CSS references
    find . -name "*.html" -o -name "*.css" -o -name "*.scss" | grep -v node_modules | grep -v backup | while read file; do
        grep -n "src=\|href=\|url(\|@import" "$file" 2>/dev/null | sed "s|^|$file:|" || true
    done > /tmp/asset_refs.txt
    
    log "Found $(wc -l < /tmp/asset_refs.txt) asset references"
}

# Check Git activity for files
check_git_activity() {
    log "Checking Git activity..."
    
    # Files modified in last 6 months
    git log --since="6 months ago" --name-only --pretty=format: | sort | uniq > /tmp/recent_files.txt
    
    # Files not modified in last year
    git log --until="1 year ago" --name-only --pretty=format: | sort | uniq > /tmp/old_files.txt
    
    log "Recent files (6 months): $(wc -l < /tmp/recent_files.txt)"
    log "Old files (>1 year): $(wc -l < /tmp/old_files.txt)"
}

# Analyze specific file for references
analyze_file_references() {
    local file="$1"
    local basename_file=$(basename "$file")
    local dirname_file=$(dirname "$file")
    
    echo "{"
    echo "  \"file\": \"$file\","
    echo "  \"references\": ["
    
    # Search for direct filename references
    local refs=$(grep -r "$basename_file" . \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --include="*.jsx" \
        --include="*.tsx" \
        --include="*.json" \
        --include="*.yml" \
        --include="*.yaml" \
        --include="*.md" \
        --exclude-dir=node_modules \
        --exclude-dir=.git \
        --exclude-dir=__pycache__ \
        --exclude-dir=backup \
        2>/dev/null | head -20 || true)
    
    if [[ -n "$refs" ]]; then
        echo "$refs" | while IFS=: read -r ref_file ref_line ref_content; do
            echo "    {"
            echo "      \"file\": \"$ref_file\","
            echo "      \"line\": $ref_line,"
            echo "      \"content\": \"$(echo "$ref_content" | sed 's/"/\\"/g' | tr -d '\n')\""
            echo "    },"
        done | sed '$ s/,$//'
    fi
    
    echo "  ],"
    echo "  \"import_count\": $(echo "$refs" | wc -l),"
    echo "  \"is_safe_to_move\": $([ -z "$refs" ] && echo "true" || echo "false")"
    echo "}"
}

# Generate reference analysis report
generate_analysis_report() {
    log "Generating reference analysis report..."
    
    cat > "$ANALYSIS_OUTPUT" << 'EOF'
{
  "analysis_metadata": {
    "timestamp": "$(date -Iseconds)",
    "project_root": "$PROJECT_ROOT",
    "scan_type": "comprehensive_reference_analysis"
  },
  "file_categories": {
EOF

    # Analyze example code files
    echo '    "example_code": [' >> "$ANALYSIS_OUTPUT"
    if [[ -d "example code" ]]; then
        find "example code" -type f | while read file; do
            analyze_file_references "$file" >> "$ANALYSIS_OUTPUT"
            echo "," >> "$ANALYSIS_OUTPUT"
        done
        # Remove last comma
        sed -i '$ s/,$//' "$ANALYSIS_OUTPUT"
    fi
    echo '    ],' >> "$ANALYSIS_OUTPUT"
    
    # Analyze implementation docs
    echo '    "implementation_docs": [' >> "$ANALYSIS_OUTPUT"
    find implementation -name "*.md" -type f 2>/dev/null | while read file; do
        analyze_file_references "$file" >> "$ANALYSIS_OUTPUT"
        echo "," >> "$ANALYSIS_OUTPUT"
    done 2>/dev/null || true
    sed -i '$ s/,$//' "$ANALYSIS_OUTPUT" 2>/dev/null || true
    echo '    ],' >> "$ANALYSIS_OUTPUT"
    
    # Analyze backup directory
    echo '    "backup_files": [' >> "$ANALYSIS_OUTPUT"
    find backup -type f 2>/dev/null | head -10 | while read file; do
        analyze_file_references "$file" >> "$ANALYSIS_OUTPUT"
        echo "," >> "$ANALYSIS_OUTPUT"
    done 2>/dev/null || true
    sed -i '$ s/,$//' "$ANALYSIS_OUTPUT" 2>/dev/null || true
    echo '    ]' >> "$ANALYSIS_OUTPUT"
    
    cat >> "$ANALYSIS_OUTPUT" << 'EOF'
  },
  "summary": {
    "total_python_imports": $(wc -l < /tmp/python_imports.txt 2>/dev/null || echo 0),
    "total_js_imports": $(wc -l < /tmp/js_imports.txt 2>/dev/null || echo 0),
    "total_config_refs": $(wc -l < /tmp/config_refs.txt 2>/dev/null || echo 0),
    "total_asset_refs": $(wc -l < /tmp/asset_refs.txt 2>/dev/null || echo 0),
    "recent_active_files": $(wc -l < /tmp/recent_files.txt 2>/dev/null || echo 0)
  }
}
EOF
    
    # Process the template variables
    envsubst < "$ANALYSIS_OUTPUT" > "${ANALYSIS_OUTPUT}.tmp"
    mv "${ANALYSIS_OUTPUT}.tmp" "$ANALYSIS_OUTPUT"
    
    log "Analysis report generated: $ANALYSIS_OUTPUT"
}

# Check specific file safety
check_file_safety() {
    local file="$1"
    
    if [[ ! -e "$file" ]]; then
        echo -e "${RED}File not found: $file${NC}"
        return 1
    fi
    
    local basename_file=$(basename "$file")
    local refs=$(grep -r "$basename_file" . \
        --include="*.py" \
        --include="*.js" \
        --include="*.ts" \
        --exclude-dir=node_modules \
        --exclude-dir=.git \
        --exclude-dir=__pycache__ \
        --exclude-dir=backup \
        2>/dev/null || true)
    
    if [[ -z "$refs" ]]; then
        echo -e "${GREEN}✅ SAFE: No references found to $file${NC}"
        return 0
    else
        echo -e "${RED}❌ UNSAFE: Found references to $file:${NC}"
        echo "$refs" | head -5
        if [[ $(echo "$refs" | wc -l) -gt 5 ]]; then
            echo "... and $(( $(echo "$refs" | wc -l) - 5 )) more"
        fi
        return 1
    fi
}

# Main function
main() {
    cd "$PROJECT_ROOT"
    
    log "Starting comprehensive reference analysis..."
    
    scan_python_imports
    scan_js_imports  
    scan_config_references
    scan_asset_references
    check_git_activity
    
    generate_analysis_report
    
    log "Analysis complete!"
    log "Results saved to: $ANALYSIS_OUTPUT"
    
    # Quick safety check for key directories
    echo
    log "Quick safety assessment:"
    check_file_safety "example code"
    check_file_safety "implementation/SPECIFIC_REFACTORING_GUIDE.md"
    check_file_safety "backup/enhanced_database_adapter.py"
    
    # Cleanup temp files
    rm -f /tmp/python_imports.txt /tmp/js_imports.txt /tmp/config_refs.txt /tmp/asset_refs.txt /tmp/recent_files.txt /tmp/old_files.txt
}

# Run if called directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
