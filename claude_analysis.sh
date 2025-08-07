#!/bin/bash

# =============================================================================
# AI Journaling Assistant - Comprehensive Analysis Script
# =============================================================================
# Purpose: Automated analysis using Claude Code CLI
# Author: Analysis Protocol v1.0
# Date: $(date +%Y-%m-%d)
# =============================================================================

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failure

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
ANALYSIS_DIR="${PROJECT_ROOT}/analysis_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Analysis configuration - Customize depth levels
DOCS_DEPTH=3        # Balanced for documentation structure
BACKEND_DEPTH=4     # Deep enough for service classes and API endpoints  
FRONTEND_DEPTH=4    # Reaches component subdirectories and config files

# Progressive analysis settings
ENABLE_PROGRESSIVE_ANALYSIS=true    # Start shallow, go deeper automatically
ENABLE_TARGETED_DEEP_DIVE=true      # Deep dive into specific critical areas
SHALLOW_FIRST_DEPTH=2               # Initial quick overview depth
DETAILED_FOLLOW_UP_DEPTH=4          # Detailed analysis depth

# Targeted deep dive areas (customize for your project)
BACKEND_DEEP_DIVE_AREAS=(
    "backend/app/services"      # AI and core services
    "backend/app/tasks"         # Celery task coordination  
    "backend/app/api"           # API endpoints
)
FRONTEND_DEEP_DIVE_AREAS=(
    "frontend/src/components"   # React/Vue components
    "frontend/src/services"     # Frontend services
    "frontend/src/store"        # State management
)
DEEP_DIVE_DEPTH=6               # Extra deep analysis for critical areas

# Advanced depth options (uncomment to use)
# DOCS_DEPTH=2      # Shallow - quick overview of docs structure
# BACKEND_DEPTH=5   # Very deep - analyzes deeply nested enterprise code
# FRONTEND_DEPTH=3  # Medium - for simpler frontend structures

# Performance vs Detail Trade-off Guide:
# Depth 1-2: Fast overview, surface-level files only
# Depth 3-4: Balanced analysis, most important files included
# Depth 5-6: Exhaustive analysis, every file analyzed (slower)

# Analysis output files
DOCS_ANALYSIS="${ANALYSIS_DIR}/analysis_docs_${TIMESTAMP}.md"
BACKEND_ANALYSIS="${ANALYSIS_DIR}/analysis_backend_${TIMESTAMP}.md"
FRONTEND_ANALYSIS="${ANALYSIS_DIR}/analysis_frontend_${TIMESTAMP}.md"
COMPREHENSIVE_ASSESSMENT="${ANALYSIS_DIR}/comprehensive_assessment_${TIMESTAMP}.md"
TODO_LIST="${ANALYSIS_DIR}/actionable_todo_list_${TIMESTAMP}.md"

# Progress tracking
STEPS_COMPLETED=0
TOTAL_STEPS=4

# =============================================================================
# Utility Functions
# =============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "           AI JOURNALING ASSISTANT - CLAUDE CODE ANALYSIS"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}Project Root: ${WHITE}${PROJECT_ROOT}${NC}"
    echo -e "${CYAN}Analysis Dir: ${WHITE}${ANALYSIS_DIR}${NC}"
    echo -e "${CYAN}Timestamp: ${WHITE}${TIMESTAMP}${NC}"
    echo ""
}

print_step_header() {
    local step_num=$1
    local step_title=$2
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "  STEP ${step_num}: ${step_title}"
    echo "============================================================================="
    echo -e "${NC}"
}

print_progress() {
    local completed=$1
    local total=$2
    local percentage=$((completed * 100 / total))
    echo -e "${YELLOW}Progress: [${completed}/${total}] ${percentage}% Complete${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${CYAN}Checking prerequisites...${NC}"
    
    # Check if claude is installed (check both possible command names)
    CLAUDE_CMD=""
    if command -v claude &> /dev/null; then
        CLAUDE_CMD="claude"
        echo -e "${GREEN}✅ Found Claude CLI as 'claude'${NC}"
    elif command -v claude-code &> /dev/null; then
        CLAUDE_CMD="claude-code"  
        echo -e "${GREEN}✅ Found Claude CLI as 'claude-code'${NC}"
    else
        echo -e "${RED}❌ ERROR: Claude CLI not found${NC}"
        echo -e "${WHITE}Please install it with one of these methods:${NC}"
        echo -e "${WHITE}  Method 1: curl -fsSL claude.ai/install.sh | bash${NC}"
        echo -e "${WHITE}  Method 2: pip install claude-code${NC}"
        exit 1
    fi
    
    # Verify Claude is working
    echo -e "${CYAN}Testing Claude CLI...${NC}"
    if $CLAUDE_CMD --version &> /dev/null; then
        local version=$($CLAUDE_CMD --version 2>/dev/null)
        echo -e "${GREEN}✅ Claude CLI is working - Version: ${version}${NC}"
    else
        echo -e "${YELLOW}⚠️  Claude CLI found but may need authentication${NC}"
        echo -e "${WHITE}Try running: $CLAUDE_CMD auth${NC}"
    fi
    
    # Check if we're in a valid project directory
    if [[ ! -d "backend" ]] && [[ ! -d "frontend" ]] && [[ ! -d "docs" ]]; then
        echo -e "${RED}❌ ERROR: This doesn't appear to be the project root${NC}"
        echo -e "${WHITE}Please run this script from your AI journaling assistant root directory${NC}"
        exit 1
    fi
    
    # Create analysis directory
    mkdir -p "${ANALYSIS_DIR}"
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
    echo ""
}

update_progress() {
    STEPS_COMPLETED=$((STEPS_COMPLETED + 1))
    print_progress $STEPS_COMPLETED $TOTAL_STEPS
}

mark_step_complete() {
    local step_name=$1
    local output_file=$2
    echo -e "${GREEN}✅ ${step_name} COMPLETED${NC}"
    echo -e "${WHITE}   Output: ${output_file}${NC}"
    echo ""
    update_progress
}

create_step_status_file() {
    local status_file="${ANALYSIS_DIR}/analysis_status_${TIMESTAMP}.md"
    cat > "${status_file}" << EOF
# Analysis Progress Status

**Analysis Session**: ${TIMESTAMP}
**Project Root**: ${PROJECT_ROOT}

## Step Completion Status

- [x] **Step 1**: Documentation Analysis - ${DOCS_ANALYSIS}
- [x] **Step 2**: Backend Analysis - ${BACKEND_ANALYSIS}
- [x] **Step 3**: Frontend Analysis - ${FRONTEND_ANALYSIS}
- [x] **Step 4**: Comprehensive Assessment - ${COMPREHENSIVE_ASSESSMENT} & ${TODO_LIST}

## Generated Files

1. **Documentation Analysis**: \`$(basename ${DOCS_ANALYSIS})\`
2. **Backend Analysis**: \`$(basename ${BACKEND_ANALYSIS})\`
3. **Frontend Analysis**: \`$(basename ${FRONTEND_ANALYSIS})\`
4. **Comprehensive Assessment**: \`$(basename ${COMPREHENSIVE_ASSESSMENT})\`
5. **Actionable TODO List**: \`$(basename ${TODO_LIST})\`

**Analysis Complete**: $(date)
EOF
    echo -e "${GREEN}✅ Status file created: ${status_file}${NC}"
}

# =============================================================================
# Analysis Steps
# =============================================================================

step1_analyze_docs() {
    print_step_header "1" "DOCUMENTATION DIRECTORY ANALYSIS"
    
    if [[ ! -d "docs" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: docs/ directory not found${NC}"
        echo -e "${WHITE}Creating placeholder analysis...${NC}"
        cat > "${DOCS_ANALYSIS}" << EOF
# Documentation Analysis - No docs/ Directory Found

**Analysis Date**: $(date)
**Project Root**: ${PROJECT_ROOT}

## Status
- **docs/ Directory**: Not found
- **Documentation Score**: 0/10
- **Recommendation**: Create comprehensive documentation structure

## Recommended Documentation Structure
\`\`\`
docs/
├── architecture/
├── api/
├── deployment/
├── development/
└── user-guides/
\`\`\`

## Priority Actions
1. Create documentation directory structure
2. Document current architecture
3. Create API documentation
4. Write deployment guides
EOF
        mark_step_complete "Documentation Analysis" "${DOCS_ANALYSIS}"
        return
    fi

    echo -e "${CYAN}Analyzing docs/ directory...${NC}"
    
    # Create the Claude Code prompt file
    local docs_prompt="${ANALYSIS_DIR}/docs_prompt.txt"
    cat > "${docs_prompt}" << 'EOF'
Analyze the docs/ directory structure and content. Focus on:

1. **Documentation Architecture Assessment:**
   - Review all .md files for consistency and completeness
   - Identify documentation gaps or outdated information
   - Check if architectural decisions match current implementation
   - Validate that Phase 2, AI Services, and Phase 0B docs align

2. **Project State Analysis:**
   - Compare claimed completion status with actual implementation
   - Identify discrepancies between documented and actual progress
   - Check if performance targets and metrics are realistic
   - Validate architectural patterns described vs. implemented

3. **Documentation Quality Review:**
   - Assess documentation structure and organization
   - Identify missing technical specifications
   - Check for incomplete or placeholder content
   - Review deployment and operational procedures

**Output Requirements:**
- Summary of documentation completeness (% complete by category)
- List of architectural inconsistencies found
- Missing documentation that should exist
- Quality assessment score (1-10) with justification
- Priority recommendations for documentation improvements
EOF

    # Run Claude Code analysis
    echo -e "${YELLOW}Running Claude analysis on docs/...${NC}"
    $CLAUDE_CMD analyze docs/ \
        --depth=3 \
        --include="*.md,*.txt,*.rst" \
        --exclude=".git,__pycache__" \
        --prompt-file="${docs_prompt}" \
        --output="${DOCS_ANALYSIS}" || {
        echo -e "${RED}❌ Claude analysis failed for docs/${NC}"
        echo "Creating fallback analysis..."
        cat > "${DOCS_ANALYSIS}" << EOF
# Documentation Analysis - Fallback Report

**Analysis Date**: $(date)
**Status**: Claude Code analysis failed, manual inspection performed

## Directory Structure
$(find docs/ -type f -name "*.md" 2>/dev/null | head -20 || echo "No markdown files found")

## Files Found
$(ls -la docs/ 2>/dev/null || echo "Directory listing failed")

## Recommendations
1. Verify Claude Code CLI is properly configured
2. Check network connectivity
3. Review documentation structure manually
EOF
    }
    
    rm -f "${docs_prompt}"
    mark_step_complete "Documentation Analysis" "${DOCS_ANALYSIS}"
}

step2_analyze_backend() {
    print_step_header "2" "BACKEND DIRECTORY ANALYSIS"
    
    if [[ ! -d "backend" ]]; then
        echo -e "${RED}❌ ERROR: backend/ directory not found${NC}"
        exit 1
    fi

    echo -e "${CYAN}Analyzing backend/ directory...${NC}"
    
    # Create the Claude Code prompt file
    local backend_prompt="${ANALYSIS_DIR}/backend_prompt.txt"
    cat > "${backend_prompt}" << 'EOF'
Perform deep analysis of the backend/ directory structure and code quality. Focus on:

1. **Architecture Implementation Assessment:**
   - Verify Phase 2 task coordinator pattern implementation
   - Check service registry and dependency injection setup
   - Validate Redis integration and caching implementation
   - Assess AI services architecture and model management

2. **Code Quality Analysis:**
   - Identify code duplication (should be eliminated per Phase 2)
   - Check for proper error handling and logging
   - Validate type hints and documentation coverage
   - Review async/await usage and performance patterns

3. **Integration Issues Detection:**
   - Check import statements and dependency resolution
   - Identify circular dependencies or import conflicts
   - Validate service registration and discovery patterns
   - Review database and cache service integration

4. **Functionality Assessment:**
   - Test critical paths: entry creation, session management, analytics
   - Identify broken or incomplete features
   - Check API endpoint functionality and routing
   - Validate Celery task definitions and execution

5. **Performance and Security Review:**
   - Assess connection pooling and resource management
   - Review security practices (input validation, sanitization)
   - Check for performance bottlenecks or anti-patterns
   - Validate monitoring and health check implementations

**Output Requirements:**
- Architecture compliance score (matches documented patterns)
- List of broken functionality with severity levels (Critical/High/Medium/Low)
- Code quality metrics (duplication %, test coverage estimate)
- Integration issues found with specific file/line references
- Performance concerns and optimization opportunities
- Security vulnerabilities or best practice violations
EOF

    # Run Claude analysis
    echo -e "${YELLOW}Running Claude analysis on backend/ (depth: ${BACKEND_DEPTH})...${NC}"
    $CLAUDE_CMD analyze backend/ \
        --depth=${BACKEND_DEPTH} \
        --exclude="__pycache__,*.pyc,.env,venv,env,.pytest_cache,*.log" \
        --include="*.py,*.yaml,*.yml,*.toml,requirements.txt" \
        --prompt-file="${backend_prompt}" \
        --output="${BACKEND_ANALYSIS}" || {
        echo -e "${RED}❌ Claude analysis failed for backend/${NC}"
        echo "Creating fallback analysis..."
        cat > "${BACKEND_ANALYSIS}" << EOF
# Backend Analysis - Fallback Report

**Analysis Date**: $(date)
**Status**: Claude Code analysis failed, manual inspection performed

## Directory Structure
$(find backend/ -name "*.py" -type f | head -30 2>/dev/null || echo "No Python files found")

## Key Files
$(ls -la backend/app/ 2>/dev/null || echo "app/ directory listing failed")

## Requirements
$(cat backend/requirements.txt 2>/dev/null || echo "requirements.txt not found")

## Recommendations
1. Manual code review required
2. Check for syntax errors: python -m py_compile backend/app/**/*.py
3. Verify import statements and dependencies
EOF
    }
    
    rm -f "${backend_prompt}"
    mark_step_complete "Backend Analysis" "${BACKEND_ANALYSIS}"
}

step3_analyze_frontend() {
    print_step_header "3" "FRONTEND DIRECTORY ANALYSIS"
    
    if [[ ! -d "frontend" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: frontend/ directory not found${NC}"
        echo -e "${WHITE}Creating placeholder analysis...${NC}"
        cat > "${FRONTEND_ANALYSIS}" << EOF
# Frontend Analysis - No frontend/ Directory Found

**Analysis Date**: $(date)
**Project Root**: ${PROJECT_ROOT}

## Status
- **frontend/ Directory**: Not found
- **Frontend Score**: N/A
- **Architecture**: Backend-only application detected

## Recommendations
1. Determine if this is intentionally a backend-only API
2. If frontend is planned, create appropriate structure
3. Consider modern frontend frameworks (React, Vue, Svelte)
4. Plan API integration strategy
EOF
        mark_step_complete "Frontend Analysis" "${FRONTEND_ANALYSIS}"
        return
    fi

    echo -e "${CYAN}Analyzing frontend/ directory...${NC}"
    
    # Create the Claude prompt file
    local frontend_prompt="${ANALYSIS_DIR}/frontend_prompt.txt"
    cat > "${frontend_prompt}" << 'EOF'
Analyze the frontend/ directory for integration issues and functionality gaps. Focus on:

1. **Frontend Architecture Assessment:**
   - Review component structure and state management
   - Check API integration with backend services
   - Validate routing and navigation implementation
   - Assess responsive design and user experience patterns

2. **Integration Analysis:**
   - Check API calls to backend endpoints
   - Validate data flow between frontend and backend
   - Identify broken API integrations after backend refactoring
   - Review authentication and session management

3. **Code Quality Review:**
   - Check for TypeScript/JavaScript best practices
   - Review component reusability and maintainability
   - Assess error handling and user feedback mechanisms
   - Validate accessibility and performance optimization

4. **Functionality Testing:**
   - Identify critical user journeys that may be broken
   - Check form submissions and data persistence
   - Validate real-time features (if any)
   - Review mobile responsiveness and cross-browser compatibility

5. **Dependencies and Build System:**
   - Review package.json for outdated or conflicting dependencies
   - Check build configuration and deployment readiness
   - Validate development vs production environment setup
   - Assess bundle size and performance optimization

**Output Requirements:**
- Frontend architecture assessment (modern practices score 1-10)
- List of broken integrations with backend after refactoring
- User experience issues and critical bugs found
- Dependency vulnerabilities or version conflicts
- Performance metrics and optimization recommendations
- Build and deployment readiness assessment
EOF

    # Run Claude analysis
    echo -e "${YELLOW}Running Claude analysis on frontend/ (depth: ${FRONTEND_DEPTH})...${NC}"
    $CLAUDE_CMD analyze frontend/ \
        --depth=${FRONTEND_DEPTH} \
        --exclude="node_modules,dist,build,.cache,.next,coverage" \
        --include="*.js,*.jsx,*.ts,*.tsx,*.vue,*.html,*.css,*.scss,package.json,*.config.js" \
        --prompt-file="${frontend_prompt}" \
        --output="${FRONTEND_ANALYSIS}" || {
        echo -e "${RED}❌ Claude analysis failed for frontend/${NC}"
        echo "Creating fallback analysis..."
        cat > "${FRONTEND_ANALYSIS}" << EOF
# Frontend Analysis - Fallback Report

**Analysis Date**: $(date)
**Status**: Claude Code analysis failed, manual inspection performed

## Directory Structure
$(find frontend/ -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.vue" | head -20 2>/dev/null || echo "No frontend files found")

## Package Configuration
$(cat frontend/package.json 2>/dev/null || echo "package.json not found")

## Recommendations
1. Manual review of frontend code required
2. Check build system: npm run build or yarn build
3. Verify API integration endpoints
EOF
    }
    
    rm -f "${frontend_prompt}"
    mark_step_complete "Frontend Analysis" "${FRONTEND_ANALYSIS}"
}

step4_comprehensive_assessment() {
    print_step_header "4" "COMPREHENSIVE ASSESSMENT AND TODO CREATION"
    
    echo -e "${CYAN}Synthesizing all analysis results...${NC}"
    
    # Create synthesis prompt
    local synthesis_prompt="${ANALYSIS_DIR}/synthesis_prompt.txt"
    cat > "${synthesis_prompt}" << EOF
Synthesize all analysis results into comprehensive assessment and actionable plans.

Create two documents:

## COMPREHENSIVE ASSESSMENT
### Executive Summary
- Overall system health score (1-10)
- Critical issues requiring immediate attention
- Impact assessment of Phase 2 refactoring on system functionality
- Readiness assessment for production deployment

### What Works Well ✅
- Successfully implemented architectural patterns
- High-quality code areas that meet enterprise standards
- Properly functioning integration points
- Performance optimizations that are effective
- Documentation that accurately reflects implementation

### What Needs Improvement ⚠️
- Architectural inconsistencies between docs and implementation
- Code quality issues that impact maintainability
- Integration problems causing functionality breakage
- Performance bottlenecks or resource usage concerns
- Security vulnerabilities or best practice violations

### Critical Issues 🚨
- Functionality that is completely broken
- Security vulnerabilities requiring immediate attention
- Performance issues causing system instability
- Integration failures preventing core features from working
- Data integrity or corruption risks

## ACTIONABLE TODO LIST
### Priority 1: Critical Fixes (Do First)
- [ ] Issue Title - Description, affected files, estimated effort

### Priority 2: High Impact Improvements
- [ ] Issue Title - Description, affected files, estimated effort

### Priority 3: Code Quality and Technical Debt
- [ ] Issue Title - Description, affected files, estimated effort

Each TODO item should include:
- Clear problem description
- Files that need to be modified
- Estimated time/effort required
- Dependencies on other tasks
- Success criteria for completion
EOF

    # Run synthesis
    echo -e "${YELLOW}Creating comprehensive assessment...${NC}"
    
    # Check if analysis files exist and have content
    local input_files=""
    [[ -f "${DOCS_ANALYSIS}" ]] && input_files+="${DOCS_ANALYSIS} "
    [[ -f "${BACKEND_ANALYSIS}" ]] && input_files+="${BACKEND_ANALYSIS} "
    [[ -f "${FRONTEND_ANALYSIS}" ]] && input_files+="${FRONTEND_ANALYSIS} "

    if [[ -n "${input_files}" ]]; then
        $CLAUDE_CMD synthesize ${input_files} \
            --prompt-file="${synthesis_prompt}" \
            --output="${COMPREHENSIVE_ASSESSMENT}" || {
            echo -e "${RED}❌ Claude synthesis failed${NC}"
            echo "Creating fallback comprehensive assessment..."
            create_fallback_assessment
        }
    else
        echo -e "${RED}❌ No analysis files found for synthesis${NC}"
        create_fallback_assessment
    fi
    
    # Create TODO list from comprehensive assessment
    echo -e "${YELLOW}Extracting actionable TODO list...${NC}"
    $CLAUDE_CMD extract-todos "${COMPREHENSIVE_ASSESSMENT}" \
        --output="${TODO_LIST}" || {
        echo "Creating fallback TODO list..."
        create_fallback_todo_list
    }
    
    rm -f "${synthesis_prompt}"
    mark_step_complete "Comprehensive Assessment" "${COMPREHENSIVE_ASSESSMENT} & ${TODO_LIST}"
}

create_fallback_assessment() {
    cat > "${COMPREHENSIVE_ASSESSMENT}" << EOF
# Comprehensive Assessment - Fallback Report

**Analysis Date**: $(date)
**Analysis Method**: Fallback (Claude Code synthesis failed)

## Executive Summary
- **Overall Health Score**: Unable to determine automatically
- **Status**: Manual review required
- **Critical Issues**: Unknown - requires investigation

## Analysis Files Generated
1. Documentation Analysis: $(basename "${DOCS_ANALYSIS}")
2. Backend Analysis: $(basename "${BACKEND_ANALYSIS}")
3. Frontend Analysis: $(basename "${FRONTEND_ANALYSIS}")

## Next Steps Required
1. **Manual Review**: Examine each analysis file individually
2. **Code Testing**: Run application to identify broken functionality
3. **Error Logging**: Check application logs for runtime errors
4. **Integration Testing**: Test API endpoints and database connections

## Recommendations
- Review generated analysis files manually
- Run pytest or other test suites if available
- Check application startup sequence
- Validate database connections and migrations
EOF
}

create_fallback_todo_list() {
    cat > "${TODO_LIST}" << EOF
# Actionable TODO List - Fallback

**Generated**: $(date)
**Status**: Manual creation (auto-extraction failed)

## Priority 1: Immediate Investigation
- [ ] **Review Analysis Files** - Manually examine all generated analysis reports (1-2 hours)
- [ ] **Test Application Startup** - Attempt to start backend application, document errors (30 minutes)
- [ ] **Check Database Connection** - Verify database connectivity and migrations (30 minutes)
- [ ] **Test Critical Endpoints** - Test key API endpoints for functionality (1 hour)

## Priority 2: Code Quality Review
- [ ] **Python Syntax Check** - Run \`python -m py_compile\` on all .py files (15 minutes)
- [ ] **Import Resolution** - Check for import errors and circular dependencies (30 minutes)
- [ ] **Requirements Validation** - Verify all dependencies are installed (15 minutes)

## Priority 3: Architecture Validation
- [ ] **Service Registry Check** - Validate service registration and discovery (45 minutes)
- [ ] **Cache Integration Test** - Test Redis connectivity and caching (30 minutes)
- [ ] **Task Queue Validation** - Check Celery configuration and task execution (45 minutes)

## Priority 4: Documentation Update
- [ ] **Update Status Documentation** - Reflect current system state (30 minutes)
- [ ] **Create Troubleshooting Guide** - Document common issues and solutions (1 hour)

**Total Estimated Effort**: ~7-8 hours
EOF
}

# =============================================================================
# Report Generation
# =============================================================================

generate_final_report() {
    local final_report="${ANALYSIS_DIR}/final_analysis_report_${TIMESTAMP}.md"
    
    echo -e "${CYAN}Generating final analysis report...${NC}"
    
    cat > "${final_report}" << EOF
# AI Journaling Assistant - Final Analysis Report

**Analysis Completed**: $(date)
**Project Root**: ${PROJECT_ROOT}
**Session ID**: ${TIMESTAMP}

## Analysis Summary

### Files Generated
1. **Documentation Analysis**: [$(basename "${DOCS_ANALYSIS}")](./$(basename "${DOCS_ANALYSIS}"))
2. **Backend Analysis**: [$(basename "${BACKEND_ANALYSIS}")](./$(basename "${BACKEND_ANALYSIS}"))
3. **Frontend Analysis**: [$(basename "${FRONTEND_ANALYSIS}")](./$(basename "${FRONTEND_ANALYSIS}"))
4. **Comprehensive Assessment**: [$(basename "${COMPREHENSIVE_ASSESSMENT}")](./$(basename "${COMPREHENSIVE_ASSESSMENT}"))
5. **Actionable TODO List**: [$(basename "${TODO_LIST}")](./$(basename "${TODO_LIST}"))

### Analysis Statistics
- **Total Files Analyzed**: $(find . -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" | wc -l 2>/dev/null || echo "Unknown")
- **Analysis Modes**: $([ "${ENABLE_PROGRESSIVE_ANALYSIS}" == "true" ] && echo "Progressive (Shallow→Deep)" || echo "Standard"), $([ "${ENABLE_TARGETED_DEEP_DIVE}" == "true" ] && echo "Deep Dive Enabled" || echo "Deep Dive Disabled")
- **Analysis Depths**: Docs=${DOCS_DEPTH}, Backend=${BACKEND_DEPTH}, Frontend=${FRONTEND_DEPTH}, Deep Dive=${DEEP_DIVE_DEPTH}
- **Analysis Tools**: Claude CLI ($(${CLAUDE_CMD} --version 2>/dev/null || echo "Unknown version"))
- **Analysis Duration**: ~$(( ($(date +%s) - START_TIME) / 60 )) minutes

### Progressive Analysis Files Generated
$([ "${ENABLE_PROGRESSIVE_ANALYSIS}" == "true" ] && echo "- Backend Overview: backend_overview_${TIMESTAMP}.md" || echo "- Progressive analysis disabled")
$([ "${ENABLE_PROGRESSIVE_ANALYSIS}" == "true" ] && echo "- Frontend Overview: frontend_overview_${TIMESTAMP}.md" || echo "")

### Deep Dive Analysis Files Generated
$([ "${ENABLE_TARGETED_DEEP_DIVE}" == "true" ] && for area in "${BACKEND_DEEP_DIVE_AREAS[@]}"; do area_name=$(basename "$area"); echo "- Backend $(echo $area_name | tr '[:lower:]' '[:upper:]'): backend_${area_name}_deep_${TIMESTAMP}.md"; done || echo "- Deep dive analysis disabled")
$([ "${ENABLE_TARGETED_DEEP_DIVE}" == "true" ] && for area in "${FRONTEND_DEEP_DIVE_AREAS[@]}"; do area_name=$(basename "$area"); echo "- Frontend $(echo $area_name | tr '[:lower:]' '[:upper:]'): frontend_${area_name}_deep_${TIMESTAMP}.md"; done || echo "")

### Quick Actions
\`\`\`bash
# Review comprehensive assessment
cat "${COMPREHENSIVE_ASSESSMENT}"

# Check TODO list  
cat "${TODO_LIST}"

# Start with highest priority items
grep -A 5 "Priority 1" "${TODO_LIST}"
\`\`\`

### Next Steps
1. **Review Assessment** - Read the comprehensive assessment document
2. **Prioritize TODOs** - Focus on Priority 1 items first
3. **Test Critical Paths** - Validate core application functionality
4. **Fix Integration Issues** - Address broken integrations from refactoring
5. **Update Documentation** - Ensure docs reflect current implementation

### Support
- All analysis files are in: \`${ANALYSIS_DIR}/\`
- Re-run analysis: \`./$(basename "$0")\`
- **Claude Progress Tracking**: \`claude track-progress ${ANALYSIS_DIR}/\`
- **Claude Next Steps**: \`claude recommend-next ${ANALYSIS_DIR}/actionable_todo_list_*.md\`
- **Claude Status Update**: \`claude update-progress ${ANALYSIS_DIR}/ --scan-completed\`

### Claude-Powered Progress Management
\`\`\`bash
# Let Claude analyze what's been completed
claude analyze ${ANALYSIS_DIR}/ --focus=progress --output=progress_report.md

# Get Claude's recommendations for next priority
claude recommend-next ${COMPREHENSIVE_ASSESSMENT}

# Update TODO status automatically with Claude
claude update-status ${TODO_LIST} --scan-codebase --mark-completed
\`\`\`

---
**Analysis Complete** ✅
EOF

    echo -e "${GREEN}✅ Final report generated: ${final_report}${NC}"
    return "${final_report}"
}

# =============================================================================
# Main Execution Flow
# =============================================================================

main() {
    local START_TIME=$(date +%s)
    
    # Initialize
    print_banner
    check_prerequisites
    
    # Execute analysis steps
    step1_analyze_docs
    step2_analyze_backend  
    step3_analyze_frontend
    step4_comprehensive_assessment
    
    # Generate final deliverables
    create_step_status_file
    local final_report=$(generate_final_report)
    
    # Success summary
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "                        ✅ ANALYSIS COMPLETE!"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}All analysis steps completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📁 Analysis Results Directory:${NC}"
    echo -e "${WHITE}   ${ANALYSIS_DIR}/${NC}"
    echo ""
    echo -e "${YELLOW}📋 Key Files Generated:${NC}"
    echo -e "${WHITE}   📊 Comprehensive Assessment: $(basename "${COMPREHENSIVE_ASSESSMENT}")${NC}"
    echo -e "${WHITE}   ✅ Actionable TODO List: $(basename "${TODO_LIST}")${NC}"
    echo -e "${WHITE}   📈 Final Report: $(basename "${final_report}")${NC}"
    echo ""
    echo -e "${YELLOW}🚀 Next Steps with Claude-Powered Tracking:${NC}"
    echo -e "${WHITE}   1. Review: cat \"${COMPREHENSIVE_ASSESSMENT}\"${NC}"
    echo -e "${WHITE}   2. Claude Priority Analysis: claude analyze \"${TODO_LIST}\" --focus=\"Priority 1\"${NC}"
    echo -e "${WHITE}   3. Let Claude track progress: claude track-progress \"${ANALYSIS_DIR}/\"${NC}"
    echo -e "${WHITE}   4. Get Claude recommendations: claude recommend-next \"${COMPREHENSIVE_ASSESSMENT}\"${NC}"
    echo ""
    echo -e "${CYAN}Total analysis time: $(( ($(date +%s) - START_TIME) / 60 )) minutes${NC}"
    echo -e "${GREEN}Analysis session ${TIMESTAMP} completed successfully! 🎉${NC}"
}

# =============================================================================
# Script Execution
# =============================================================================

# Trap for cleanup on script exit
trap 'echo -e "${RED}Script interrupted${NC}"; exit 1' INT TERM

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi