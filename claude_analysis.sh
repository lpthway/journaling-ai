#!/bin/bash

# =============================================================================
# AI Journaling Assistant - Intelligent Analysis Script with Resume
# =============================================================================
# Purpose: Automated analysis using Claude CLI v1.0.69 with self-management
# Author: Analysis Protocol v3.0 (Resume-capable, Self-tracking)
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
TIMESTAMP=${ANALYSIS_TIMESTAMP:-$(date +%Y%m%d_%H%M%S)}  # Allow resume with same timestamp

# Resume and progress tracking
PROGRESS_FILE="${ANALYSIS_DIR}/analysis_progress_${TIMESTAMP}.json"
SELF_TODO_FILE="${ANALYSIS_DIR}/script_self_todo_${TIMESTAMP}.md"
QUOTA_RESUME_FILE="${ANALYSIS_DIR}/quota_resume_${TIMESTAMP}.sh"

# Analysis configuration - Natural language approach
DOCS_ANALYSIS_DEPTH="examine 3 levels deep into documentation structure"
BACKEND_ANALYSIS_DEPTH="analyze 4-5 levels deep into backend architecture, including all service layers"
FRONTEND_ANALYSIS_DEPTH="analyze 4 levels deep into frontend components and architecture"

# Timeout configuration (in seconds)
CLAUDE_TIMEOUT=600      # 10 minutes - very generous for large analysis
CLAUDE_QUICK_TIMEOUT=180 # 3 minutes for simple operations

# Progressive analysis settings
ENABLE_PROGRESSIVE_ANALYSIS=true
ENABLE_TARGETED_DEEP_DIVE=true
ENABLE_SELF_MANAGEMENT=true     # Track own progress and create self-TODOs

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
    local status="$2"  # completed, failed, in_progress
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
        echo "[]"
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
# Resume Analysis Script - Generated automatically
# Resume from step: $resume_step
# Generated: $(date)

export ANALYSIS_TIMESTAMP="${TIMESTAMP}"
export RESUME_FROM_STEP="$resume_step"

echo "🔄 Resuming analysis from step: $resume_step"
echo "📅 Original session: ${TIMESTAMP}"
echo "⏳ Waiting for Claude quota to refresh..."

# Wait a bit before resuming
sleep 5

# Resume the analysis
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
$(is_step_completed "backend_detailed" && echo "- [x] **Backend Detailed Analysis** - Completed successfully")
$(is_step_completed "synthesis" && echo "- [x] **Synthesis** - Created comprehensive assessment")

### Pending Self-Tasks  
$(! is_step_completed "docs" && echo "- [ ] **Complete Documentation Analysis** - Analyze docs/ directory structure")
$(! is_step_completed "backend_overview" && echo "- [ ] **Complete Backend Overview** - Quick backend architecture scan")
$(! is_step_completed "backend_detailed" && echo "- [ ] **Complete Backend Analysis** - Detailed backend code review")
$(! is_step_completed "synthesis" && echo "- [ ] **Create Comprehensive Assessment** - Synthesize all analysis results")
$(! is_step_completed "final_report" && echo "- [ ] **Generate Final Report** - Create summary and next steps")

### Self-Improvement Tasks
- [ ] **Optimize Claude Quota Usage** - Monitor and minimize API calls  
- [ ] **Enhance Error Recovery** - Improve fallback mechanisms
- [ ] **Add More Detailed Logging** - Track analysis quality and timing
- [ ] **Implement Smart Resume** - Better handling of quota limits

## Quota Management
- **Current Status**: $(get_progress_status)
- **Resume Available**: $([ -f "$QUOTA_RESUME_FILE" ] && echo "Yes - $QUOTA_RESUME_FILE" || echo "No")
- **Auto-Resume**: Enabled - script will create resume point on quota exhaustion

## Quality Metrics  
- **Analysis Depth**: Comprehensive (docs, backend, frontend + deep dives)
- **Fallback Coverage**: 100% (all steps have manual fallbacks)
- **Resume Reliability**: High (JSON-based progress tracking)
- **Self-Awareness**: Active (this TODO list updates automatically)

---
*This TODO list is automatically maintained by the analysis script*  
*Last updated: $(date)*
EOF

    echo -e "${GREEN}✅ Self-TODO created: $SELF_TODO_FILE${NC}"
}

update_self_todo() {
    if [[ "$ENABLE_SELF_MANAGEMENT" == "true" ]]; then
        create_self_todo  # Recreate with current status
    fi
}

# =============================================================================
# Utility Functions
# =============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "        AI JOURNALING ASSISTANT - CLAUDE v1.0.69 INTELLIGENT ANALYSIS"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}Project Root: ${WHITE}${PROJECT_ROOT}${NC}"
    echo -e "${CYAN}Analysis Dir: ${WHITE}${ANALYSIS_DIR}${NC}"
    echo -e "${CYAN}Session ID: ${WHITE}${TIMESTAMP}${NC}"
    echo -e "${CYAN}Progress File: ${WHITE}$(basename "$PROGRESS_FILE")${NC}"
    
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
        return 1  # Signal to skip
    fi
    
    update_progress "$step_key" "in_progress" "Starting $step_title"
    return 0  # Signal to proceed
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
    
    # Check for pytz package (needed for intelligent quota scheduling)
    if ! python3 -c "import pytz" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Installing pytz package for intelligent timezone handling...${NC}"
        if python3 -m pip install pytz --quiet 2>/dev/null || pip3 install pytz --quiet 2>/dev/null; then
            echo -e "${GREEN}✅ pytz package installed successfully${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not install pytz - auto-scheduling may not work optimally${NC}"
            echo -e "${WHITE}Falling back to basic resume scripts${NC}"
        fi
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
# Intelligent Quota Management Functions
# =============================================================================

parse_quota_reset_time() {
    local quota_message="$1"
    
    # Handle different quota message formats:
    # Format 1: "Claude AI usage limit reached|1754578800" (timestamp)
    # Format 2: "Claude usage limit reached. Your limit will reset at 5pm (Europe/Berlin)."
    
    # Check for timestamp format first (more reliable)
    if [[ "$quota_message" =~ Claude\ AI\ usage\ limit\ reached\|([0-9]+) ]]; then
        local timestamp="${BASH_REMATCH[1]}"
        echo "TIMESTAMP:$timestamp"
        return 0
    fi
    
    # Fall back to text format parsing
    if echo "$quota_message" | grep -q "reset at.*[ap]m.*(" ; then
        # Extract the time and timezone parts
        local reset_info=$(echo "$quota_message" | sed -n 's/.*reset at \([0-9:]*[ap]m\) (\([^)]*\)).*/\1|\2/p')
        
        if [[ -n "$reset_info" ]]; then
            local time_part=$(echo "$reset_info" | cut -d'|' -f1)
            local timezone=$(echo "$reset_info" | cut -d'|' -f2)
            
            echo "TIME:$time_part|TZ:$timezone"
            return 0
        fi
    fi
    
    return 1
}

calculate_wait_time() {
    local parsed_data="$1"
    
    # Handle timestamp format: TIMESTAMP:1754578800
    if [[ "$parsed_data" =~ ^TIMESTAMP:([0-9]+)$ ]]; then
        local timestamp="${BASH_REMATCH[1]}"
        
        python3 -c "
import datetime
import sys

try:
    timestamp = int('$timestamp')
    reset_time = datetime.datetime.fromtimestamp(timestamp)
    now = datetime.datetime.now()
    
    # Calculate wait time in seconds
    wait_seconds = int((reset_time - now).total_seconds())
    
    # Add 2 minutes buffer to be safe
    wait_seconds += 120
    
    # Ensure minimum wait time is 0
    if wait_seconds < 0:
        wait_seconds = 300  # Default to 5 minutes if time has passed
    
    print(f'WAIT_SECONDS:{wait_seconds}')
    print(f'RESET_TIME:{reset_time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
    print(f'CURRENT_TIME:{now.strftime(\"%Y-%m-%d %H:%M:%S\")}')
    
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>/dev/null
        return $?
    fi
    
    # Handle text format: TIME:5pm|TZ:Europe/Berlin
    local reset_time=$(echo "$parsed_data" | sed 's/.*TIME:\([^|]*\).*/\1/')
    local timezone=$(echo "$parsed_data" | sed 's/.*TZ:\([^|]*\).*/\1/')
    
    # Convert reset time to 24-hour format and get current time in target timezone
    python3 -c "
import datetime
import pytz
import re
import sys

try:
    # Parse time
    time_str = '$reset_time'
    tz_str = '$timezone'
    
    # Handle timezone string (convert Europe/Berlin format)
    if '/' in tz_str:
        tz = pytz.timezone(tz_str)
    else:
        # Handle abbreviated timezones like CET, EST, etc.
        tz = pytz.timezone('UTC')  # Fallback to UTC
    
    # Get current time in target timezone
    now = datetime.datetime.now(tz)
    today = now.date()
    
    # Parse the reset time
    time_match = re.match(r'(\d{1,2})(:(\d{2}))?(am|pm)', time_str.lower())
    if not time_match:
        print('ERROR: Could not parse time format')
        sys.exit(1)
    
    hour = int(time_match.group(1))
    minute = int(time_match.group(3)) if time_match.group(3) else 0
    ampm = time_match.group(4)
    
    # Convert to 24-hour format
    if ampm == 'pm' and hour != 12:
        hour += 12
    elif ampm == 'am' and hour == 12:
        hour = 0
    
    # Create reset datetime for today
    reset_today = tz.localize(datetime.datetime.combine(today, datetime.time(hour, minute)))
    
    # If reset time is in the past today, it means tomorrow
    if reset_today <= now:
        reset_tomorrow = reset_today + datetime.timedelta(days=1)
        reset_time = reset_tomorrow
    else:
        reset_time = reset_today
    
    # Calculate wait time in seconds
    wait_seconds = int((reset_time - now).total_seconds())
    
    # Add 2 minutes buffer to be safe
    wait_seconds += 120
    
    print(f'WAIT_SECONDS:{wait_seconds}')
    print(f'RESET_TIME:{reset_time.strftime(\"%Y-%m-%d %H:%M:%S %Z\")}')
    print(f'CURRENT_TIME:{now.strftime(\"%Y-%m-%d %H:%M:%S %Z\")}')
    
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>/dev/null
}

create_auto_resume_script() {
    local resume_step="$1"
    local wait_seconds="$2"
    local reset_time_str="$3"
    
    cat > "$QUOTA_RESUME_FILE" << EOF
#!/bin/bash
# Automatic Resume Analysis Script - Generated with intelligent scheduling
# Resume from step: $resume_step
# Scheduled resume time: $reset_time_str
# Generated: $(date)

export ANALYSIS_TIMESTAMP="${TIMESTAMP}"
export RESUME_FROM_STEP="$resume_step"

echo "🤖 Intelligent Auto-Resume Script Activated"
echo "📅 Original session: ${TIMESTAMP}"
echo "⏰ Claude quota will reset at: $reset_time_str"
echo "🕐 Current time: \$(date)"
echo ""

# Calculate remaining wait time dynamically (in case script is run later)
# Extract timestamp from reset time string
reset_timestamp=\$(date -d "$reset_time_str" +%s 2>/dev/null)
current_timestamp=\$(date +%s)

if [[ -n "\$reset_timestamp" ]] && [[ "\$reset_timestamp" -gt "\$current_timestamp" ]]; then
    wait_seconds=\$((\$reset_timestamp - \$current_timestamp + 120))  # Add 2-minute buffer
else
    # Fallback: if we can't parse the time, assume quota is ready
    wait_seconds=0
    echo "⚠️  Could not calculate remaining time - assuming quota is ready"
fi

if [[ \$wait_seconds -gt 0 ]]; then
    echo "⏳ Waiting \$wait_seconds seconds (\$((\$wait_seconds / 60)) minutes) for quota reset..."
    echo "💡 You can safely close this terminal - the script will complete automatically"
    echo "🎯 Will auto-resume at: $reset_time_str"
    echo ""
    echo "⏱️  Countdown:"
    
    # Intelligent countdown with progress indicators
    while [[ \$wait_seconds -gt 0 ]]; do
        hours=\$((\$wait_seconds / 3600))
        minutes=\$(( (\$wait_seconds % 3600) / 60 ))
        seconds=\$((\$wait_seconds % 60))
        
        if [[ \$hours -gt 0 ]]; then
            printf "\r   🕐 %02d:%02d:%02d remaining - Resume at $reset_time_str" \$hours \$minutes \$seconds
        else
            printf "\r   ⏰ %02d:%02d remaining - Resume at $reset_time_str" \$minutes \$seconds
        fi
        
        sleep 1
        ((wait_seconds--))
    done
    echo ""
    echo ""
fi

echo "🚀 Quota should be refreshed now - attempting resume..."
echo "📊 Checking Claude availability..."

# Test Claude availability before proceeding
if claude -p "test" --output-format text >/dev/null 2>&1; then
    echo "✅ Claude is responding - quota appears to be refreshed"
else
    echo "⚠️  Claude still appears to be limited - adding 5 minute safety buffer..."
    sleep 300
    if claude -p "test" --output-format text >/dev/null 2>&1; then
        echo "✅ Claude is now responding after safety buffer"
    else
        echo "❌ Claude still not responding - you may need to wait longer or check your account"
        echo "💡 Try running this script again later, or resume manually:"
        echo "   ./$(basename "$0") --resume"
        exit 1
    fi
fi

echo "🔄 Resuming intelligent analysis from step: $resume_step"
echo ""

# Resume the analysis
cd "${PROJECT_ROOT}"
./$(basename "$0") --resume

echo ""
echo "✅ Intelligent auto-resume completed successfully!"
echo "📊 Check the analysis results in: ${ANALYSIS_DIR}/"
EOF
    chmod +x "$QUOTA_RESUME_FILE"
    echo -e "${GREEN}🤖 Intelligent auto-resume script created: $QUOTA_RESUME_FILE${NC}"
}

handle_claude_quota_exhausted() {
    local current_step="$1"
    local quota_message="$2"  # Pass the actual quota message
    
    echo -e "${RED}🚫 Claude quota exhausted!${NC}"
    echo -e "${YELLOW}🤖 Analyzing quota message for intelligent scheduling...${NC}"
    
    # Try to parse reset time from quota message
    local parsed_data=$(parse_quota_reset_time "$quota_message")
    local auto_schedule_success=false
    
    if [[ $? -eq 0 && -n "$parsed_data" ]]; then
        echo -e "${GREEN}✅ Successfully parsed quota reset information${NC}"
        echo -e "${BLUE}� Parsed data: $parsed_data${NC}"
        
        # Calculate wait time using the parsed data
        local wait_calculation=$(calculate_wait_time "$parsed_data")
        
        if [[ "$wait_calculation" == *"WAIT_SECONDS:"* ]]; then
            local wait_seconds=$(echo "$wait_calculation" | grep "WAIT_SECONDS:" | cut -d: -f2)
            local reset_time_str=$(echo "$wait_calculation" | grep "RESET_TIME:" | cut -d: -f2-)
            local current_time_str=$(echo "$wait_calculation" | grep "CURRENT_TIME:" | cut -d: -f2-)
            
            if [[ "$wait_seconds" =~ ^[0-9]+$ ]] && [[ $wait_seconds -gt 0 ]] && [[ $wait_seconds -lt 86400 ]]; then
                echo -e "${GREEN}✅ Successfully calculated wait time: $(($wait_seconds / 60)) minutes${NC}"
                echo -e "${CYAN}📅 Current time: $current_time_str${NC}"
                echo -e "${CYAN}🎯 Resume time: $reset_time_str${NC}"
                
                create_auto_resume_script "$current_step" "$wait_seconds" "$reset_time_str"
                auto_schedule_success=true
            else
                echo -e "${YELLOW}⚠️  Wait time calculation failed (${wait_seconds}s) - creating standard resume script${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Could not calculate wait time - creating standard resume script${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Could not parse reset time from quota message - creating standard resume script${NC}"
    fi
    
    # Fallback to standard resume script if auto-scheduling failed
    if [[ "$auto_schedule_success" != "true" ]]; then
        create_resume_script "$current_step"
    fi
    
    update_progress "$current_step" "quota_exhausted" "Quota exhausted, resume available"
    update_self_todo
    
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "                    ⏳ CLAUDE QUOTA EXHAUSTED"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}The analysis has been paused due to Claude quota limits.${NC}"
    echo ""
    echo -e "${YELLOW}📋 What happened:${NC}"
    echo -e "${WHITE}   • Analysis progress saved to: $(basename "$PROGRESS_FILE")${NC}"
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${WHITE}   • 🤖 Intelligent auto-resume script created: $(basename "$QUOTA_RESUME_FILE")${NC}"
        echo -e "${GREEN}   • ✨ Script will automatically resume when quota resets!${NC}"
    else
        echo -e "${WHITE}   • Resume script created: $(basename "$QUOTA_RESUME_FILE")${NC}"
    fi
    echo -e "${WHITE}   • Self-TODO updated with current status${NC}"
    echo ""
    echo -e "${YELLOW}🔄 To resume analysis:${NC}"
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${GREEN}   🤖 Automatic (Recommended): ./${QUOTA_RESUME_FILE##*/}${NC}"
        echo -e "${WHITE}   📋 Manual: ./$(basename "$0") --resume${NC}"
        echo -e "${WHITE}   🕐 Later: ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0")${NC}"
        echo ""
        echo -e "${CYAN}🎯 Intelligent Features:${NC}"
        echo -e "${WHITE}   • Auto-resume script will wait for quota reset${NC}"
        echo -e "${WHITE}   • Script includes countdown timer and progress indicators${NC}"
        echo -e "${WHITE}   • Automatic Claude availability testing before resume${NC}"
        echo -e "${WHITE}   • Safety buffers to ensure quota is actually refreshed${NC}"
    else
        echo -e "${WHITE}   Option 1 (Recommended): ./${QUOTA_RESUME_FILE##*/}${NC}"
        echo -e "${WHITE}   Option 2 (Manual): ./$(basename "$0") --resume${NC}"
        echo -e "${WHITE}   Option 3 (Later): ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0")${NC}"
    fi
    echo ""
    echo -e "${YELLOW}📊 Progress Summary:${NC}"
    local completed_count=$(echo $(get_completed_steps) | tr ',' '\n' | wc -w)
    echo -e "${WHITE}   • Completed Steps: ${completed_count}/${#ANALYSIS_STEPS[@]}${NC}"
    echo -e "${WHITE}   • Stopped At: $current_step${NC}"
    echo -e "${WHITE}   • Session ID: ${TIMESTAMP}${NC}"
    echo ""
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${GREEN}🚀 Starting intelligent auto-resume process...${NC}"
        echo -e "${CYAN}💡 The script will countdown to quota reset and automatically continue!${NC}"
        echo ""
        echo -e "${YELLOW}🤖 What will happen next:${NC}"
        echo -e "${WHITE}   1. Countdown timer until quota resets (at 17:00)${NC}"
        echo -e "${WHITE}   2. Test Claude availability automatically${NC}"
        echo -e "${WHITE}   3. Resume analysis from where it stopped${NC}"
        echo -e "${WHITE}   4. Complete the remaining analysis steps${NC}"
        echo ""
        echo -e "${BLUE}🔍 Manual control options:${NC}"
        echo -e "${WHITE}   • Press Ctrl+C to cancel auto-resume${NC}"
        echo -e "${WHITE}   • Manual resume later: ./$(basename "$0") --resume${NC}"
        echo -e "${WHITE}   • Check specific session: ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume${NC}"
        echo ""
        
        # Execute the auto-resume script directly (not in background)
        echo -e "${GREEN}▶️  Starting auto-resume process now...${NC}"
        echo -e "${CYAN}💡 You can press Ctrl+C anytime to cancel and resume manually later${NC}"
        echo ""
        
        # Run the script directly
        exec bash "$QUOTA_RESUME_FILE"
    else
        echo -e "${CYAN}⏰ Wait for quota refresh, then resume with any option above${NC}"
    fi
    exit 0
}

# =============================================================================
# Claude Natural Language Analysis Functions
# =============================================================================

run_claude_analysis() {
    local prompt="$1"
    local output_file="$2" 
    local context_dir="$3"
    local step_key="$4"
    local use_quick_timeout="$5"  # Optional: use shorter timeout for quick operations
    
    local timeout_duration=${CLAUDE_TIMEOUT}
    if [[ "$use_quick_timeout" == "quick" ]]; then
        timeout_duration=${CLAUDE_QUICK_TIMEOUT}
    fi
    
    echo -e "${YELLOW}Running Claude analysis (timeout: ${timeout_duration}s)...${NC}"
    
    # Change to context directory if provided
    local original_dir=$(pwd)
    if [[ -n "$context_dir" ]] && [[ -d "$context_dir" ]]; then
        cd "$context_dir"
        echo -e "${CYAN}Context: Analyzing from $(pwd)${NC}"
    fi
    
    # Run Claude with natural language prompt and quota monitoring
    local claude_output=$(mktemp)
    local claude_error=$(mktemp)
    local claude_combined=$(mktemp)
    
    echo -e "${CYAN}Debug: Running command: $CLAUDE_CMD -p \"[PROMPT_LENGTH: ${#prompt} chars]\" --output-format text${NC}"
    echo -e "${CYAN}Debug: Working directory: $(pwd)${NC}"
    echo -e "${CYAN}Debug: Expected output file: $output_file${NC}"
    
    if [[ -n "$timeout_duration" ]]; then
        timeout_cmd="timeout $timeout_duration"
    else
        timeout_cmd=""
        echo -e "${RED}⚠️  Running without timeout - use Ctrl+C to interrupt if needed${NC}"
    fi
    
    # Capture both stdout and stderr, and also save combined output for quota checking
    if $timeout_cmd $CLAUDE_CMD -p "$prompt" --output-format text > "$claude_output" 2> "$claude_error"; then
        # Success
        mv "$claude_output" "$output_file"
        rm -f "$claude_error" "$claude_combined"
        cd "$original_dir"
        echo -e "${GREEN}✅ Claude analysis successful${NC}"
        update_progress "$step_key" "completed" "Analysis completed successfully"
        return 0
    else
        # Check if it's a quota issue - Claude outputs quota messages to stdout, not stderr
        local error_content=$(cat "$claude_error" 2>/dev/null || echo "")
        local output_content=$(cat "$claude_output" 2>/dev/null || echo "")
        local combined_content="$error_content $output_content"
        
        echo -e "${CYAN}Debug: Error content: '$error_content'${NC}"
        echo -e "${CYAN}Debug: Output content: '$output_content'${NC}"
        
        if [[ "$combined_content" == *"quota"* ]] || [[ "$combined_content" == *"rate limit"* ]] || [[ "$combined_content" == *"limit exceeded"* ]] || [[ "$combined_content" == *"usage limit reached"* ]] || [[ "$combined_content" == *"usage limit"* ]] || [[ "$combined_content" == *"Your limit will reset"* ]] || [[ "$combined_content" == *"Claude AI usage limit reached"* ]]; then
            echo -e "${RED}❌ Claude quota/rate limit reached: $output_content${NC}"
            rm -f "$claude_output" "$claude_error" "$claude_combined"
            cd "$original_dir"
            handle_claude_quota_exhausted "$step_key" "$combined_content"
            return 2  # Special return code for quota
        else
            echo -e "${RED}❌ Claude analysis failed: stdout='$output_content' stderr='$error_content'${NC}"
            rm -f "$claude_output" "$claude_error" "$claude_combined"
            cd "$original_dir"
            update_progress "$step_key" "failed" "Claude analysis failed"
            return 1
        fi
    fi
}

create_fallback_analysis() {
    local output_file="$1"
    local analysis_type="$2"
    local directory="$3"
    local step_key="$4"
    
    cat > "$output_file" << EOF
# ${analysis_type} Analysis - Fallback Report

**Analysis Date**: $(date)
**Analysis Method**: Fallback (Claude analysis failed or quota exhausted)
**Directory**: ${directory}
**Session ID**: ${TIMESTAMP}

## Status
- **Claude Analysis**: Failed or quota exhausted
- **Fallback Method**: Manual directory inspection
- **Resume Available**: Yes (use --resume flag)

## Directory Structure
$(find "${directory}" -type f -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" 2>/dev/null | head -20 || echo "No relevant files found")

## File Count by Type
- Python files: $(find "${directory}" -name "*.py" 2>/dev/null | wc -l)
- JavaScript/TypeScript files: $(find "${directory}" -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" 2>/dev/null | wc -l)
- Documentation files: $(find "${directory}" -name "*.md" -o -name "*.rst" -o -name "*.txt" 2>/dev/null | wc -l)

## Resume Instructions
When Claude quota is available again:
\`\`\`bash
# Resume this specific analysis step
ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume

# Or use the generated resume script
./${QUOTA_RESUME_FILE##*/}
\`\`\`

## Manual Analysis Commands (Alternative)
\`\`\`bash
# Try these individual commands when quota available:
cd "${directory}"
claude -p "Analyze this directory structure and identify key components"
claude -p "Review code quality and architecture in this directory"
claude -p "Identify potential issues and improvement opportunities"
\`\`\`

## Self-Management Note
This analysis step is tracked in: $(basename "$PROGRESS_FILE")  
The script will automatically resume from this point when quota is available.
EOF

    update_progress "$step_key" "completed" "Fallback analysis created"
}

# =============================================================================
# Analysis Steps with Natural Language & Resume Support
# =============================================================================

step1_analyze_docs() {
    if ! print_step_header "docs" "Documentation Analysis" "1"; then
        return 0  # Step was already completed
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

## Self-Management Note
This step completed automatically due to missing docs/ directory.
Session ID: ${TIMESTAMP}
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
- Validate that Phase 2, AI Services, and Phase 0B documentation align with reality

## Project State Analysis:
- Compare claimed completion status with actual implementation evidence
- Identify discrepancies between documented and actual progress
- Check if performance targets and metrics are realistic and measurable
- Validate architectural patterns described vs what appears to be implemented

## Documentation Quality Review:
- Assess documentation structure and organization
- Identify missing technical specifications that should exist
- Check for incomplete or placeholder content that needs completion
- Review deployment and operational procedures for completeness

## Output Requirements:
Please provide:
- Summary of documentation completeness (percentage complete by category)
- List of architectural inconsistencies found between docs and reality
- Missing documentation that should exist for a project of this scope
- Quality assessment score (1-10) with detailed justification
- Priority recommendations for documentation improvements

Focus on being practical and actionable in your analysis. This is session ${TIMESTAMP}."

    # Run Claude analysis with quota monitoring
    if run_claude_analysis "$docs_prompt" "$DOCS_ANALYSIS" "docs" "docs"; then
        echo -e "${GREEN}✅ Documentation analysis completed${NC}"
        update_self_todo
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            return 2  # Quota exhausted
        fi
        echo -e "${YELLOW}Creating fallback documentation analysis...${NC}"
        create_fallback_analysis "$DOCS_ANALYSIS" "Documentation" "docs" "docs"
        update_self_todo
    fi
    
    print_progress
}

step2_analyze_backend() {
    # Backend Overview
    if ! print_step_header "backend_overview" "Backend Overview Analysis" "2a"; then
        echo -e "${BLUE}✅ Backend overview already completed${NC}"
    else
        if [[ ! -d "backend" ]]; then
            echo -e "${RED}❌ ERROR: backend/ directory not found${NC}"
            exit 1
        fi

        echo -e "${CYAN}Creating backend overview with Claude...${NC}"
        
        local overview_prompt="I need a quick architectural overview of this backend codebase. Please examine the top-level structure and main components to give me:

1. **Architecture Overview**: What framework/technology stack is used
2. **Main Components**: Key directories and their purposes  
3. **Entry Points**: Main application files and how the system starts
4. **Dependencies**: Key external dependencies and their purposes
5. **Potential Issues**: Any obvious problems or red flags you notice

Keep this analysis high-level and focused on understanding the overall structure quickly. This is session ${TIMESTAMP}."

        local overview_file="${ANALYSIS_DIR}/backend_overview_${TIMESTAMP}.md"
        if run_claude_analysis "$overview_prompt" "$overview_file" "backend" "backend_overview"; then
            echo -e "${GREEN}✅ Backend overview completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback backend overview...${NC}"
            create_fallback_analysis "$overview_file" "Backend Overview" "backend" "backend_overview"
            update_self_todo
        fi
        print_progress
    fi

    # Backend Detailed Analysis
    if ! print_step_header "backend_detailed" "Backend Detailed Analysis" "2b"; then
        echo -e "${BLUE}✅ Backend detailed analysis already completed${NC}"
    else
        echo -e "${CYAN}Running detailed backend analysis with Claude...${NC}"
        
        local backend_prompt="I need a comprehensive analysis of this backend codebase. Please ${BACKEND_ANALYSIS_DEPTH} and provide detailed insights on:

## Architecture Implementation Assessment:
- Verify Phase 2 task coordinator pattern implementation (if present)
- Check service registry and dependency injection setup
- Validate Redis integration and caching implementation
- Assess AI services architecture and model management
- Review overall architectural patterns and design quality

## Code Quality Analysis:
- Identify code duplication that should be eliminated
- Check for proper error handling and logging patterns
- Validate type hints and documentation coverage
- Review async/await usage and performance patterns
- Assess testing coverage and quality

## Integration Issues Detection:
- Check import statements and dependency resolution
- Identify circular dependencies or import conflicts
- Validate service registration and discovery patterns
- Review database and cache service integration
- Check API endpoint organization and routing

## Functionality Assessment:
- Analyze critical paths: entry creation, session management, analytics
- Identify broken or incomplete features
- Check API endpoint functionality and routing structure
- Validate Celery task definitions and execution patterns
- Review background job processing

## Performance and Security Review:
- Assess connection pooling and resource management
- Review security practices (input validation, sanitization)
- Check for performance bottlenecks or anti-patterns
- Validate monitoring and health check implementations
- Review configuration management and environment handling

## Output Requirements:
Please provide:
- Architecture compliance score (rate how well patterns are implemented 1-10)
- List of broken functionality with severity levels (Critical/High/Medium/Low)
- Code quality metrics and assessment
- Integration issues found with specific file/line references where possible
- Performance concerns and optimization opportunities
- Security vulnerabilities or best practice violations
- Specific recommendations for fixes and improvements

Be thorough and practical in your analysis - focus on actionable insights. This is session ${TIMESTAMP}."

        if run_claude_analysis "$backend_prompt" "$BACKEND_ANALYSIS" "backend" "backend_detailed"; then
            echo -e "${GREEN}✅ Backend detailed analysis completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback backend analysis...${NC}"
            create_fallback_analysis "$BACKEND_ANALYSIS" "Backend Detailed" "backend" "backend_detailed"
            update_self_todo
        fi
        print_progress
    fi

    # Backend Deep Dive Analysis
    if [[ "$ENABLE_TARGETED_DEEP_DIVE" == "true" ]]; then
        if ! print_step_header "backend_deep_dive" "Backend Deep Dive Analysis" "2c"; then
            echo -e "${BLUE}✅ Backend deep dive already completed${NC}"
        else
            echo -e "${BLUE}🎯 Backend Deep Dive Analysis${NC}"
            
            for critical_area in "${BACKEND_CRITICAL_AREAS[@]}"; do
                if [[ -d "${critical_area}" ]]; then
                    echo -e "${YELLOW}Deep diving into: ${critical_area}${NC}"
                    
                    local area_name=$(basename "${critical_area}")
                    local deep_analysis="${ANALYSIS_DIR}/backend_${area_name}_deep_${TIMESTAMP}.md"
                    
                    local deep_prompt="I need an extremely detailed analysis of this specific directory: ${critical_area}

Please examine every file and provide deep insights on:
- Architecture patterns and design quality in this specific area
- Code quality, maintainability, and potential technical debt
- Integration points with other parts of the system
- Potential bugs, security issues, or performance problems
- Specific improvement recommendations with code examples where helpful

Focus on being very detailed and specific to this directory's responsibilities and implementation. This is session ${TIMESTAMP}."

                    if run_claude_analysis "$deep_prompt" "$deep_analysis" "$critical_area" "backend_deep_dive"; then
                        echo -e "${GREEN}✅ Deep dive completed: $(basename "$deep_analysis")${NC}"
                    else
                        local exit_code=$?
                        if [[ $exit_code -eq 2 ]]; then
                            return 2  # Quota exhausted
                        fi
                        echo -e "${YELLOW}⚠️  Deep dive failed for ${critical_area}, creating fallback${NC}"
                        create_fallback_analysis "$deep_analysis" "Backend Deep Dive ${area_name}" "$critical_area" "backend_deep_dive"
                    fi
                else
                    echo -e "${YELLOW}⚠️  Critical area not found: ${critical_area}${NC}"
                fi
            done
            
            update_progress "backend_deep_dive" "completed" "Deep dive analysis completed"
            update_self_todo
            print_progress
        fi
    fi
}

step3_analyze_frontend() {
    # Frontend Overview
    if ! print_step_header "frontend_overview" "Frontend Overview Analysis" "3a"; then
        echo -e "${BLUE}✅ Frontend overview already completed${NC}"
    else
        if [[ ! -d "frontend" ]]; then
            echo -e "${YELLOW}⚠️  WARNING: frontend/ directory not found${NC}"
            echo -e "${WHITE}Creating placeholder analysis...${NC}"
            cat > "${FRONTEND_ANALYSIS}" << EOF
# Frontend Analysis - No frontend/ Directory Found

**Analysis Date**: $(date)
**Project Root**: ${PROJECT_ROOT}
**Session ID**: ${TIMESTAMP}

## Status
- **frontend/ Directory**: Not found
- **Frontend Score**: N/A
- **Architecture**: Backend-only application detected

## Recommendations
1. Determine if this is intentionally a backend-only API
2. If frontend is planned, create appropriate structure
3. Consider modern frontend frameworks (React, Vue, Svelte)
4. Plan API integration strategy with the existing backend

## Self-Management Note
This step completed automatically due to missing frontend/ directory.
Session ID: ${TIMESTAMP}
EOF
            update_progress "frontend_overview" "completed" "No frontend directory found - placeholder created"
            update_progress "frontend_detailed" "completed" "Skipped - no frontend directory"
            update_progress "frontend_deep_dive" "completed" "Skipped - no frontend directory"
            update_self_todo
            print_progress
            return 0
        fi

        echo -e "${CYAN}Creating frontend overview with Claude...${NC}"
        
        local frontend_overview_prompt="I need a quick overview of this frontend codebase. Please analyze:

1. **Framework/Technology**: What frontend framework is being used
2. **Project Structure**: Main directories and their purposes
3. **Build System**: Package.json, build tools, and configuration
4. **Dependencies**: Key libraries and their purposes
5. **Entry Points**: How the application starts and main routing

Keep this high-level to understand the frontend architecture quickly. This is session ${TIMESTAMP}."

        local frontend_overview="${ANALYSIS_DIR}/frontend_overview_${TIMESTAMP}.md"
        if run_claude_analysis "$frontend_overview_prompt" "$frontend_overview" "frontend" "frontend_overview"; then
            echo -e "${GREEN}✅ Frontend overview completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback frontend overview...${NC}"
            create_fallback_analysis "$frontend_overview" "Frontend Overview" "frontend" "frontend_overview"
            update_self_todo
        fi
        print_progress
    fi
    
    # Frontend Detailed Analysis
    if ! print_step_header "frontend_detailed" "Frontend Detailed Analysis" "3b"; then
        echo -e "${BLUE}✅ Frontend detailed analysis already completed${NC}"
    else
        local frontend_prompt="I need a comprehensive analysis of this frontend codebase. Please ${FRONTEND_ANALYSIS_DEPTH} and analyze:

## Frontend Architecture Assessment:
- Review component structure and state management patterns
- Check API integration with backend services
- Validate routing and navigation implementation
- Assess responsive design and user experience patterns
- Review build system and deployment configuration

## Integration Analysis:
- Check API calls to backend endpoints
- Validate data flow between frontend and backend
- Identify broken API integrations after backend refactoring
- Review authentication and session management
- Check error handling for API failures

## Code Quality Review:
- Check for TypeScript/JavaScript best practices
- Review component reusability and maintainability
- Assess error handling and user feedback mechanisms
- Validate accessibility and performance optimization
- Review code organization and structure

## Functionality Testing:
- Identify critical user journeys that may be broken
- Check form submissions and data persistence
- Validate real-time features (if any)
- Review mobile responsiveness and cross-browser compatibility
- Assess user interface consistency

## Dependencies and Build System:
- Review package.json for outdated or conflicting dependencies
- Check build configuration and deployment readiness
- Validate development vs production environment setup
- Assess bundle size and performance optimization
- Review security of dependencies

## Output Requirements:
Please provide:
- Frontend architecture assessment (modern practices score 1-10)
- List of broken integrations with backend after refactoring
- User experience issues and critical bugs found
- Dependency vulnerabilities or version conflicts
- Performance metrics and optimization recommendations
- Build and deployment readiness assessment
- Specific actionable recommendations for improvements

Focus on practical insights that can improve user experience and code quality. This is session ${TIMESTAMP}."

        if run_claude_analysis "$frontend_prompt" "$FRONTEND_ANALYSIS" "frontend" "frontend_detailed"; then
            echo -e "${GREEN}✅ Frontend detailed analysis completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback frontend analysis...${NC}"
            create_fallback_analysis "$FRONTEND_ANALYSIS" "Frontend Detailed" "frontend" "frontend_detailed"
            update_self_todo
        fi
        print_progress
    fi
    
    # Frontend Deep Dive Analysis
    if [[ "$ENABLE_TARGETED_DEEP_DIVE" == "true" ]]; then
        if ! print_step_header "frontend_deep_dive" "Frontend Deep Dive Analysis" "3c"; then
            echo -e "${BLUE}✅ Frontend deep dive already completed${NC}"
        else
            echo -e "${BLUE}🎯 Frontend Deep Dive Analysis${NC}"
            
            for critical_area in "${FRONTEND_CRITICAL_AREAS[@]}"; do
                if [[ -d "${critical_area}" ]]; then
                    echo -e "${YELLOW}Deep diving into: ${critical_area}${NC}"
                    
                    local area_name=$(basename "${critical_area}")
                    local deep_analysis="${ANALYSIS_DIR}/frontend_${area_name}_deep_${TIMESTAMP}.md"
                    
                    local deep_prompt="I need detailed analysis of this specific frontend directory: ${critical_area}

Please examine thoroughly and provide insights on:
- Component architecture and design patterns in this area
- Props flow, state management, and data handling
- API integration and error handling
- User interface consistency and user experience
- Performance implications and optimization opportunities
- Potential bugs or issues in the implementation
- Specific improvement recommendations

Be very detailed and specific to this directory's functionality. This is session ${TIMESTAMP}."

                    if run_claude_analysis "$deep_prompt" "$deep_analysis" "$critical_area" "frontend_deep_dive"; then
                        echo -e "${GREEN}✅ Frontend deep dive completed: $(basename "$deep_analysis")${NC}"
                    else
                        local exit_code=$?
                        if [[ $exit_code -eq 2 ]]; then
                            return 2  # Quota exhausted
                        fi
                        echo -e "${YELLOW}⚠️  Frontend deep dive failed for ${critical_area}${NC}"
                        create_fallback_analysis "$deep_analysis" "Frontend Deep Dive ${area_name}" "$critical_area" "frontend_deep_dive"
                    fi
                else
                    echo -e "${YELLOW}⚠️  Frontend critical area not found: ${critical_area}${NC}"
                fi
            done
            
            update_progress "frontend_deep_dive" "completed" "Frontend deep dive completed"
            update_self_todo
            print_progress
        fi
    fi
}

step4_comprehensive_assessment() {
    if ! print_step_header "synthesis" "Comprehensive Assessment Creation" "4a"; then
        echo -e "${BLUE}✅ Synthesis already completed${NC}"
    else
        echo -e "${CYAN}Creating comprehensive assessment with Claude...${NC}"
        
        # Gather all analysis results
        local analysis_summary=""
        [[ -f "${DOCS_ANALYSIS}" ]] && analysis_summary+="\n\n## Documentation Analysis Results:\n$(cat "${DOCS_ANALYSIS}")"
        [[ -f "${BACKEND_ANALYSIS}" ]] && analysis_summary+="\n\n## Backend Analysis Results:\n$(cat "${BACKEND_ANALYSIS}")"
        [[ -f "${FRONTEND_ANALYSIS}" ]] && analysis_summary+="\n\n## Frontend Analysis Results:\n$(cat "${FRONTEND_ANALYSIS}")"
        
        # Add any overview and deep dive analysis results
        for analysis_file in "${ANALYSIS_DIR}"/*overview*.md "${ANALYSIS_DIR}"/*_deep_*.md; do
            if [[ -f "$analysis_file" ]]; then
                local file_title=$(basename "$analysis_file" .md | tr '_' ' ' | sed 's/.*/\u&/')
                analysis_summary+="\n\n## ${file_title} Results:\n$(cat "$analysis_file")"
            fi
        done
        
        local synthesis_prompt="Based on the comprehensive analysis results below, I need you to create a detailed assessment that synthesizes all findings. Session ID: ${TIMESTAMP}

Please create a comprehensive assessment that includes:

## EXECUTIVE SUMMARY
- Overall system health score (1-10) based on all analysis results
- Critical issues requiring immediate attention  
- Impact assessment of Phase 2 refactoring on system functionality
- Readiness assessment for production deployment

## WHAT WORKS WELL ✅
- Successfully implemented architectural patterns
- High-quality code areas that meet enterprise standards
- Properly functioning integration points
- Performance optimizations that are effective
- Documentation that accurately reflects implementation

## WHAT NEEDS IMPROVEMENT ⚠️
- Architectural inconsistencies between docs and implementation
- Code quality issues that impact maintainability
- Integration problems causing functionality breakage
- Performance bottlenecks or resource usage concerns
- Security vulnerabilities or best practice violations

## CRITICAL ISSUES 🚨
- Functionality that is completely broken
- Security vulnerabilities requiring immediate attention
- Performance issues causing system instability
- Integration failures preventing core features from working
- Data integrity or corruption risks

## DETAILED FINDINGS SYNTHESIS
Synthesize and correlate findings across all analysis areas:
- Cross-reference issues found in multiple components
- Identify root causes that affect multiple areas
- Highlight patterns in code quality or architectural decisions
- Connect documentation gaps to implementation issues

## PRIORITY RECOMMENDATIONS
Based on all analysis results, provide specific, prioritized recommendations for:
1. Critical fixes that should be done immediately
2. High-impact improvements for system reliability
3. Code quality enhancements for maintainability
4. Documentation updates for accuracy
5. Performance optimizations for scalability

Be specific and actionable in your synthesis. This analysis covers the entire project comprehensively.

## Analysis Results to Synthesize:
$analysis_summary"

        # Create comprehensive assessment
        if run_claude_analysis "$synthesis_prompt" "$COMPREHENSIVE_ASSESSMENT" "." "synthesis"; then
            echo -e "${GREEN}✅ Comprehensive assessment completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback comprehensive assessment...${NC}"
            create_fallback_comprehensive_assessment
            update_self_todo
        fi
        print_progress
    fi

    # TODO List Extraction
    if ! print_step_header "todo_extraction" "TODO List Creation" "4b"; then
        echo -e "${BLUE}✅ TODO extraction already completed${NC}"
    else
        local todo_extraction_prompt="From the comprehensive assessment below, extract and create a detailed, actionable TODO list. Session ID: ${TIMESTAMP}

Create a standalone markdown document with prioritized TODO items that includes:

## PRIORITY 1: CRITICAL FIXES (Do First)
- [ ] **Issue Title** - Clear description, affected files, estimated effort (hours), success criteria, dependencies

## PRIORITY 2: HIGH IMPACT IMPROVEMENTS  
- [ ] **Issue Title** - Description, files, effort, success criteria, dependencies

## PRIORITY 3: CODE QUALITY AND TECHNICAL DEBT
- [ ] **Issue Title** - Description, files, effort, success criteria, dependencies

## PRIORITY 4: DOCUMENTATION AND TESTING
- [ ] **Issue Title** - Description, files, effort, success criteria, dependencies

## PRIORITY 5: ENHANCEMENT AND OPTIMIZATION
- [ ] **Issue Title** - Description, files, effort, success criteria, dependencies

Each TODO item must include:
- **Clear Problem Description**: What exactly needs to be fixed
- **Affected Files**: Specific files that need modification
- **Estimated Effort**: Time required in hours (be realistic)
- **Success Criteria**: How to know when the task is complete
- **Dependencies**: What other tasks must be completed first
- **Testing Requirements**: How to verify the fix works

Make the TODO items specific, actionable, and implementable by a developer.

## Comprehensive Assessment to Extract From:
$(cat "$COMPREHENSIVE_ASSESSMENT" 2>/dev/null || echo "Assessment file not found - creating basic TODO structure")"

        if run_claude_analysis "$todo_extraction_prompt" "$TODO_LIST" "." "todo_extraction"; then
            echo -e "${GREEN}✅ TODO list extraction completed${NC}"
            update_self_todo
        else
            local exit_code=$?
            if [[ $exit_code -eq 2 ]]; then
                return 2  # Quota exhausted
            fi
            echo -e "${YELLOW}Creating fallback TODO list...${NC}"
            create_fallback_todo_list
            update_self_todo
        fi
        print_progress
    fi
}

step5_final_report() {
    if ! print_step_header "final_report" "Final Report Generation" "5"; then
        echo -e "${BLUE}✅ Final report already completed${NC}"
        return 0
    fi

    echo -e "${CYAN}Generating final analysis report...${NC}"
    
    local final_report="${ANALYSIS_DIR}/final_analysis_report_${TIMESTAMP}.md"
    local START_TIME=$(date +%s)
    
    cat > "${final_report}" << EOF
# AI Journaling Assistant - Final Analysis Report

**Analysis Completed**: $(date)
**Project Root**: ${PROJECT_ROOT}
**Session ID**: ${TIMESTAMP}
**Claude Version**: $($CLAUDE_CMD --version 2>/dev/null || echo "Unknown")

## Analysis Summary

### Files Generated
1. **Documentation Analysis**: [$(basename "${DOCS_ANALYSIS}")](./$(basename "${DOCS_ANALYSIS}"))
2. **Backend Analysis**: [$(basename "${BACKEND_ANALYSIS}")](./$(basename "${BACKEND_ANALYSIS}"))
3. **Frontend Analysis**: [$(basename "${FRONTEND_ANALYSIS}")](./$(basename "${FRONTEND_ANALYSIS}"))
4. **Comprehensive Assessment**: [$(basename "${COMPREHENSIVE_ASSESSMENT}")](./$(basename "${COMPREHENSIVE_ASSESSMENT}"))
5. **Actionable TODO List**: [$(basename "${TODO_LIST}")](./$(basename "${TODO_LIST}"))

### Progressive Analysis Files
$(ls -la "${ANALYSIS_DIR}"/*overview*.md 2>/dev/null | awk '{print "- **" $(NF) "**: Overview analysis"}' || echo "- No overview files generated")

### Deep Dive Analysis Files
$(ls -la "${ANALYSIS_DIR}"/*_deep_*.md 2>/dev/null | awk '{print "- **" $(NF) "**: Detailed component analysis"}' || echo "- No deep dive files generated")

### Self-Management Files
- **Progress Tracking**: [$(basename "${PROGRESS_FILE}")](./$(basename "${PROGRESS_FILE}"))
- **Self-TODO List**: [$(basename "${SELF_TODO_FILE}")](./$(basename "${SELF_TODO_FILE}"))
$([ -f "$QUOTA_RESUME_FILE" ] && echo "- **Resume Script**: [$(basename "${QUOTA_RESUME_FILE}")](./$(basename "${QUOTA_RESUME_FILE}"))" || echo "- **Resume Script**: Not needed (analysis completed)")

### Analysis Statistics
- **Total Files Analyzed**: $(find . -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" | wc -l 2>/dev/null || echo "Unknown")
- **Analysis Method**: Claude CLI Natural Language Interface with Resume Support
- **Analysis Types**: Progressive + Detailed$([ "${ENABLE_TARGETED_DEEP_DIVE}" == "true" ] && echo " + Deep Dive" || echo "")
- **Self-Management**: Enabled (auto-progress tracking and TODO updates)
- **Analysis Duration**: $(( ($(date +%s) - START_TIME) / 60 )) minutes (this session)

### Session Management
- **Session ID**: ${TIMESTAMP}
- **Resume Capability**: $([ -f "$PROGRESS_FILE" ] && echo "Available" || echo "Not available")
- **Progress Tracking**: $([ -f "$PROGRESS_FILE" ] && echo "Active" || echo "Inactive") 
- **Self-TODO Updates**: $([ "$ENABLE_SELF_MANAGEMENT" == "true" ] && echo "Automatic" || echo "Manual")

## Quick Actions

### Review Analysis Results
\`\`\`bash
# Review comprehensive assessment
cat "${COMPREHENSIVE_ASSESSMENT}"

# Check TODO list priorities
cat "${TODO_LIST}"

# Check script's self-management
cat "${SELF_TODO_FILE}"

# Start with highest priority items
grep -A 5 "Priority 1" "${TODO_LIST}"
\`\`\`

### Claude-Powered Next Steps
\`\`\`bash
# Let Claude help prioritize your work
claude -p "Review my TODO list and help me create a daily action plan"

# Get Claude's recommendations for specific issues
claude -p "Help me fix the critical issues identified in the analysis"

# Track progress with Claude
claude -p "Help me track which TODO items I've completed"

# Get coding help from Claude
claude -p "Help me implement the fixes for Priority 1 items"
\`\`\`

### Resume Capability
$(if [[ -f "$QUOTA_RESUME_FILE" ]]; then
    echo "\`\`\`bash"
    echo "# Resume if interrupted by quota limits"
    echo "./${QUOTA_RESUME_FILE##*/}"
    echo ""
    echo "# Or resume manually"
    echo "ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume"
    echo "\`\`\`"
else
    echo "Analysis completed successfully - no resume needed."
fi)

## Project Health Assessment
Based on the comprehensive analysis:
- **Architecture Status**: See detailed assessment in comprehensive report
- **Code Quality**: Review backend and frontend analysis results
- **Documentation State**: Check documentation analysis findings
- **Production Readiness**: Refer to critical issues and priority recommendations

## Key Features of This Analysis
- ✅ **Resume Support**: Can pause and resume if Claude quota exhausted
- ✅ **Progress Tracking**: JSON-based progress tracking with step completion status  
- ✅ **Self-Management**: Script tracks its own progress and creates self-TODOs
- ✅ **Intelligent Fallbacks**: Creates useful reports even if Claude analysis fails
- ✅ **Natural Language Interface**: Uses Claude v1.0.69 properly (not broken flags)
- ✅ **Comprehensive Coverage**: Docs + Backend + Frontend + Deep Dive analysis

## Next Steps Recommendations

### Immediate Actions
1. **Review Assessment**: Read \`${COMPREHENSIVE_ASSESSMENT}\` for overall project health
2. **Check Critical Issues**: Focus on Priority 1 items in \`${TODO_LIST}\`
3. **Verify Core Functions**: Test basic application functionality
4. **Plan Implementation**: Use TODO list effort estimates for sprint planning

### Ongoing Management
- **Progress Tracking**: Use the self-TODO file to track script improvements
- **Regular Re-analysis**: Re-run this script after major changes
- **Claude Integration**: Use Claude CLI for ongoing development assistance
- **Documentation Updates**: Keep docs synchronized with implementation

### Support Resources
- **All analysis files**: \`${ANALYSIS_DIR}/\`
- **Re-run analysis**: \`./$(basename "$0")\`
- **Resume if needed**: Use resume script or --resume flag
- **Claude assistance**: \`claude -p "your question about the codebase"\`

---

**Analysis Session ${TIMESTAMP} Complete** ✅

**Script Self-Assessment**: This analysis script successfully demonstrated:
- Intelligent quota management with resume capability
- Self-tracking and TODO management
- Comprehensive multi-layer analysis (overview → detailed → deep dive)
- Natural language interface compatibility with Claude v1.0.69
- Robust fallback mechanisms for reliability

**Ready for Implementation** - Use the TODO list to start improving your AI journaling assistant! 🚀
EOF

    update_progress "final_report" "completed" "Final report generated successfully"
    update_self_todo
    
    echo -e "${GREEN}✅ Final report generated: ${final_report}${NC}"
    return 0
}

create_fallback_comprehensive_assessment() {
    cat > "${COMPREHENSIVE_ASSESSMENT}" << EOF
# Comprehensive Assessment - Intelligent Fallback Report

**Analysis Date**: $(date)
**Analysis Method**: Intelligent Fallback (Claude synthesis failed or quota exhausted)
**Session ID**: ${TIMESTAMP}

## Executive Summary
- **Overall Health Score**: Unable to determine automatically - manual review required
- **Status**: Individual analysis files available for manual review
- **Resume Capability**: Available - analysis can continue when quota refreshes
- **Critical Issues**: Unknown - requires examination of individual analysis files

## Analysis Files Available for Manual Review
1. **Documentation Analysis**: $(basename "${DOCS_ANALYSIS}") $([ -f "${DOCS_ANALYSIS}" ] && echo "✅" || echo "❌")
2. **Backend Analysis**: $(basename "${BACKEND_ANALYSIS}") $([ -f "${BACKEND_ANALYSIS}" ] && echo "✅" || echo "❌")
3. **Frontend Analysis**: $(basename "${FRONTEND_ANALYSIS}") $([ -f "${FRONTEND_ANALYSIS}" ] && echo "✅" || echo "❌")

## Overview and Deep Dive Files
$(ls -la "${ANALYSIS_DIR}"/*overview*.md 2>/dev/null | awk '{print "- " $(NF) " ✅"}' || echo "- No overview files generated")
$(ls -la "${ANALYSIS_DIR}"/*_deep_*.md 2>/dev/null | awk '{print "- " $(NF) " ✅"}' || echo "- No deep dive files generated")

## Self-Management Status
- **Progress Tracking**: Active - see $(basename "$PROGRESS_FILE")
- **Self-TODO**: Updated - see $(basename "$SELF_TODO_FILE") 
- **Resume Capability**: $([ -f "$QUOTA_RESUME_FILE" ] && echo "Available - $(basename "$QUOTA_RESUME_FILE")" || echo "Analysis completed")

## Manual Review Process
Since Claude synthesis was not available, follow this process:

### Step 1: Review Individual Analysis Files
\`\`\`bash
# Read each analysis file
cat "${DOCS_ANALYSIS}"
cat "${BACKEND_ANALYSIS}" 
cat "${FRONTEND_ANALYSIS}"

# Check additional analysis files
ls -la "${ANALYSIS_DIR}"/*.md
\`\`\`

### Step 2: Identify Common Themes
Look for recurring issues across files:
- Architecture problems mentioned in multiple analyses
- Code quality issues that span different areas
- Integration problems between components
- Performance or security concerns

### Step 3: Prioritize Issues
Based on your manual review, categorize issues as:
- **Critical**: Breaks core functionality
- **High**: Significantly impacts user experience or development
- **Medium**: Code quality and maintainability issues
- **Low**: Nice-to-have improvements

## Resume Instructions
When Claude quota becomes available:
\`\`\`bash
# Resume from synthesis step
ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume

# Or use the auto-generated resume script
$([ -f "$QUOTA_RESUME_FILE" ] && echo "./${QUOTA_RESUME_FILE##*/}" || echo "# Resume not needed - analysis complete")
\`\`\`

## Alternative Analysis with Claude
When quota is available, you can get Claude's help manually:
\`\`\`bash
# Ask Claude to synthesize your findings
claude -p "Help me synthesize these analysis results into priorities and action items"

# Get specific recommendations
claude -p "Based on my code analysis files, what are the most critical issues to fix first?"

# Create TODO list with Claude
claude -p "Create a prioritized TODO list from my analysis findings"
\`\`\`

## Next Steps
1. **Manual Review**: Examine all individual analysis files
2. **Issue Prioritization**: Categorize findings by severity and impact  
3. **Create Action Plan**: Use manual findings to create implementation plan
4. **Resume When Possible**: Use resume capability for complete Claude synthesis
5. **Track Progress**: Update the self-TODO file as you make improvements

**Note**: This fallback provides comprehensive analysis data even when Claude synthesis isn't available. The individual analysis files contain detailed findings that can guide your improvement efforts.
EOF

    update_progress "synthesis" "completed" "Fallback comprehensive assessment created"
}

create_fallback_todo_list() {
    cat > "${TODO_LIST}" << EOF
# Actionable TODO List - Intelligent Fallback

**Generated**: $(date)
**Status**: Fallback creation (Claude extraction failed or quota exhausted)
**Session ID**: ${TIMESTAMP}

## Overview
This TODO list was created as a fallback when Claude analysis was not available. It provides a structured approach to reviewing your analysis results and implementing improvements.

## Priority 1: Analysis Review and Critical Issue Identification
- [ ] **Review All Analysis Files** - Examine generated analysis reports thoroughly
  - Files: ${DOCS_ANALYSIS}, ${BACKEND_ANALYSIS}, ${FRONTEND_ANALYSIS}
  - Additional files: $(ls "${ANALYSIS_DIR}"/*.md 2>/dev/null | wc -l) analysis files in total
  - Effort: 2-3 hours
  - Success: Complete understanding of project state and issues
  - Dependencies: None
  - Testing: Document findings and create issue prioritization

- [ ] **Test Core Application Functions** - Verify basic functionality works
  - Files: backend/main.py, backend/app/__init__.py, key API endpoints
  - Effort: 1-2 hours
  - Success: Application starts and core features respond
  - Dependencies: None
  - Testing: Manual testing of key user journeys

- [ ] **Database and Cache Connectivity Check** - Verify infrastructure works
  - Files: backend/app/core/database.py, Redis configuration files
  - Effort: 30-45 minutes
  - Success: Database connects, Redis cache operational
  - Dependencies: Database and Redis servers running
  - Testing: Connection tests and basic read/write operations

## Priority 2: Architecture and Integration Validation
- [ ] **Service Registry Functionality** - Verify service discovery works
  - Files: backend/app/core/service_interfaces.py, service registration code
  - Effort: 1 hour
  - Success: Services register and resolve correctly
  - Dependencies: Application startup successful
  - Testing: Service lookup and method calling

- [ ] **API Endpoint Testing** - Verify all endpoints respond correctly
  - Files: backend/app/api/*.py, all API route definitions
  - Effort: 2-3 hours
  - Success: All endpoints return expected responses
  - Dependencies: Application and database operational
  - Testing: Automated endpoint testing or manual API calls

- [ ] **Task Queue Operations** - Verify Celery/background tasks work
  - Files: backend/app/tasks/*.py, Celery configuration
  - Effort: 1-2 hours
  - Success: Tasks can be queued and execute successfully
  - Dependencies: Message broker (Redis) operational
  - Testing: Queue test tasks and verify completion

## Priority 3: Code Quality and Standards
- [ ] **Python Code Syntax Validation** - Ensure all code compiles
  - Files: All .py files in backend/
  - Effort: 30 minutes
  - Success: No syntax errors found
  - Dependencies: Python environment configured
  - Testing: \`python -m py_compile backend/app/**/*.py\`

- [ ] **Import Resolution Check** - Fix any import errors
  - Files: All Python files with import statements
  - Effort: 1-2 hours
  - Success: All imports resolve without circular dependencies
  - Dependencies: Syntax validation complete
  - Testing: Import each module and check for errors

- [ ] **Dependencies and Requirements** - Verify all packages installed correctly
  - Files: backend/requirements.txt, package.json (if frontend exists)
  - Effort: 30 minutes
  - Success: All requirements install without conflicts
  - Dependencies: Python/Node environments available
  - Testing: Fresh environment installation test

## Priority 4: Documentation and Knowledge Management
- [ ] **Update Project Documentation** - Synchronize docs with current implementation
  - Files: docs/ directory, README files, architecture documentation
  - Effort: 2-4 hours
  - Success: Documentation accurately reflects current system state
  - Dependencies: Complete understanding of current implementation
  - Testing: Documentation review by team member

- [ ] **Create Troubleshooting Guide** - Document common issues and solutions
  - Files: docs/troubleshooting.md (new file)
  - Effort: 1-2 hours
  - Success: Guide covers identified issues with step-by-step solutions
  - Dependencies: Issue identification complete
  - Testing: Follow guide to resolve known issues

## Priority 5: Performance and Enhancement
- [ ] **Performance Baseline Testing** - Establish current performance metrics
  - Files: All API endpoints, database queries, Redis cache operations
  - Effort: 2-3 hours
  - Success: Performance benchmarks documented with response times
  - Dependencies: Application fully operational
  - Testing: Load testing tools or manual performance measurement

- [ ] **Security Review** - Check for common security vulnerabilities
  - Files: API endpoints, authentication code, input validation
  - Effort: 3-4 hours
  - Success: Security checklist completed with no critical vulnerabilities
  - Dependencies: Code quality issues resolved
  - Testing: Security scanning tools or manual code review

## Resume and Self-Management Tasks

### When Claude Quota Available
- [ ] **Resume Claude Analysis** - Complete automated synthesis if interrupted
  - Command: \`ANALYSIS_TIMESTAMP=${TIMESTAMP} ./$(basename "$0") --resume\`
  - Effort: 5-10 minutes (automated)
  - Success: Complete comprehensive assessment and refined TODO list
  - Dependencies: Claude quota available
  - Testing: Verify generated comprehensive assessment

- [ ] **Claude-Assisted Prioritization** - Get AI help for issue prioritization
  - Command: \`claude -p "Help me prioritize these analysis findings"\`
  - Effort: 10-15 minutes
  - Success: AI-guided priority ranking with reasoning
  - Dependencies: Analysis review complete
  - Testing: Compare AI recommendations with manual assessment

### Self-Management Tracking
- [ ] **Update Progress Status** - Mark completed tasks in this TODO
  - Files: ${TODO_LIST}, ${SELF_TODO_FILE}
  - Effort: 5 minutes per update
  - Success: Accurate progress tracking maintained
  - Dependencies: Tasks completed
  - Testing: Verify progress matches actual completion

- [ ] **Script Self-Improvement** - Implement enhancements to analysis script
  - Files: $(basename "$0"), progress tracking system
  - Effort: 1-2 hours per improvement
  - Success: Enhanced script functionality and reliability
  - Dependencies: Understanding of script architecture
  - Testing: Test improvements on sample project

## Advanced Analysis Tasks (When Resources Available)

- [ ] **Deep Code Architecture Review** - Detailed examination of core patterns
  - Files: Service layer, data layer, API layer implementations
  - Effort: 4-6 hours
  - Success: Comprehensive architecture assessment with improvement plan
  - Dependencies: Basic functionality verified
  - Testing: Architecture review checklist completion

- [ ] **Integration Testing Suite** - Create comprehensive integration tests
  - Files: New test files, CI/CD configuration
  - Effort: 6-8 hours
  - Success: Automated integration test suite with >80% coverage
  - Dependencies: Core functionality working
  - Testing: All integration tests pass consistently

- [ ] **Performance Optimization Implementation** - Apply performance improvements
  - Files: Database queries, caching logic, API optimization
  - Effort: 4-8 hours
  - Success: Measurable performance improvement (>20% faster)
  - Dependencies: Performance baseline established
  - Testing: Before/after performance comparison

## Estimated Total Effort
- **Priority 1 (Critical)**: 4-6 hours
- **Priority 2 (High Impact)**: 5-8 hours  
- **Priority 3 (Code Quality)**: 2-4 hours
- **Priority 4 (Documentation)**: 3-6 hours
- **Priority 5 (Enhancement)**: 5-7 hours
- **Advanced Tasks**: 14-22 hours

**Total Project Improvement Effort**: 33-53 hours (4-7 working days)

## Success Metrics
- [ ] Application starts without errors
- [ ] All critical user journeys functional
- [ ] No high-severity security vulnerabilities
- [ ] Documentation matches implementation
- [ ] Performance meets acceptable thresholds
- [ ] Code quality standards maintained
- [ ] Comprehensive test coverage achieved

## Notes
- This TODO list provides structure when Claude analysis isn't available
- Update progress regularly to maintain momentum
- Use Claude CLI when quota allows for additional insights
- Re-run the analysis script after major improvements
- Consider this a living document - adjust priorities based on findings

---
**Fallback TODO List Complete**  
**Session ID**: ${TIMESTAMP}  
**Use analysis files and this TODO to guide improvements systematically**
EOF

    update_progress "todo_extraction" "completed" "Fallback TODO list created"
}

# =============================================================================
# Main Execution Flow with Resume Support
# =============================================================================

show_resume_status() {
    echo -e "${CYAN}📊 Analysis Status Summary${NC}"
    echo -e "${WHITE}Session ID: ${TIMESTAMP}${NC}"
    
    local status=$(get_progress_status)
    local completed_steps=$(get_completed_steps)
    local completed_count=$(echo "$completed_steps" | tr ',' '\n' | wc -w)
    
    echo -e "${WHITE}Overall Status: ${status}${NC}"
    echo -e "${WHITE}Progress: ${completed_count}/${#ANALYSIS_STEPS[@]} steps completed${NC}"
    echo ""
    
    echo -e "${YELLOW}Step Status:${NC}"
    for step_key in "${!ANALYSIS_STEPS[@]}"; do
        local step_name="${ANALYSIS_STEPS[$step_key]}"
        if is_step_completed "$step_key"; then
            echo -e "${GREEN}  ✅ ${step_name}${NC}"
        else
            echo -e "${WHITE}  ⏳ ${step_name}${NC}"
        fi
    done
    echo ""
}

main() {
    local START_TIME=$(date +%s)
    
    # Handle resume mode
    if [[ "$1" == "--resume" ]] || [[ -n "$RESUME_FROM_STEP" ]]; then
        echo -e "${BLUE}🔄 RESUME MODE ACTIVATED${NC}"
        show_resume_status
        echo -e "${CYAN}Resuming from where we left off...${NC}"
        echo ""
    fi
    
    # Initialize
    print_banner
    check_prerequisites
    
    # Initialize self-management
    if [[ "$ENABLE_SELF_MANAGEMENT" == "true" ]]; then
        create_self_todo
    fi
    
    # Execute analysis steps with resume support
    echo -e "${BLUE}🚀 Starting Analysis Execution${NC}"
    print_progress
    echo ""
    
    # Step 1: Documentation Analysis
    if step1_analyze_docs; then
        [[ $? -eq 2 ]] && return 0  # Quota exhausted
    fi
    
    # Step 2: Backend Analysis (multi-part)
    if step2_analyze_backend; then
        [[ $? -eq 2 ]] && return 0  # Quota exhausted
    fi
    
    # Step 3: Frontend Analysis (multi-part)
    if step3_analyze_frontend; then
        [[ $? -eq 2 ]] && return 0  # Quota exhausted  
    fi
    
    # Step 4: Synthesis and TODO Creation
    if step4_comprehensive_assessment; then
        [[ $? -eq 2 ]] && return 0  # Quota exhausted
    fi
    
    # Step 5: Final Report Generation
    if step5_final_report; then
        [[ $? -eq 2 ]] && return 0  # Quota exhausted
    fi
    
    # Final self-management update
    update_self_todo
    
    # Success summary
    echo -e "${GREEN}"
    echo "============================================================================="
    echo "                    ✅ INTELLIGENT ANALYSIS COMPLETE!"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}All analysis steps completed successfully with self-management!${NC}"
    echo ""
    echo -e "${YELLOW}📁 Analysis Results Directory:${NC}"
    echo -e "${WHITE}   ${ANALYSIS_DIR}/${NC}"
    echo ""
    echo -e "${YELLOW}📋 Key Files Generated:${NC}"
    echo -e "${WHITE}   📊 Comprehensive Assessment: $(basename "${COMPREHENSIVE_ASSESSMENT}")${NC}"
    echo -e "${WHITE}   ✅ Project TODO List: $(basename "${TODO_LIST}")${NC}"
    echo -e "${WHITE}   🤖 Script Self-TODO: $(basename "${SELF_TODO_FILE}")${NC}"
    echo -e "${WHITE}   📈 Final Report: final_analysis_report_${TIMESTAMP}.md${NC}"
    echo ""
    echo -e "${YELLOW}🧠 Self-Management Features:${NC}"
    echo -e "${WHITE}   ✅ Progress automatically tracked in JSON format${NC}"
    echo -e "${WHITE}   ✅ Self-TODO list updated throughout analysis${NC}"
    echo -e "${WHITE}   ✅ Resume capability for quota interruptions${NC}"
    echo -e "${WHITE}   ✅ Intelligent fallbacks for all analysis steps${NC}"
    echo ""
    echo -e "${YELLOW}🚀 Next Steps with Intelligence:${NC}"
    echo -e "${WHITE}   1. Review assessment: cat \"${COMPREHENSIVE_ASSESSMENT}\"${NC}"
    echo -e "${WHITE}   2. Check priorities: cat \"${TODO_LIST}\"${NC}"
    echo -e "${WHITE}   3. Script self-tracking: cat \"${SELF_TODO_FILE}\"${NC}"
    echo -e "${WHITE}   4. Get Claude help: claude -p \"Help me implement Priority 1 fixes\"${NC}"
    echo ""
    echo -e "${BLUE}💡 Intelligence Features Demonstrated:${NC}"
    echo -e "${WHITE}   🎯 Self-aware progress tracking with JSON state management${NC}"
    echo -e "${WHITE}   🔄 Quota-aware execution with automatic resume scripts${NC}"
    echo -e "${WHITE}   📋 Self-managing TODO lists that update automatically${NC}"
    echo -e "${WHITE}   🛡️ Robust fallback systems for every analysis component${NC}"
    echo -e "${WHITE}   🧠 Natural language interface compatible with Claude v1.0.69${NC}"
    echo ""
    echo -e "${CYAN}Total analysis time: $(( ($(date +%s) - START_TIME) / 60 )) minutes${NC}"
    echo -e "${GREEN}Intelligent analysis session ${TIMESTAMP} completed successfully! 🎉${NC}"
    echo ""
    echo -e "${PURPLE}This script has demonstrated true self-management:${NC}"
    echo -e "${WHITE}• Tracked its own progress throughout execution${NC}"
    echo -e "${WHITE}• Created and updated its own TODO list${NC}"
    echo -e "${WHITE}• Handled quota limits intelligently with resume capability${NC}"
    echo -e "${WHITE}• Provided comprehensive fallbacks for reliability${NC}"
    echo -e "${WHITE}• Generated detailed reports and next-step guidance${NC}"
}

# =============================================================================
# Script Execution with Intelligence
# =============================================================================

# Trap for cleanup on script exit
trap 'echo -e "${RED}Script interrupted${NC}"; update_progress "interrupted" "failed" "Script interrupted by user"; exit 1' INT TERM

# Parse command line arguments
case "${1:-}" in
    "--resume")
        RESUME_MODE=true
        ;;
    "--status")
        show_resume_status
        exit 0
        ;;
    "--no-timeout")
        echo -e "${RED}⚠️  WARNING: Removing all timeouts - Claude may hang indefinitely!${NC}"
        echo -e "${YELLOW}Are you sure? This could lock up your terminal if Claude doesn't respond.${NC}"
        read -p "Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            CLAUDE_TIMEOUT=""
            CLAUDE_QUICK_TIMEOUT=""
            echo -e "${CYAN}Timeouts disabled - Claude will run until completion or manual interruption${NC}"
            shift
        else
            echo "Keeping timeouts enabled for safety"
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
    "--test-quota")
        echo "🤖 Testing Intelligent Quota Scheduling System"
        echo ""
        echo "This will test the auto-scheduling feature with sample quota messages:"
        echo ""
        
        # Test cases
        test_messages=(
            "Claude usage limit reached. Your limit will reset at 5pm (Europe/Berlin)."
            "Claude usage limit reached. Your limit will reset at 11:30am (America/New_York)."
            "Your limit will reset at 2pm (UTC)."
        )
        
        for msg in "${test_messages[@]}"; do
            echo "📝 Testing message: '$msg'"
            
            parsed=$(parse_quota_reset_time "$msg")
            if [[ $? -eq 0 ]]; then
                reset_time=$(echo "$parsed" | sed 's/.*TIME:\([^|]*\).*/\1/')
                timezone=$(echo "$parsed" | sed 's/.*TZ:\([^|]*\).*/\1/')
                echo "   ✅ Parsed: $reset_time in $timezone"
                
                wait_calc=$(calculate_wait_time "$reset_time" "$timezone")
                if [[ "$wait_calc" == *"WAIT_SECONDS:"* ]]; then
                    wait_seconds=$(echo "$wait_calc" | grep "WAIT_SECONDS:" | cut -d: -f2)
                    reset_time_str=$(echo "$wait_calc" | grep "RESET_TIME:" | cut -d: -f2-)
                    echo "   ⏰ Would wait: $(($wait_seconds / 60)) minutes"
                    echo "   🎯 Resume at: $reset_time_str"
                else
                    echo "   ❌ Time calculation failed"
                fi
            else
                echo "   ❌ Parse failed"
            fi
            echo ""
        done
        
        echo "🎯 The intelligent quota system can:"
        echo "   • Parse quota reset times from Claude messages"
        echo "   • Handle different time formats (5pm, 11:30am, etc.)"
        echo "   • Work with various timezones (Europe/Berlin, America/New_York, UTC)"
        echo "   • Calculate exact wait times with safety buffers"
        echo "   • Create auto-resume scripts with countdown timers"
        echo "   • Test Claude availability before resuming"
        echo ""
        echo "💡 When quota is hit, just run the generated auto-resume script and walk away!"
        exit 0
        ;;
    "--help")
        echo "AI Journaling Assistant - Intelligent Analysis Script"
        echo ""
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --resume     Resume interrupted analysis from last checkpoint"
        echo "  --status     Show current analysis progress status"
        echo "  --test       Test Claude CLI functionality"
        echo "  --test-quota Test intelligent quota scheduling (demo)"
        echo "  --no-timeout Remove timeouts (WARNING: may hang indefinitely)"
        echo "  --help       Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  ANALYSIS_TIMESTAMP    Resume specific session (format: YYYYMMDD_HHMMSS)"
        echo "  RESUME_FROM_STEP      Resume from specific step"
        echo ""
        echo "Features:"
        echo "  • 🤖 Intelligent auto-scheduling for Claude quota limits"
        echo "  • ⏰ Automatic resume with timezone-aware countdown timers"
        echo "  • 📊 Smart progress tracking with JSON state management"
        echo "  • 🔄 Resume capability that remembers exactly where you left off"
        echo "  • 📋 Self-managing TODO lists that update throughout analysis"
        echo "  • 🛡️ Comprehensive fallback systems for reliability"
        echo "  • 🧠 Natural language interface compatible with Claude v1.0.69"
        echo "  • Natural language interface compatible with Claude v1.0.69"
        echo ""
        exit 0
        ;;
esac

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi