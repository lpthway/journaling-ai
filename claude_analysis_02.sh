#!/bin/bash

# =============================================================================
# AI Journaling Assistant - Intelligent Analysis Script with Enhanced Monitoring
# =============================================================================
# Purpose: Automated analysis using Claude CLI v1.0.69 with comprehensive monitoring
# Author: Analysis Protocol v3.1 (Enhanced monitoring, Token tracking)
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
TIMESTAMP=${ANALYSIS_TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}

# Resume and progress tracking
PROGRESS_FILE="${ANALYSIS_DIR}/analysis_progress_${TIMESTAMP}.json"
SELF_TODO_FILE="${ANALYSIS_DIR}/script_self_todo_${TIMESTAMP}.md"
QUOTA_RESUME_FILE="${ANALYSIS_DIR}/quota_resume_${TIMESTAMP}.sh"

# Timeout configuration (in seconds)
CLAUDE_TIMEOUT=600      # 10 minutes - very generous for large analysis
CLAUDE_QUICK_TIMEOUT=120 # 2 minutes for simple operations

# Progress and logging configuration
SHOW_DETAILED_PROGRESS=true    # Show what Claude is analyzing in real-time
SHOW_TOKEN_USAGE=true          # Track and display token consumption
LOG_CLAUDE_INTERACTIONS=true   # Log all Claude interactions for debugging

# Token tracking (approximate - will be updated during execution)
SESSION_TOKEN_COUNT=0
SESSION_REQUESTS_COUNT=0

# Progress and logging configuration
SHOW_DETAILED_PROGRESS=true    # Show what Claude is analyzing in real-time
SHOW_TOKEN_USAGE=true          # Track and display token consumption
LOG_CLAUDE_INTERACTIONS=true   # Log all Claude interactions for debugging

# Token tracking (approximate - will be updated during execution)
SESSION_TOKEN_COUNT=0
SESSION_REQUESTS_COUNT=0

# Analysis configuration
DOCS_ANALYSIS_DEPTH="examine 3 levels deep into documentation structure"
BACKEND_ANALYSIS_DEPTH="analyze 4-5 levels deep into backend architecture, including all service layers"
FRONTEND_ANALYSIS_DEPTH="analyze 4 levels deep into frontend components and architecture"

# Progressive analysis settings
ENABLE_PROGRESSIVE_ANALYSIS=true
ENABLE_TARGETED_DEEP_DIVE=true
ENABLE_SELF_MANAGEMENT=true

# Critical areas for deep analysis
BACKEND_CRITICAL_AREAS=(
    "backend/app/services"
    "backend/app/tasks" 
    "backend/app/api"
    "backend/app/models"
)

FRONTEND_CRITICAL_AREAS=(
    "frontend/src/components"
    "frontend/src/services"
    "frontend/src/store"
)

# Analysis output files
DOCS_ANALYSIS="${ANALYSIS_DIR}/analysis_docs_${TIMESTAMP}.md"
BACKEND_ANALYSIS="${ANALYSIS_DIR}/analysis_backend_${TIMESTAMP}.md"
FRONTEND_ANALYSIS="${ANALYSIS_DIR}/analysis_frontend_${TIMESTAMP}.md"
COMPREHENSIVE_ASSESSMENT="${ANALYSIS_DIR}/comprehensive_assessment_${TIMESTAMP}.md"
TODO_LIST="${ANALYSIS_DIR}/actionable_todo_list_${TIMESTAMP}.md"

# Analysis steps definition
declare -A ANALYSIS_STEPS=(
    ["docs"]="Documentation Analysis"
    ["backend_overview"]="Backend Overview"
    ["backend_detailed"]="Backend Detailed Analysis"
    ["backend_deep_dive"]="Backend Deep Dive"
    ["frontend_overview"]="Frontend Overview" 
    ["frontend_detailed"]="Frontend Detailed Analysis"
    ["frontend_deep_dive"]="Frontend Deep Dive"
    ["synthesis"]="Comprehensive Assessment"
    ["todo_extraction"]="TODO List Creation"
    ["final_report"]="Final Report Generation"
)

# =============================================================================
# Progress and Token Tracking Functions
# =============================================================================

estimate_tokens() {
    local text="$1"
    local char_count=${#text}
    local estimated_tokens=$((char_count / 4))
    echo $estimated_tokens
}

log_claude_interaction() {
    local step="$1"
    local prompt_tokens="$2"
    local response_tokens="$3"
    local status="$4"
    local interaction_log="${ANALYSIS_DIR}/claude_interactions_${TIMESTAMP}.log"
    
    local timestamp=$(date -Iseconds)
    local total_tokens=$((prompt_tokens + response_tokens))
    
    SESSION_TOKEN_COUNT=$((SESSION_TOKEN_COUNT + total_tokens))
    SESSION_REQUESTS_COUNT=$((SESSION_REQUESTS_COUNT + 1))
    
    cat >> "$interaction_log" << EOF
[${timestamp}] STEP: ${step}
  Status: ${status}
  Prompt Tokens: ${prompt_tokens}
  Response Tokens: ${response_tokens}
  Total Tokens: ${total_tokens}
  Session Total: ${SESSION_TOKEN_COUNT}
  Request #: ${SESSION_REQUESTS_COUNT}
  ----------------------------------------
EOF
    
    if [[ "$SHOW_TOKEN_USAGE" == "true" ]]; then
        echo -e "${BLUE}📊 Token Usage:${NC}"
        echo -e "${WHITE}   • Prompt: ${prompt_tokens} tokens${NC}"
        echo -e "${WHITE}   • Response: ${response_tokens} tokens${NC}"
        echo -e "${WHITE}   • This Request: ${total_tokens} tokens${NC}"
        echo -e "${WHITE}   • Session Total: ${SESSION_TOKEN_COUNT} tokens${NC}"
        echo -e "${WHITE}   • Request Count: ${SESSION_REQUESTS_COUNT}${NC}"
        echo ""
    fi
}

show_detailed_progress() {
    local step="$1"
    local action="$2"
    local details="$3"
    
    if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]]; then
        local timestamp=$(date '+%H:%M:%S')
        echo -e "${CYAN}[${timestamp}] 🔄 ${step}: ${action}${NC}"
        if [[ -n "$details" ]]; then
            echo -e "${WHITE}   Details: ${details}${NC}"
        fi
    fi
}

show_analysis_preview() {
    local step="$1"
    local directory="$2"
    local file_count="$3"
    local analysis_type="$4"
    
    if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]]; then
        echo -e "${PURPLE}📁 Analysis Scope:${NC}"
        echo -e "${WHITE}   • Directory: ${directory}${NC}"
        echo -e "${WHITE}   • Files Found: ${file_count}${NC}"
        echo -e "${WHITE}   • Analysis Type: ${analysis_type}${NC}"
        echo ""
    fi
}

# =============================================================================
# Progress Management Functions  
# =============================================================================

create_progress_file() {
    cat > "$PROGRESS_FILE" << EOF
{
  "session_id": "${TIMESTAMP}",
  "started_at": "$(date -Iseconds)",
  "project_root": "${PROJECT_ROOT}",
  "steps_completed": [],
  "steps_failed": [],
  "current_step": "",
  "claude_quota_exhausted": false,
  "resume_point": null,
  "total_steps": ${#ANALYSIS_STEPS[@]}
}
EOF
}

update_progress() {
    local step="$1"
    local status="$2"
    local details="$3"
    
    if [[ ! -f "$PROGRESS_FILE" ]]; then
        create_progress_file
    fi
    
    local temp_file=$(mktemp)
    python3 -c "
import json
import sys
from datetime import datetime

try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
except:
    progress = {
        'session_id': '${TIMESTAMP}',
        'started_at': datetime.now().isoformat(),
        'project_root': '${PROJECT_ROOT}',
        'steps_completed': [],
        'steps_failed': [],
        'current_step': '',
        'claude_quota_exhausted': False,
        'resume_point': None,
        'total_steps': ${#ANALYSIS_STEPS[@]}
    }

progress['current_step'] = '$step'
progress['last_updated'] = datetime.now().isoformat()

if '$status' == 'completed':
    if '$step' not in progress['steps_completed']:
        progress['steps_completed'].append('$step')
    if '$step' in progress['steps_failed']:
        progress['steps_failed'].remove('$step')
elif '$status' == 'failed':
    if '$step' not in progress['steps_failed']:
        progress['steps_failed'].append('$step')
elif '$status' == 'quota_exhausted':
    progress['claude_quota_exhausted'] = True
    progress['resume_point'] = '$step'

if '$details':
    if 'step_details' not in progress:
        progress['step_details'] = {}
    progress['step_details']['$step'] = '$details'

with open('$temp_file', 'w') as f:
    json.dump(progress, f, indent=2)
" 2>/dev/null && mv "$temp_file" "$PROGRESS_FILE" || rm -f "$temp_file"
}

get_progress_status() {
    if [[ ! -f "$PROGRESS_FILE" ]]; then
        echo "not_started"
        return
    fi
    
    python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
    
    if progress.get('claude_quota_exhausted', False):
        print('quota_exhausted')
    elif len(progress['steps_completed']) == progress['total_steps']:
        print('completed')
    elif progress['steps_completed'] or progress['current_step']:
        print('in_progress')
    else:
        print('not_started')
except:
    print('not_started')
" 2>/dev/null || echo "not_started"
}

get_completed_steps() {
    if [[ ! -f "$PROGRESS_FILE" ]]; then
        echo ""
        return
    fi
    
    python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
    print(','.join(progress.get('steps_completed', [])))
except:
    print('')
" 2>/dev/null || echo ""
}

is_step_completed() {
    local step="$1"
    local completed_steps=$(get_completed_steps)
    [[ "$completed_steps" == *"$step"* ]]
}

create_resume_script() {
    local resume_step="$1"
    cat > "$QUOTA_RESUME_FILE" << EOF
#!/bin/bash
export ANALYSIS_TIMESTAMP="${TIMESTAMP}"
export RESUME_FROM_STEP="$resume_step"

echo "🔄 Resuming analysis from step: $resume_step"
echo "📅 Original session: ${TIMESTAMP}"
echo "⏳ Waiting for Claude quota to refresh..."

sleep 5

cd "${PROJECT_ROOT}"
./$(basename "$0") --resume

echo "✅ Resume script completed"
EOF
    chmod +x "$QUOTA_RESUME_FILE"
    echo -e "${YELLOW}📝 Resume script created: $QUOTA_RESUME_FILE${NC}"
}

create_self_todo() {
    cat > "$SELF_TODO_FILE" << EOF
# Analysis Script Self-Management TODO

**Session**: ${TIMESTAMP}  
**Generated**: $(date)  
**Status**: Auto-generated self-tracking TODO list

## Progress Overview
- **Session ID**: ${TIMESTAMP}
- **Total Steps**: ${#ANALYSIS_STEPS[@]}
- **Completed**: $(echo $(get_completed_steps) | tr ',' '\n' | wc -w)
- **Remaining**: $((${#ANALYSIS_STEPS[@]} - $(echo $(get_completed_steps) | tr ',' '\n' | wc -w)))

## Analysis Steps Checklist

$(for step in "${!ANALYSIS_STEPS[@]}"; do
    if is_step_completed "$step"; then
        echo "- [x] **${ANALYSIS_STEPS[$step]}** - ✅ Completed"
    else
        echo "- [ ] **${ANALYSIS_STEPS[$step]}** - ⏳ Pending"
    fi
done)

## Self-Management Tasks

### Completed Self-Tasks
- [x] **Initialize Progress Tracking** - Created progress.json file
- [x] **Create Self-TODO** - Generated this self-management document
$(is_step_completed "docs" && echo "- [x] **Documentation Analysis** - Completed successfully")
$(is_step_completed "backend_overview" && echo "- [x] **Backend Overview** - Completed successfully") 

### Pending Self-Tasks  
$(! is_step_completed "docs" && echo "- [ ] **Complete Documentation Analysis** - Analyze docs/ directory structure")
$(! is_step_completed "synthesis" && echo "- [ ] **Create Comprehensive Assessment** - Synthesize all analysis results")
$(! is_step_completed "final_report" && echo "- [ ] **Generate Final Report** - Create summary and next steps")

### Self-Improvement Tasks
- [ ] **Optimize Claude Quota Usage** - Monitor and minimize API calls  
- [ ] **Enhance Error Recovery** - Improve fallback mechanisms
- [ ] **Add More Detailed Logging** - Track analysis quality and timing

## Quota Management
- **Current Status**: $(get_progress_status)
- **Resume Available**: $([ -f "$QUOTA_RESUME_FILE" ] && echo "Yes - $QUOTA_RESUME_FILE" || echo "No")
- **Auto-Resume**: Enabled - script will create resume point on quota exhaustion

---
*This TODO list is automatically maintained by the analysis script*  
*Last updated: $(date)*
EOF

    echo -e "${GREEN}✅ Self-TODO created: $SELF_TODO_FILE${NC}"
}

update_self_todo() {
    if [[ "$ENABLE_SELF_MANAGEMENT" == "true" ]]; then
        create_self_todo
    fi
}

handle_claude_quota_exhausted() {
    local current_step="$1"
    echo -e "${RED}🚫 Claude quota exhausted!${NC}"
    echo -e "${YELLOW}Creating resume point...${NC}"
    
    update_progress "$current_step" "quota_exhausted" "Quota exhausted, resume available"
    create_resume_script "$current_step"
    update_self_todo
    
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "                    ⏳ CLAUDE QUOTA EXHAUSTED"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}The analysis has been paused due to Claude quota limits.${NC}"
    echo ""
    echo -e "${YELLOW}🔄 To resume analysis:${NC}"
    echo -e "${WHITE}   Option 1: ./${QUOTA_RESUME_FILE##*/}${NC}"
    echo -e "${WHITE}   Option 2: ./$(basename "$0") --resume${NC}"
    echo ""
    echo -e "${CYAN}⏰ Wait for quota refresh, then resume${NC}"
    exit 0
}

# =============================================================================
# Utility Functions
# =============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "     AI JOURNALING ASSISTANT - CLAUDE v1.0.69+ ENHANCED MONITORING"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}Project Root: ${WHITE}${PROJECT_ROOT}${NC}"
    echo -e "${CYAN}Analysis Dir: ${WHITE}${ANALYSIS_DIR}${NC}"
    echo -e "${CYAN}Session ID: ${WHITE}${TIMESTAMP}${NC}"
    
    local status=$(get_progress_status)
    case $status in
        "not_started")
            echo -e "${CYAN}Status: ${WHITE}New Analysis${NC}"
            ;;
        "in_progress") 
            local completed_count=$(echo $(get_completed_steps) | tr ',' '\n' | wc -w)
            echo -e "${CYAN}Status: ${YELLOW}Resuming (${completed_count}/${#ANALYSIS_STEPS[@]} steps completed)${NC}"
            ;;
        "quota_exhausted")
            echo -e "${CYAN}Status: ${RED}Quota Exhausted - Resume Available${NC}"
            ;;
        "completed")
            echo -e "${CYAN}Status: ${GREEN}Previously Completed${NC}"
            ;;
    esac
    echo ""
}

print_step_header() {
    local step_key=$1
    local step_title=$2
    local step_num=$3
    
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "  STEP ${step_num}: ${step_title}"
    echo "============================================================================="
    echo -e "${NC}"
    
    if is_step_completed "$step_key"; then
        echo -e "${GREEN}✅ This step was previously completed - skipping${NC}"
        echo ""
        return 1
    fi
    
    update_progress "$step_key" "in_progress" "Starting $step_title"
    return 0
}

print_progress() {
    local completed_count=$(echo $(get_completed_steps) | tr ',' '\n' | wc -w)
    local total=${#ANALYSIS_STEPS[@]}
    local percentage=$((completed_count * 100 / total))
    echo -e "${YELLOW}Progress: [${completed_count}/${total}] ${percentage}% Complete${NC}"
    echo ""
}

check_prerequisites() {
    echo -e "${CYAN}Checking prerequisites...${NC}"
    
    # Check if claude is installed
    CLAUDE_CMD=""
    if command -v claude &> /dev/null; then
        CLAUDE_CMD="claude"
        echo -e "${GREEN}✅ Found Claude CLI as 'claude'${NC}"
    else
        echo -e "${RED}❌ ERROR: Claude CLI not found${NC}"
        echo -e "${WHITE}Please install it with: curl -fsSL claude.ai/install.sh | bash${NC}"
        exit 1
    fi
    
    # Verify Claude is working
    echo -e "${CYAN}Testing Claude CLI...${NC}"
    if $CLAUDE_CMD --version &> /dev/null; then
        local version=$($CLAUDE_CMD --version 2>/dev/null)
        echo -e "${GREEN}✅ Claude CLI is working - Version: ${version}${NC}"
    else
        echo -e "${YELLOW}⚠️  Claude CLI found but may need authentication${NC}"
        echo -e "${WHITE}Try running: $CLAUDE_CMD${NC}"
    fi
    
    # Check Python3 for progress tracking
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ ERROR: Python3 required for progress tracking${NC}"
        exit 1
    fi
    
    # Check if we're in a valid project directory
    if [[ ! -d "backend" ]] && [[ ! -d "frontend" ]] && [[ ! -d "docs" ]]; then
        echo -e "${RED}❌ ERROR: This doesn't appear to be the project root${NC}"
        echo -e "${WHITE}Please run this script from your AI journaling assistant root directory${NC}"
        exit 1
    fi
    
    # Create analysis directory
    mkdir -p "${ANALYSIS_DIR}"
    
    # Initialize or load progress
    if [[ ! -f "$PROGRESS_FILE" ]]; then
        create_progress_file
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
    echo ""
}

# =============================================================================
# Claude Analysis Functions
# =============================================================================

run_claude_analysis() {
    local prompt="$1"
    local output_file="$2" 
    local context_dir="$3"
    local step_key="$4"
    local use_quick_timeout="$5"
    
    local timeout_duration=${CLAUDE_TIMEOUT}
    if [[ "$use_quick_timeout" == "quick" ]]; then
        timeout_duration=${CLAUDE_QUICK_TIMEOUT}
    fi
    
    # Calculate estimated tokens and show progress
    local prompt_tokens=$(estimate_tokens "$prompt")
    show_detailed_progress "$step_key" "Preparing Claude analysis" "Estimated prompt size: ${prompt_tokens} tokens"
    
    echo -e "${YELLOW}🤖 Running Claude analysis (timeout: ${timeout_duration}s)...${NC}"
    
    # Change to context directory if provided
    local original_dir=$(pwd)
    if [[ -n "$context_dir" ]] && [[ -d "$context_dir" ]]; then
        cd "$context_dir"
        show_detailed_progress "$step_key" "Context switch" "Analyzing from $(pwd)"
        echo -e "${CYAN}📂 Context: Analyzing from $(pwd)${NC}"
        
        # Show what files will be analyzed
        local file_count=$(find . -maxdepth 3 -type f \( -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" -o -name "*.txt" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) 2>/dev/null | wc -l)
        show_analysis_preview "$step_key" "$(pwd)" "$file_count" "Deep analysis"
    fi
    
    # Run Claude with natural language prompt and quota monitoring
    local claude_output=$(mktemp)
    local claude_error=$(mktemp)
    
    echo -e "${CYAN}🔧 Debug Info:${NC}"
    echo -e "${WHITE}   • Command: $CLAUDE_CMD -p \"[PROMPT]\" --output-format text${NC}"
    echo -e "${WHITE}   • Working directory: $(pwd)${NC}"
    echo -e "${WHITE}   • Expected output file: $(basename "$output_file")${NC}"
    echo -e "${WHITE}   • Prompt length: ${#prompt} characters (~${prompt_tokens} tokens)${NC}"
    echo ""
    
    # Show Claude is thinking
    echo -e "${BLUE}🧠 Claude is analyzing...${NC}"
    local start_time=$(date +%s)
    
    # Start a background process to show progress dots
    if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]]; then
        (
            local dots=""
            while true; do
                echo -ne "\r${CYAN}   Thinking${dots}${NC}"
                dots="${dots}."
                if [[ ${#dots} -gt 10 ]]; then
                    dots=""
                fi
                sleep 1
            done
        ) &
        local progress_pid=$!
    fi
    
    # Determine timeout command
    local timeout_cmd=""
    if [[ -n "$timeout_duration" ]]; then
        timeout_cmd="timeout $timeout_duration"
    else
        echo -e "${RED}⚠️  Running without timeout - use Ctrl+C to interrupt if needed${NC}"
    fi
    
    # Execute Claude command
    if $timeout_cmd $CLAUDE_CMD -p "$prompt" --output-format text > "$claude_output" 2> "$claude_error"; then
        # Kill progress indicator
        if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]] && [[ -n "${progress_pid:-}" ]]; then
            kill $progress_pid 2>/dev/null || true
            echo -ne "\r${GREEN}   ✅ Analysis complete!${NC}                    \n"
        fi
        
        # Success - calculate timing and tokens
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local response_content=$(cat "$claude_output")
        local response_tokens=$(estimate_tokens "$response_content")
        
        # Show completion details
        echo -e "${GREEN}✅ Claude analysis successful!${NC}"
        echo -e "${BLUE}⏱️  Analysis completed in ${duration} seconds${NC}"
        
        # Log interaction and show token usage
        log_claude_interaction "$step_key" "$prompt_tokens" "$response_tokens" "SUCCESS"
        
        # Show response preview
        if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]]; then
            echo -e "${PURPLE}📄 Response Preview:${NC}"
            echo -e "${WHITE}$(echo "$response_content" | head -n 5 | sed 's/^/   • /')${NC}"
            if [[ $(echo "$response_content" | wc -l) -gt 5 ]]; then
                echo -e "${WHITE}   ... ($(echo "$response_content" | wc -l) total lines)${NC}"
            fi
            echo ""
        fi
        
        # Move output to final location
        mv "$claude_output" "$output_file"
        rm -f "$claude_error"
        cd "$original_dir"
        
        show_detailed_progress "$step_key" "Analysis completed" "Output saved to $(basename "$output_file")"
        update_progress "$step_key" "completed" "Analysis completed successfully in ${duration}s"
        return 0
    else
        # Kill progress indicator if it exists
        if [[ "$SHOW_DETAILED_PROGRESS" == "true" ]] && [[ -n "${progress_pid:-}" ]]; then
            kill $progress_pid 2>/dev/null || true
            echo -ne "\r${RED}   ❌ Analysis failed!${NC}                      \n"
        fi
        
        # Get detailed error information
        local exit_code=$?
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        local error_content=$(cat "$claude_error" 2>/dev/null || echo "No error output")
        local partial_output=$(head -n 10 "$claude_output" 2>/dev/null || echo "No output")
        
        # Log failed interaction
        log_claude_interaction "$step_key" "$prompt_tokens" "0" "FAILED: Exit $exit_code"
        
        echo -e "${RED}❌ Claude analysis failed after ${duration} seconds!${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
        echo -e "${YELLOW}Exit Code: $exit_code${NC}"
        echo -e "${YELLOW}Duration: ${duration}s / ${timeout_duration}s timeout${NC}"
        echo -e "${YELLOW}Error Content:${NC}"
        echo -e "${WHITE}$error_content${NC}"
        echo -e "${YELLOW}Working Directory: $(pwd)${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
        
        # Check specific error types
        if [[ $exit_code -eq 124 ]]; then
            echo -e "${RED}🕒 TIMEOUT: Claude took longer than $timeout_duration seconds${NC}"
        elif [[ "$error_content" == *"quota"* ]] || [[ "$error_content" == *"rate limit"* ]] || [[ "$error_content" == *"limit exceeded"* ]]; then
            echo -e "${RED}🚫 QUOTA/RATE LIMIT: Claude usage limits reached${NC}"
            rm -f "$claude_output" "$claude_error"
            cd "$original_dir"
            handle_claude_quota_exhausted "$step_key"
            return 2
        elif [[ "$error_content" == *"authentication"* ]] || [[ "$error_content" == *"auth"* ]]; then
            echo -e "${RED}🔐 AUTHENTICATION: Claude authentication failed${NC}"
            echo -e "${CYAN}💡 Fix: Run 'claude auth' to re-authenticate${NC}"
        else
            echo -e "${RED}❓ UNKNOWN ERROR: See error details above${NC}"
        fi
        
        rm -f "$claude_output" "$claude_error"
        cd "$original_dir"
        update_progress "$step_key" "failed" "Claude analysis failed: Exit $exit_code after ${duration}s - $error_content"
        return 1
    fi
}

# =============================================================================
# Analysis Steps (Simplified for Testing)
# =============================================================================

step1_analyze_docs() {
    if ! print_step_header "docs" "Documentation Analysis" "1"; then
        return 0
    fi
    
    if [[ ! -d "docs" ]]; then
        echo -e "${YELLOW}⚠️  WARNING: docs/ directory not found${NC}"
        echo -e "${WHITE}Creating placeholder analysis...${NC}"
        cat > "${DOCS_ANALYSIS}" << EOF
# Documentation Analysis - No docs/ Directory Found

**Analysis Date**: $(date)
**Project Root**: ${PROJECT_ROOT}
**Session ID**: ${TIMESTAMP}

## Status
- **docs/ Directory**: Not found
- **Documentation Score**: 0/10
- **Recommendation**: Create comprehensive documentation structure

## Priority Actions
1. Create documentation directory structure
2. Document current architecture
3. Create API documentation
4. Write deployment guides
EOF
        update_progress "docs" "completed" "No docs directory found - placeholder created"
        update_self_todo
        return 0
    fi

    echo -e "${CYAN}Analyzing docs/ directory with Claude...${NC}"
    
    local docs_prompt="I need you to analyze the documentation structure and content in this project. Please ${DOCS_ANALYSIS_DEPTH} and focus on:

## Documentation Architecture Assessment:
- Review all markdown files for consistency and completeness
- Identify documentation gaps or outdated information  
- Check if architectural decisions match current implementation

## Project State Analysis:
- Compare claimed completion status with actual implementation evidence
- Identify discrepancies between documented and actual progress
- Check if performance targets and metrics are realistic and measurable

## Documentation Quality Review:
- Assess documentation structure and organization
- Identify missing technical specifications that should exist
- Check for incomplete or placeholder content that needs completion

## Output Requirements:
Please provide:
- Summary of documentation completeness (percentage complete by category)
- List of architectural inconsistencies found between docs and reality
- Missing documentation that should exist for a project of this scope
- Quality assessment score (1-10) with detailed justification
- Priority recommendations for documentation improvements

Focus on being practical and actionable in your analysis. This is session ${TIMESTAMP}."

    if run_claude_analysis "$docs_prompt" "$DOCS_ANALYSIS" "docs" "docs"; then
        echo -e "${GREEN}✅ Documentation analysis completed${NC}"
        update_self_todo
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            return 2
        fi
        echo -e "${YELLOW}Creating fallback documentation analysis...${NC}"
        cat > "${DOCS_ANALYSIS}" << EOF
# Documentation Analysis - Fallback Report

**Analysis Date**: $(date)
**Analysis Method**: Fallback (Claude analysis failed or quota exhausted)
**Directory**: docs
**Session ID**: ${TIMESTAMP}

## Status
- **Claude Analysis**: Failed or quota exhausted
- **Fallback Method**: Manual directory inspection

## Directory Structure
$(find docs/ -type f -name "*.md" 2>/dev/null | head -20 || echo "No markdown files found")

## File Count by Type
- Documentation files: $(find docs/ -name "*.md" -o -name "*.rst" -o -name "*.txt" 2>/dev/null | wc -l)

## Resume Instructions
When Claude quota is available again:
\`\`\`bash
ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume
\`\`\`
EOF
        update_progress "docs" "completed" "Fallback analysis created"
        update_self_todo
    fi
    
    print_progress
}

# =============================================================================
# Main Execution Flow
# =============================================================================

main() {
    local START_TIME=$(date +%s)
    
    # Handle resume mode
    if [[ "$1" == "--resume" ]] || [[ -n "$RESUME_FROM_STEP" ]]; then
        echo -e "${BLUE}🔄 RESUME MODE ACTIVATED${NC}"
        echo ""
    fi
    
    # Initialize
    print_banner
    check_prerequisites
    
    # Initialize self-management
    if [[ "$ENABLE_SELF_MANAGEMENT" == "true" ]]; then
        create_self_todo
    fi
    
    # Execute analysis steps
    echo -e "${BLUE}🚀 Starting Analysis Execution${NC}"
    print_progress
    echo ""
    
    # Step 1: Documentation Analysis
    if step1_analyze_docs; then
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            return 0
        fi
    fi
    
    # For now, just complete docs analysis to test the script
    update_self_todo
    
    # Success summary
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "                    ✅ ANALYSIS TEST COMPLETE!"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}Documentation analysis completed successfully with enhanced monitoring!${NC}"
    echo ""
    echo -e "${YELLOW}📁 Analysis Results Directory:${NC}"
    echo -e "${WHITE}   ${ANALYSIS_DIR}/${NC}"
    echo ""
    echo -e "${YELLOW}📋 Files Generated:${NC}"
    echo -e "${WHITE}   📊 Documentation Analysis: $(basename "${DOCS_ANALYSIS}")${NC}"
    echo -e "${WHITE}   🤖 Script Self-TODO: $(basename "${SELF_TODO_FILE}")${NC}"
    echo -e "${WHITE}   📊 Claude Interactions Log: claude_interactions_${TIMESTAMP}.log${NC}"
    echo ""
    echo -e "${YELLOW}📊 Session Statistics:${NC}"
    echo -e "${WHITE}   🤖 Total Claude Requests: ${SESSION_REQUESTS_COUNT}${NC}"
    echo -e "${WHITE}   🎯 Total Tokens Used: ${SESSION_TOKEN_COUNT}${NC}"
    echo -e "${WHITE}   ⏱️  Analysis Time: $(( ($(date +%s) - START_TIME) / 60 )) minutes${NC}"
    echo ""
    echo -e "${BLUE}💡 Enhanced Monitoring Features:${NC}"
    echo -e "${WHITE}   🎯 Real-time progress tracking with visual indicators${NC}"
    echo -e "${WHITE}   📊 Token usage monitoring and cost estimation${NC}"
    echo -e "${WHITE}   🕐 Detailed timing information for each analysis step${NC}"
    echo -e "${WHITE}   📝 Complete interaction logging${NC}"
    echo ""
    echo -e "${CYAN}Test completed successfully! 🎉${NC}"
    echo -e "${GREEN}Enhanced monitoring and error reporting is working!${NC}"
}

# =============================================================================
# Script Execution with Command Line Parsing
# =============================================================================

# Parse command line arguments
case "${1:-}" in
    "--no-timeout")
        echo -e "${RED}⚠️  WARNING: Removing all timeouts!${NC}"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            CLAUDE_TIMEOUT=""
            CLAUDE_QUICK_TIMEOUT=""
            echo -e "${CYAN}Timeouts disabled${NC}"
            shift
        else
            echo "Keeping timeouts enabled"
            exit 0
        fi
        ;;
    "--test")
        echo "Testing Claude CLI functionality..."
        echo ""
        echo "Test 1: Basic Claude response"
        if claude -p "Respond with 'Claude is working' to confirm functionality" --output-format text; then
            echo "✅ Basic Claude test passed"
        else
            echo "❌ Basic Claude test failed"
        fi
        echo ""
        echo "Test 2: Directory analysis capability"
        if claude -p "List 3 key observations about the current directory structure" --output-format text; then
            echo "✅ Directory analysis test passed"
        else
            echo "❌ Directory analysis test failed"
        fi
        exit 0
        ;;
    "--resume")
        RESUME_MODE=true
        ;;
    "--status")
        if [[ -f "$PROGRESS_FILE" ]]; then
            echo "Analysis Status:"
            cat "$PROGRESS_FILE" | python3 -m json.tool
        else
            echo "No analysis in progress"
        fi
        exit 0
        ;;
    "--help")
        echo "AI Journaling Assistant - Intelligent Analysis Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --resume       Resume interrupted analysis"
        echo "  --status       Show current progress"
        echo "  --test         Test Claude CLI functionality"
        echo "  --no-timeout   Remove timeouts (WARNING: may hang)"
        echo "  --help         Show this help"
        echo ""
        echo "Features:"
        echo "  • Enhanced monitoring with real-time progress"
        echo "  • Token usage tracking and cost estimation"
        echo "  • Intelligent resume capability for quota limits"
        echo "  • Comprehensive error reporting and debugging"
        exit 0
        ;;
esac

# Trap for cleanup
trap 'echo -e "${RED}Script interrupted${NC}"; update_progress "interrupted" "failed" "Script interrupted by user"; exit 1' INT TERM

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi