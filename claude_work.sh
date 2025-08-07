#!/bin/bash

# =============================================================================
# AI Journaling Assistant - Claude Work Implementation Script
# =============================================================================
# Purpose: Step-by-step implementation of prioritized TODO items with testing
# Author: Claude Work Protocol v1.0 
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
IMPL_DIR="${PROJECT_ROOT}/implementation_results"
TODO_FILE="${IMPL_DIR}/implementation_todo.md"
PROGRESS_FILE="${IMPL_DIR}/implementation_progress.json"
INSTRUCTIONS_FILE="${IMPL_DIR}/claude_work_instructions.md"
CURRENT_SESSION_FILE="${IMPL_DIR}/current_session.md"
LOGS_DIR="${IMPL_DIR}/logs"

# Store the original branch to merge back to
ORIGINAL_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# Session configuration
TIMESTAMP=${WORK_SESSION_ID:-$(date +%Y%m%d_%H%M%S)}
SESSION_LOG="${LOGS_DIR}/session_${TIMESTAMP}.log"
SESSION_BRANCH="phase-${TIMESTAMP}"
ENABLE_AUTO_TEST=true
ENABLE_AUTO_COMMIT=true
REQUIRE_SUCCESS_CRITERIA=true

# Resume and quota management
QUOTA_RESUME_FILE="${IMPL_DIR}/work_resume_${TIMESTAMP}.sh"
CLAUDE_CMD=""

# Timeout configuration (in seconds)
CLAUDE_TIMEOUT=300      # 5 minutes for implementation tasks
CLAUDE_QUICK_TIMEOUT=60 # 1 minute for quick operations

# Testing configuration
BACKEND_TEST_CMD="cd backend && python -m pytest -v"
FRONTEND_TEST_CMD="cd frontend && npm test -- --watchAll=false"
LINT_BACKEND_CMD="cd backend && python -m flake8 ."
LINT_FRONTEND_CMD="cd frontend && npm run lint"

# =============================================================================
# Utility Functions
# =============================================================================

print_banner() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "          AI JOURNALING ASSISTANT - CLAUDE WORK IMPLEMENTATION"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}Project Root: ${WHITE}${PROJECT_ROOT}${NC}"
    echo -e "${CYAN}Implementation Dir: ${WHITE}${IMPL_DIR}${NC}"
    echo -e "${CYAN}Session ID: ${WHITE}${TIMESTAMP}${NC}"
    echo -e "${CYAN}Session Log: ${WHITE}$(basename "$SESSION_LOG")${NC}"
    echo ""
}

log_action() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $message" | tee -a "$SESSION_LOG"
}

log_error() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${RED}[$timestamp] ERROR: $message${NC}" | tee -a "$SESSION_LOG"
}

log_success() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo -e "${GREEN}[$timestamp] SUCCESS: $message${NC}" | tee -a "$SESSION_LOG"
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
try:
    import pytz
except ImportError:
    pytz = None
import re
import sys

try:
    # Parse time
    time_str = '$reset_time'
    tz_str = '$timezone'
    
    # Handle timezone string (convert Europe/Berlin format)
    if pytz and '/' in tz_str:
        tz = pytz.timezone(tz_str)
    else:
        # Handle abbreviated timezones like CET, EST, etc. or fallback to UTC
        tz = pytz.timezone('UTC') if pytz else None
    
    # Get current time in target timezone
    if tz:
        now = datetime.datetime.now(tz)
    else:
        now = datetime.datetime.now()
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
    if tz:
        reset_today = tz.localize(datetime.datetime.combine(today, datetime.time(hour, minute)))
    else:
        reset_today = datetime.datetime.combine(today, datetime.time(hour, minute))
    
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
    local resume_task="$1"
    local wait_seconds="$2"
    local reset_time_str="$3"
    
    cat > "$QUOTA_RESUME_FILE" << EOF
#!/bin/bash
# Intelligent Auto-Resume Work Script - Generated with intelligent scheduling
# Resume from task: $resume_task
# Scheduled resume time: $reset_time_str
# Generated: $(date)

export WORK_SESSION_ID="${TIMESTAMP}"
export RESUME_FROM_TASK="$resume_task"

echo "🤖 Intelligent Auto-Resume Work Script Activated"
echo "📅 Original session: ${TIMESTAMP}"
echo "⏰ Claude quota will reset at: $reset_time_str"
echo "🕐 Current time: \$(date)"
echo ""

# Calculate remaining wait time dynamically (in case script is run later)
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

echo "🔄 Resuming intelligent work from task: $resume_task"
echo ""

# Resume the work
cd "${PROJECT_ROOT}"
./$(basename "$0") --resume

echo ""
echo "✅ Intelligent auto-resume completed successfully!"
echo "📊 Check the implementation results in: ${IMPL_DIR}/"
EOF
    chmod +x "$QUOTA_RESUME_FILE"
    echo -e "${GREEN}🤖 Intelligent auto-resume script created: $QUOTA_RESUME_FILE${NC}"
}

handle_claude_quota_exhausted() {
    local current_task="$1"
    local quota_message="$2"  # Pass the actual quota message
    
    echo -e "${RED}🚫 Claude quota exhausted!${NC}"
    echo -e "${YELLOW}🤖 Analyzing quota message for intelligent scheduling...${NC}"
    
    # Update progress to show quota exhausted
    python3 -c "
import json
from datetime import datetime

try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
    
    progress['current_session']['claude_quota_exhausted'] = True
    progress['current_session']['resume_point'] = '$current_task'
    progress['current_session']['quota_exhausted_at'] = datetime.now().isoformat()
    
    if 'blockers' not in progress:
        progress['blockers'] = []
    
    progress['blockers'].append({
        'type': 'claude_quota',
        'task': '$current_task',
        'timestamp': datetime.now().isoformat(),
        'resume_script': '$(basename "$QUOTA_RESUME_FILE")'
    })
    
    with open('$PROGRESS_FILE', 'w') as f:
        json.dump(progress, f, indent=2)
        
except Exception as e:
    print(f'Error updating progress: {e}')
"
    
    # Try to parse reset time from quota message
    local parsed_data=$(parse_quota_reset_time "$quota_message")
    local auto_schedule_success=false
    
    if [[ $? -eq 0 && -n "$parsed_data" ]]; then
        echo -e "${GREEN}✅ Successfully parsed quota reset information${NC}"
        echo -e "${BLUE}📊 Parsed data: $parsed_data${NC}"
        
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
                
                create_auto_resume_script "$current_task" "$wait_seconds" "$reset_time_str"
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
        create_simple_resume_script "$current_task"
    fi
    
    log_action "Claude quota exhausted on task $current_task - resume available"
    
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "                    ⏳ CLAUDE QUOTA EXHAUSTED - WORK PAUSED"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${WHITE}The implementation work has been paused due to Claude quota limits.${NC}"
    echo ""
    echo -e "${YELLOW}📋 What happened:${NC}"
    echo -e "${WHITE}   • Implementation progress saved to: $(basename "$PROGRESS_FILE")${NC}"
    echo -e "${WHITE}   • Current task status updated in: $(basename "$TODO_FILE")${NC}"
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${WHITE}   • 🤖 Intelligent auto-resume script created: $(basename "$QUOTA_RESUME_FILE")${NC}"
        echo -e "${GREEN}   • ✨ Script will automatically resume when quota resets!${NC}"
    else
        echo -e "${WHITE}   • Resume script created: $(basename "$QUOTA_RESUME_FILE")${NC}"
    fi
    echo -e "${WHITE}   • Session log updated with current status${NC}"
    echo ""
    echo -e "${YELLOW}🔄 To resume implementation work:${NC}"
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${GREEN}   🤖 Automatic (Recommended): ./${QUOTA_RESUME_FILE##*/}${NC}"
        echo -e "${WHITE}   📋 Manual: ./$(basename "$0") --resume${NC}"
        echo -e "${WHITE}   🕐 Later: WORK_SESSION_ID=${TIMESTAMP} ./$(basename "$0")${NC}"
    else
        echo -e "${WHITE}   Option 1 (Recommended): ./${QUOTA_RESUME_FILE##*/}${NC}"
        echo -e "${WHITE}   Option 2 (Manual): ./$(basename "$0") --resume${NC}"
        echo -e "${WHITE}   Option 3 (Later): WORK_SESSION_ID=${TIMESTAMP} ./$(basename "$0")${NC}"
    fi
    echo ""
    echo -e "${YELLOW}📊 Implementation Progress:${NC}"
    echo -e "${WHITE}   • Stopped At: $current_task${NC}"
    echo -e "${WHITE}   • Session ID: ${TIMESTAMP}${NC}"
    echo -e "${WHITE}   • Resume Available: Yes${NC}"
    echo ""
    
    if [[ "$auto_schedule_success" == "true" ]]; then
        echo -e "${GREEN}🚀 Starting intelligent auto-resume process...${NC}"
        echo -e "${CYAN}💡 The script will countdown to quota reset and automatically continue!${NC}"
        echo ""
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

create_simple_resume_script() {
    local resume_task="$1"
    cat > "$QUOTA_RESUME_FILE" << EOF
#!/bin/bash
# Resume Implementation Script - Generated automatically
# Resume from task: $resume_task
# Generated: $(date)

export WORK_SESSION_ID="${TIMESTAMP}"
export RESUME_FROM_TASK="$resume_task"

echo "🔄 Resuming implementation from task: $resume_task"
echo "📅 Original session: ${TIMESTAMP}"
echo "⏳ Waiting for Claude quota to refresh..."

# Wait a bit before resuming
sleep 5

# Resume the work
cd "${PROJECT_ROOT}"
./$(basename "$0") --resume

echo "✅ Resume script completed"
EOF
    chmod +x "$QUOTA_RESUME_FILE"
    echo -e "${YELLOW}📝 Resume script created: $QUOTA_RESUME_FILE${NC}"
}

run_claude_with_quota_monitoring() {
    local prompt="$1"
    local context_dir="$2"
    local task_id="$3"
    local timeout_duration="${4:-$CLAUDE_TIMEOUT}"
    
    echo -e "${YELLOW}Running Claude with quota monitoring (timeout: ${timeout_duration}s)...${NC}"
    
    # Change to context directory if provided
    local original_dir=$(pwd)
    if [[ -n "$context_dir" ]] && [[ -d "$context_dir" ]]; then
        cd "$context_dir"
        echo -e "${CYAN}Context: Working from $(pwd)${NC}"
    fi
    
    # Run Claude with quota monitoring
    local claude_output=$(mktemp)
    local claude_error=$(mktemp)
    
    echo -e "${CYAN}Debug: Running command: $CLAUDE_CMD -p \"[PROMPT_LENGTH: ${#prompt} chars]\" --output-format text${NC}"
    
    if timeout "$timeout_duration" $CLAUDE_CMD -p "$prompt" --output-format text > "$claude_output" 2> "$claude_error"; then
        # Success
        cat "$claude_output"
        rm -f "$claude_output" "$claude_error"
        cd "$original_dir"
        echo -e "${GREEN}✅ Claude operation successful${NC}"
        return 0
    else
        # Check if it's a quota issue
        local error_content=$(cat "$claude_error" 2>/dev/null || echo "")
        local output_content=$(cat "$claude_output" 2>/dev/null || echo "")
        local combined_content="$error_content $output_content"
        
        if [[ "$combined_content" == *"quota"* ]] || [[ "$combined_content" == *"rate limit"* ]] || [[ "$combined_content" == *"limit exceeded"* ]] || [[ "$combined_content" == *"usage limit reached"* ]] || [[ "$combined_content" == *"usage limit"* ]] || [[ "$combined_content" == *"Your limit will reset"* ]] || [[ "$combined_content" == *"Claude AI usage limit reached"* ]]; then
            echo -e "${RED}❌ Claude quota/rate limit reached: $output_content${NC}"
            rm -f "$claude_output" "$claude_error"
            cd "$original_dir"
            handle_claude_quota_exhausted "$task_id" "$combined_content"
            return 2  # Special return code for quota
        else
            echo -e "${RED}❌ Claude operation failed: stdout='$output_content' stderr='$error_content'${NC}"
            rm -f "$claude_output" "$claude_error"
            cd "$original_dir"
            return 1
        fi
    fi
}

check_claude_availability() {
    echo -e "${CYAN}🔍 Checking Claude CLI availability...${NC}"
    
    # Check if claude is installed
    if command -v claude &> /dev/null; then
        CLAUDE_CMD="claude"
        echo -e "${GREEN}✅ Found Claude CLI as 'claude'${NC}"
    else
        echo -e "${RED}❌ ERROR: Claude CLI not found${NC}"
        echo -e "${WHITE}Please install it with: curl -fsSL claude.ai/install.sh | bash${NC}"
        exit 1
    fi
    
    # Verify Claude is working with quota monitoring
    echo -e "${CYAN}Testing Claude CLI with quota monitoring...${NC}"
    if run_claude_with_quota_monitoring "Respond with 'Claude Work Ready' to confirm availability" "." "test" "$CLAUDE_QUICK_TIMEOUT" >/dev/null 2>&1; then
        local version=$($CLAUDE_CMD --version 2>/dev/null)
        echo -e "${GREEN}✅ Claude CLI is working - Version: ${version}${NC}"
        log_action "Claude CLI verified and ready for work"
        return 0
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            echo -e "${RED}❌ Claude quota exhausted during availability check${NC}"
            return 2  # Quota exhausted
        else
            echo -e "${YELLOW}⚠️  Claude CLI found but may need authentication${NC}"
            echo -e "${WHITE}Try running: $CLAUDE_CMD${NC}"
            return 1
        fi
    fi
}

# =============================================================================
# Self-Instruction and Status Check Functions
# =============================================================================

read_self_instructions() {
    echo -e "${BLUE}📋 Reading self-instructions...${NC}"
    if [[ -f "$INSTRUCTIONS_FILE" ]]; then
        echo -e "${YELLOW}Self-instruction prompt loaded. Key reminders:${NC}"
        echo -e "${WHITE}• Always check where you are and what you've done${NC}"
        echo -e "${WHITE}• Follow the 5-phase implementation workflow${NC}"
        echo -e "${WHITE}• Test after every change${NC}"
        echo -e "${WHITE}• Update progress tracking continuously${NC}"
        log_action "Self-instructions loaded from $INSTRUCTIONS_FILE"
    else
        log_error "Self-instructions file not found at $INSTRUCTIONS_FILE"
        echo -e "${RED}❌ Cannot proceed without self-instructions${NC}"
        exit 1
    fi
    echo ""
}

check_current_status() {
    echo -e "${CYAN}🔍 Checking current implementation status...${NC}"
    
    # Check what was last worked on
    if [[ -f "$CURRENT_SESSION_FILE" ]]; then
        echo -e "${WHITE}Last session information:${NC}"
        cat "$CURRENT_SESSION_FILE" | sed 's/^/  /'
        echo ""
    else
        echo -e "${WHITE}No previous session found - starting fresh${NC}"
    fi
    
    # Load progress data
    if [[ -f "$PROGRESS_FILE" ]]; then
        local completed=$(python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        data = json.load(f)
    print(data['implementation_status']['completed_tasks'])
except: 
    print('0')
")
        local total=$(python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        data = json.load(f)
    print(data['implementation_status']['total_tasks'])
except:
    print('21')
")
        echo -e "${WHITE}Progress: ${completed}/${total} tasks completed${NC}"
        log_action "Current progress: ${completed}/${total} tasks completed"
    else
        echo -e "${YELLOW}No progress file found - will initialize${NC}"
    fi
    echo ""
}

find_next_task() {
    echo -e "${YELLOW}🎯 Finding next task to work on...${NC}" >&2
    
    # Look for IN_PROGRESS tasks first
    local in_progress_task=$(grep -n "Status.*🔄.*IN_PROGRESS" "$TODO_FILE" | head -1)
    if [[ -n "$in_progress_task" ]]; then
        local task_line=$(echo "$in_progress_task" | cut -d: -f1)
        # Get the task header before the status line
        local task_header_line=$((task_line - 1))
        for ((i = task_line - 1; i >= 1; i--)); do
            local line_content=$(sed -n "${i}p" "$TODO_FILE")
            if [[ "$line_content" =~ ^###[[:space:]]+[0-9]+\.[0-9]+ ]]; then
                task_header_line=$i
                break
            fi
        done
        local task_name=$(sed -n "${task_header_line}p" "$TODO_FILE" | sed 's/^### //')
        echo -e "${BLUE}Found interrupted task: $task_name${NC}" >&2
        echo -e "${WHITE}Resuming previous work...${NC}" >&2
        echo "$task_name"
        return 0
    fi
    
    # Look for next PENDING task in priority order
    for priority in {1..5}; do
        # Find the priority section
        local priority_start=$(grep -n "## PRIORITY $priority" "$TODO_FILE" | cut -d: -f1)
        if [[ -n "$priority_start" ]]; then
            # Find the next priority section or end of file
            local priority_end=$(grep -n "## PRIORITY $((priority + 1))" "$TODO_FILE" | cut -d: -f1)
            if [[ -z "$priority_end" ]]; then
                priority_end=$(wc -l < "$TODO_FILE")
            else
                priority_end=$((priority_end - 1))
            fi
            
            # Look for PENDING tasks in this priority section
            local pending_line=$(sed -n "${priority_start},${priority_end}p" "$TODO_FILE" | grep -n "Status.*⏳.*PENDING" | head -1 | cut -d: -f1)
            if [[ -n "$pending_line" ]]; then
                # Calculate actual line number
                local actual_line=$((priority_start + pending_line - 1))
                
                # Find the task header before this status line
                local task_header_line=$actual_line
                for ((i = actual_line - 1; i >= priority_start; i--)); do
                    local line_content=$(sed -n "${i}p" "$TODO_FILE")
                    if [[ "$line_content" =~ ^###[[:space:]]+[0-9]+\.[0-9]+ ]]; then
                        task_header_line=$i
                        break
                    fi
                done
                
                local task_name=$(sed -n "${task_header_line}p" "$TODO_FILE" | sed 's/^### //')
                echo -e "${GREEN}Found next task in Priority $priority: $task_name${NC}" >&2
                echo "$task_name"
                return 0
            fi
        fi
    done
    
    echo -e "${GREEN}🎉 All tasks completed!${NC}" >&2
    return 1
}

update_task_status() {
    local task_id="$1"
    local status="$2"
    local notes="$3"
    local timestamp=$(date "+%Y-%m-%d %H:%M")
    
    echo -e "${CYAN}📝 Updating task status: $task_id -> $status${NC}"
    
    # Validate task ID format
    if [[ ! "$task_id" =~ ^[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}❌ Error: Invalid task ID format: $task_id${NC}"
        log_error "Invalid task ID format: $task_id"
        return 1
    fi
    
    # Create backup
    cp "$TODO_FILE" "$TODO_FILE.backup"
    
    # Update the status line for the specific task
    local status_emoji=""
    local status_text=""
    
    case "$status" in
        "PENDING") status_emoji="⏳"; status_text="PENDING" ;;
        "IN_PROGRESS") status_emoji="🔄"; status_text="IN_PROGRESS" ;;
        "COMPLETED") status_emoji="✅"; status_text="COMPLETED" ;;
        "FAILED") status_emoji="❌"; status_text="FAILED" ;;
        "PAUSED") status_emoji="⏸️"; status_text="PAUSED" ;;
        "TESTING") status_emoji="🔍"; status_text="TESTING" ;;
    esac
    
    # Use Python to safely update the task status
    python3 << 'EOF'
import re
import sys

# Read the file
try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        content = f.read()
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

task_id = sys.argv[2]
status_emoji = sys.argv[3]
status_text = sys.argv[4]
notes = sys.argv[5] if len(sys.argv) > 5 else ""
timestamp = sys.argv[6] if len(sys.argv) > 6 else ""

# Debug: Print what we received
print(f"Debug: task_id='{task_id}', status_emoji='{status_emoji}', status_text='{status_text}'")

# Escape special regex characters in task_id
escaped_task_id = re.escape(task_id)

# Find the task section and update status
# Look for the pattern: ### task_id ... **Status**: ...
pattern = r'(### ' + escaped_task_id + r'[^\n]*\n.*?)\*\*Status\*\*: [^\n]*'
replacement = r'\1**Status**: ' + status_emoji + ' ' + status_text

# Perform replacement
updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Check if replacement was made
if updated_content == content:
    print(f"Warning: No status update made for task {task_id}")
    print(f"Looking for pattern: ### {task_id}")
    # Let's try to find the task another way
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(f'### {task_id}'):
            print(f"Found task at line {i+1}: {line}")
            break
    else:
        print(f"Could not find task {task_id} in file")

# Update implementation notes if provided
if notes and notes != 'None' and notes != '':
    notes_pattern = r'(### ' + escaped_task_id + r'[^\n]*\n.*?)\*\*Implementation Notes\*\*: [^\n]*'
    notes_replacement = r'\1**Implementation Notes**: ' + notes
    updated_content = re.sub(notes_pattern, notes_replacement, updated_content, flags=re.DOTALL)

# Add timestamps
if status_text in ['IN_PROGRESS', 'COMPLETED', 'FAILED']:
    if status_text == 'IN_PROGRESS' and timestamp:
        start_pattern = r'(### ' + escaped_task_id + r'[^\n]*\n.*?)\*\*Started\*\*: [^\n]*'
        start_replacement = r'\1**Started**: ' + timestamp
        updated_content = re.sub(start_pattern, start_replacement, updated_content, flags=re.DOTALL)
    elif status_text == 'COMPLETED' and timestamp:
        completed_pattern = r'(### ' + escaped_task_id + r'[^\n]*\n.*?)\*\*Completed\*\*: [^\n]*'
        completed_replacement = r'\1**Completed**: ' + timestamp
        updated_content = re.sub(completed_pattern, completed_replacement, updated_content, flags=re.DOTALL)

# Write back
try:
    with open(sys.argv[1], 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print(f"Updated task {task_id} to {status_text}")
except Exception as e:
    print(f"Error writing file: {e}")
    sys.exit(1)
EOF "$TODO_FILE" "$task_id" "$status_emoji" "$status_text" "$notes" "$timestamp"

    local python_exit_code=$?
    if [[ $python_exit_code -eq 0 ]]; then
        log_action "Task $task_id status updated to $status"
        if [[ -n "$notes" ]]; then
            log_action "Task notes: $notes"
        fi
        return 0
    else
        log_error "Failed to update task status for $task_id"
        return 1
    fi
}

update_progress_summary() {
    echo -e "${CYAN}📊 Updating progress summary...${NC}"
    
    # Count current status
    local completed_count=$(grep -c "Status.*✅.*COMPLETED" "$TODO_FILE" || echo "0")
    local in_progress_count=$(grep -c "Status.*🔄.*IN_PROGRESS" "$TODO_FILE" || echo "0")
    local failed_count=$(grep -c "Status.*❌.*FAILED" "$TODO_FILE" || echo "0")
    local pending_count=$(grep -c "Status.*⏳.*PENDING" "$TODO_FILE" || echo "0")
    
    # Update JSON progress file
    python3 << EOF
import json
from datetime import datetime

try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
except:
    progress = {
        "implementation_status": {},
        "time_tracking": {},
        "current_session": {}
    }

# Update status
progress['implementation_status']['completed_tasks'] = $completed_count
progress['implementation_status']['in_progress_tasks'] = $in_progress_count
progress['implementation_status']['failed_tasks'] = $failed_count
progress['implementation_status']['pending_tasks'] = $pending_count
progress['implementation_status']['total_tasks'] = $completed_count + $in_progress_count + $failed_count + $pending_count

# Update session
progress['current_session']['last_updated'] = datetime.now().isoformat()
progress['current_session']['session_id'] = '$TIMESTAMP'

with open('$PROGRESS_FILE', 'w') as f:
    json.dump(progress, f, indent=2)
EOF

    echo -e "${WHITE}Progress updated: $completed_count completed, $in_progress_count in progress, $pending_count pending${NC}"
    log_action "Progress summary updated: $completed_count/$((completed_count + in_progress_count + failed_count + pending_count)) tasks completed"
}

# =============================================================================
# Testing and Validation Functions
# =============================================================================

run_tests() {
    local test_scope="$1"  # "full", "backend", "frontend", or "quick"
    echo -e "${YELLOW}🧪 Running tests (scope: $test_scope)...${NC}"
    
    local test_success=true
    local test_output=""
    
    case "$test_scope" in
        "backend"|"full")
            echo -e "${CYAN}Running backend tests...${NC}"
            if eval "$BACKEND_TEST_CMD" 2>&1 | tee -a "$SESSION_LOG"; then
                log_success "Backend tests passed"
            else
                log_error "Backend tests failed"
                test_success=false
            fi
            ;;
    esac
    
    case "$test_scope" in
        "frontend"|"full")
            echo -e "${CYAN}Running frontend tests...${NC}"
            if [[ -d "frontend" ]]; then
                if eval "$FRONTEND_TEST_CMD" 2>&1 | tee -a "$SESSION_LOG"; then
                    log_success "Frontend tests passed"
                else
                    log_error "Frontend tests failed"
                    test_success=false
                fi
            else
                echo -e "${YELLOW}No frontend directory found - skipping frontend tests${NC}"
            fi
            ;;
    esac
    
    case "$test_scope" in
        "lint"|"full")
            echo -e "${CYAN}Running linting...${NC}"
            if eval "$LINT_BACKEND_CMD" 2>&1 | tee -a "$SESSION_LOG"; then
                log_success "Backend linting passed"
            else
                log_error "Backend linting failed"
                test_success=false
            fi
            
            if [[ -d "frontend" ]]; then
                if eval "$LINT_FRONTEND_CMD" 2>&1 | tee -a "$SESSION_LOG"; then
                    log_success "Frontend linting passed"
                else
                    log_error "Frontend linting failed"
                    test_success=false
                fi
            fi
            ;;
    esac
    
    if [[ "$test_success" == "true" ]]; then
        echo -e "${GREEN}✅ All tests passed for scope: $test_scope${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed for scope: $test_scope${NC}"
        return 1
    fi
}

validate_success_criteria() {
    local task_id="$1"
    echo -e "${YELLOW}✅ Validating success criteria for task: $task_id${NC}"
    
    # Extract success criteria from TODO file
    local criteria=$(python3 -c "
import re
with open('$TODO_FILE', 'r') as f:
    content = f.read()
    
# Find the task section
task_pattern = r'### $task_id.*?\*\*Success Criteria\*\*: ([^\n]*)'
match = re.search(task_pattern, content, re.DOTALL)
if match:
    print(match.group(1))
else:
    print('No success criteria found')
")
    
    echo -e "${WHITE}Success criteria: $criteria${NC}"
    log_action "Validating success criteria: $criteria"
    
    # This is a placeholder - in a real implementation, you'd have specific validation
    # for each type of success criteria
    echo -e "${CYAN}Manual validation required for: $criteria${NC}"
    echo -e "${WHITE}Please verify that the success criteria have been met.${NC}"
    
    read -p "Have the success criteria been met? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_success "Success criteria validated for task $task_id"
        return 0
    else
        log_error "Success criteria not met for task $task_id"
        return 1
    fi
}

# =============================================================================
# Session Completion Functions
# =============================================================================

complete_session_with_merge() {
    local session_branch="$1"
    
    echo -e "${CYAN}🔄 Completing session and merging to original branch...${NC}"
    
    # Get current branch name (should be the session branch)
    local current_branch=$(git branch --show-current 2>/dev/null)
    
    if [[ "$current_branch" != "$session_branch" ]]; then
        echo -e "${YELLOW}⚠️  Not on expected session branch. Current: $current_branch, Expected: $session_branch${NC}"
        echo -e "${WHITE}Continuing with merge attempt...${NC}"
    fi
    
    # Switch back to original branch
    echo -e "${CYAN}Switching to original branch: $ORIGINAL_BRANCH${NC}"
    if git checkout "$ORIGINAL_BRANCH" 2>/dev/null; then
        echo -e "${GREEN}✅ Switched to $ORIGINAL_BRANCH${NC}"
        
        # Pull latest changes (if it's a remote-tracking branch)
        if git rev-parse --verify "origin/$ORIGINAL_BRANCH" >/dev/null 2>&1; then
            echo -e "${CYAN}Pulling latest changes from origin/$ORIGINAL_BRANCH...${NC}"
            git pull origin "$ORIGINAL_BRANCH" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not pull from origin${NC}"
        fi
        
        # Merge the session branch
        echo -e "${CYAN}Merging session branch: $session_branch${NC}"
        local merge_msg="Merging phase branch [$session_branch] into $ORIGINAL_BRANCH

Session completed with automated workflow
Generated: $(date)

🤖 Generated with [Claude Code](https://claude.ai/code)"
        
        if git merge "$session_branch" --no-ff -m "$merge_msg" 2>&1 | tee -a "$SESSION_LOG"; then
            echo -e "${GREEN}✅ Successfully merged $session_branch into $ORIGINAL_BRANCH${NC}"
            log_success "Session branch merged successfully"
            
            # Push if it's a remote-tracking branch
            if git rev-parse --verify "origin/$ORIGINAL_BRANCH" >/dev/null 2>&1; then
                echo -e "${CYAN}Pushing merged changes to origin/$ORIGINAL_BRANCH...${NC}"
                if git push origin "$ORIGINAL_BRANCH" 2>&1 | tee -a "$SESSION_LOG"; then
                    echo -e "${GREEN}✅ Changes pushed to origin/$ORIGINAL_BRANCH${NC}"
                    log_success "Changes pushed to remote"
                else
                    echo -e "${YELLOW}⚠️  Could not push to origin - you may need to push manually${NC}"
                    log_action "Manual push required for $ORIGINAL_BRANCH"
                fi
            fi
            
            # Clean up session branch (optional)
            echo -e "${WHITE}Session branch $session_branch can be deleted if no longer needed${NC}"
            echo -e "${WHITE}To delete: git branch -d $session_branch${NC}"
            
            return 0
        else
            echo -e "${RED}❌ Failed to merge $session_branch into $ORIGINAL_BRANCH${NC}"
            echo -e "${WHITE}You may need to resolve conflicts manually${NC}"
            log_error "Failed to merge session branch"
            return 1
        fi
    else
        echo -e "${RED}❌ Could not switch to $ORIGINAL_BRANCH${NC}"
        echo -e "${WHITE}You may need to handle the merge manually${NC}"
        log_error "Could not switch to original branch"
        return 1
    fi
}

# =============================================================================
# Git Integration Functions
# =============================================================================

commit_changes() {
    local task_id="$1"
    local task_description="$2"
    local phase="${3:-5}"  # Default to phase 5 if not specified
    
    if [[ "$ENABLE_AUTO_COMMIT" != "true" ]]; then
        echo -e "${YELLOW}Auto-commit disabled - skipping git commit${NC}"
        return 0
    fi
    
    echo -e "${CYAN}📝 Committing changes for task: $task_id (Phase $phase)${NC}"
    
    # Check if there are changes to commit
    if git diff --quiet && git diff --cached --quiet; then
        echo -e "${YELLOW}No changes to commit${NC}"
        return 0
    fi
    
    # Add all changes
    git add .
    
    # Create commit message based on phase
    local commit_msg=""
    case "$phase" in
        "3")
            commit_msg="Phase 3: Implemented $task_description

Task ID: $task_id
Session: $TIMESTAMP

- Implementation phase complete
- Code changes applied

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            ;;
        "4")
            commit_msg="Phase 4: Completed unit tests for $task_description

Task ID: $task_id
Session: $TIMESTAMP

- Testing phase complete
- All tests validated

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            ;;
        "5"|*)
            commit_msg="Phase 5: Completed task $task_description

Task ID: $task_id
Session: $TIMESTAMP

- Task implementation finalized
- Documentation updated

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            ;;
    esac
    
    # Commit changes
    if git commit -m "$commit_msg" 2>&1 | tee -a "$SESSION_LOG"; then
        log_success "Changes committed for task $task_id (Phase $phase)"
        
        # Update progress file with commit info
        python3 -c "
import json
from datetime import datetime

try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
    
    if 'git_commits' not in progress:
        progress['git_commits'] = []
    
    progress['git_commits'].append({
        'task_id': '$task_id',
        'phase': '$phase',
        'timestamp': datetime.now().isoformat(),
        'message': '$task_description'
    })
    
    with open('$PROGRESS_FILE', 'w') as f:
        json.dump(progress, f, indent=2)
except Exception as e:
    print(f'Error updating progress: {e}')
"
        return 0
    else
        log_error "Failed to commit changes for task $task_id"
        return 1
    fi
}

# =============================================================================
# Implementation Workflow Functions
# =============================================================================

implement_task() {
    local task_info="$1"
    # Better task ID extraction - look for pattern like "1.1" at the start
    local task_id=$(echo "$task_info" | sed -n 's/^\([0-9]\+\.[0-9]\+\).*/\1/p')
    # Clean up task name by removing task ID and extra characters
    local task_name=$(echo "$task_info" | sed 's/^[0-9]\+\.[0-9]\+ *//' | sed 's/ ⏳$//' | sed 's/ ✅$//' | sed 's/ ❌$//' | sed 's/ 🔄$//' | sed 's/ ⏸️$//' | sed 's/ 🔍$//')
    
    # Validate we got a proper task ID
    if [[ -z "$task_id" ]] || [[ ! "$task_id" =~ ^[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}❌ Error: Could not extract valid task ID from: $task_info${NC}"
        echo -e "${WHITE}Expected format: 'X.Y Task Name'${NC}"
        echo -e "${WHITE}Received: '$task_info'${NC}"
        echo -e "${WHITE}Extracted task_id: '$task_id'${NC}"
        log_error "Invalid task format: $task_info"
        return 1
    fi
    
    echo -e "${BLUE}"
    echo "============================================================================="
    echo "  IMPLEMENTING: $task_id - $task_name"
    echo "============================================================================="
    echo -e "${NC}"
    
    # Phase 1: Session Initialization
    echo -e "${CYAN}Phase 1: Session Initialization${NC}"
    echo "Session started: $(date)" > "$CURRENT_SESSION_FILE"
    echo "Working on: [$task_id] $task_name" >> "$CURRENT_SESSION_FILE"
    log_action "Starting implementation of task $task_id: $task_name"
    
    # Phase 2: Task Preparation
    echo -e "${CYAN}Phase 2: Task Preparation${NC}"
    update_task_status "$task_id" "IN_PROGRESS" "Implementation started"
    
    # Extract task details from TODO file
    local task_details=$(python3 -c "
import re
with open('$TODO_FILE', 'r') as f:
    content = f.read()

# Escape special regex characters in task_id
task_id = re.escape('$task_id')

# Find the task section
task_pattern = r'### ' + task_id + r'.*?(?=### |---|\Z)'
match = re.search(task_pattern, content, re.DOTALL)
if match:
    section = match.group(0)
    
    # Extract key information
    effort_match = re.search(r'\*\*Effort\*\*: ([^\n]*)', section)
    effort = effort_match.group(1) if effort_match else 'Unknown'
    
    description_match = re.search(r'\*\*Description\*\*: ([^\n]*)', section)
    description = description_match.group(1) if description_match else 'No description'
    
    files_match = re.search(r'\*\*Affected Files\*\*:(.*?)\*\*Success Criteria\*\*:', section, re.DOTALL)
    files = files_match.group(1).strip() if files_match else 'No files specified'
    
    print(f'EFFORT:{effort}')
    print(f'DESCRIPTION:{description}')
    print(f'FILES:{files}')
else:
    print('EFFORT:Unknown')
    print('DESCRIPTION:Task not found')
    print('FILES:Unknown')
")
    
    local effort=$(echo "$task_details" | grep "EFFORT:" | cut -d: -f2)
    local description=$(echo "$task_details" | grep "DESCRIPTION:" | cut -d: -f2-)
    local files=$(echo "$task_details" | grep "FILES:" | cut -d: -f2-)
    
    echo -e "${WHITE}Task Details:${NC}"
    echo -e "${WHITE}  Effort: $effort${NC}"
    echo -e "${WHITE}  Description: $description${NC}"
    echo -e "${WHITE}  Affected Files: $files${NC}"
    
    # Phase 3: Implementation Execution
    echo -e "${CYAN}Phase 3: Implementation Execution${NC}"
    echo -e "${YELLOW}⚠️  Manual implementation required${NC}"
    echo -e "${WHITE}This script provides the framework, but you need to implement:${NC}"
    echo -e "${WHITE}$description${NC}"
    echo -e "${WHITE}Files to modify: $files${NC}"
    echo ""
    
    # Pause for manual implementation
    echo -e "${BLUE}Please implement the required changes now.${NC}"
    echo -e "${WHITE}When done, press Enter to continue with testing...${NC}"
    read -r
    
    # Commit Phase 3 changes (implementation)
    if commit_changes "$task_id" "$task_name" "3"; then
        log_success "Phase 3 changes committed for task $task_id"
    else
        log_error "Failed to commit Phase 3 changes for task $task_id"
    fi
    
    # Phase 4: Testing and Validation
    echo -e "${CYAN}Phase 4: Testing and Validation${NC}"
    update_task_status "$task_id" "TESTING" "Implementation complete, running tests"
    
    if [[ "$ENABLE_AUTO_TEST" == "true" ]]; then
        # Determine test scope based on files
        local test_scope="full"
        if [[ "$files" == *"backend"* ]] && [[ "$files" != *"frontend"* ]]; then
            test_scope="backend"
        elif [[ "$files" == *"frontend"* ]] && [[ "$files" != *"backend"* ]]; then
            test_scope="frontend"
        fi
        
        if run_tests "$test_scope"; then
            log_success "Tests passed for task $task_id"
            # Commit Phase 4 changes (testing)
            if commit_changes "$task_id" "$task_name" "4"; then
                log_success "Phase 4 changes committed for task $task_id"
            else
                log_error "Failed to commit Phase 4 changes for task $task_id"
            fi
        else
            log_error "Tests failed for task $task_id"
            update_task_status "$task_id" "FAILED" "Tests failed after implementation"
            echo -e "${RED}❌ Task failed due to test failures${NC}"
            return 1
        fi
    fi
    
    # Validate success criteria if required
    if [[ "$REQUIRE_SUCCESS_CRITERIA" == "true" ]]; then
        if validate_success_criteria "$task_id"; then
            log_success "Success criteria validated for task $task_id"
        else
            log_error "Success criteria not met for task $task_id"
            update_task_status "$task_id" "FAILED" "Success criteria not met"
            echo -e "${RED}❌ Task failed - success criteria not met${NC}"
            return 1
        fi
    fi
    
    # Phase 5: Completion and Documentation
    echo -e "${CYAN}Phase 5: Completion and Documentation${NC}"
    
    # Prompt for implementation notes
    echo -e "${WHITE}Please provide implementation notes for documentation:${NC}"
    read -r implementation_notes
    
    update_task_status "$task_id" "COMPLETED" "Implementation completed. Notes: $implementation_notes"
    
    # Commit final changes (Phase 5)
    if commit_changes "$task_id" "$task_name" "5"; then
        log_success "Phase 5 changes committed for task $task_id"
    else
        log_error "Failed to commit Phase 5 changes for task $task_id"
    fi
    
    # Update progress
    update_progress_summary
    
    echo -e "${GREEN}✅ Task $task_id completed successfully!${NC}"
    log_success "Task $task_id implementation completed"
    
    # Ask if user wants to merge back to original branch
    echo -e "${WHITE}Do you want to merge this session back to $ORIGINAL_BRANCH? (y/n):${NC}"
    read -p "Merge to $ORIGINAL_BRANCH? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        complete_session_with_merge "$SESSION_BRANCH"
    else
        echo -e "${CYAN}Session branch $SESSION_BRANCH kept for manual merge later${NC}"
        echo -e "${WHITE}To merge later: git checkout $ORIGINAL_BRANCH && git merge $SESSION_BRANCH${NC}"
    fi
    
    return 0
}

# =============================================================================
# Main Execution Flow
# =============================================================================

initialize_session() {
    echo -e "${CYAN}🚀 Initializing Claude Work session...${NC}"
    
    # Create directories if they don't exist
    mkdir -p "$LOGS_DIR"
    
    # Initialize session log
    echo "=== Claude Work Session Started ===" > "$SESSION_LOG"
    echo "Time: $(date)" >> "$SESSION_LOG"
    echo "Session ID: $TIMESTAMP" >> "$SESSION_LOG"
    echo "Project: AI Journaling Assistant" >> "$SESSION_LOG"
    echo "" >> "$SESSION_LOG"
    
    # Update current session tracking (from instructions)
    echo "Session started: $(date)" > "$CURRENT_SESSION_FILE"
    echo "Session ID: $TIMESTAMP" >> "$CURRENT_SESSION_FILE"
    
    # Set up virtual environment (from instructions)
    if [ ! -d "venv" ]; then
        echo -e "${CYAN}Creating virtual environment...${NC}"
        python3 -m venv venv
        echo -e "${GREEN}Virtual environment created.${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}Virtual environment activated.${NC}"
    
    # Create a new branch for this session phase (from instructions)
    echo -e "${CYAN}Creating new branch for this session: $SESSION_BRANCH${NC}"
    echo -e "${WHITE}Original branch: $ORIGINAL_BRANCH${NC}"
    if git checkout -b "$SESSION_BRANCH" 2>/dev/null; then
        echo -e "${GREEN}New branch created: $SESSION_BRANCH${NC}"
        log_action "Created new session branch: $SESSION_BRANCH (from $ORIGINAL_BRANCH)"
    else
        echo -e "${YELLOW}Branch may already exist or git error - continuing on current branch${NC}"
        log_action "Could not create new branch - continuing on current branch"
    fi
    
    # Check prerequisites
    if [[ ! -f "$TODO_FILE" ]]; then
        log_error "Implementation TODO file not found: $TODO_FILE"
        exit 1
    fi
    
    if [[ ! -f "$PROGRESS_FILE" ]]; then
        log_error "Progress file not found: $PROGRESS_FILE"
        exit 1
    fi
    
    if [[ ! -f "$INSTRUCTIONS_FILE" ]]; then
        log_error "Instructions file not found: $INSTRUCTIONS_FILE"
        exit 1
    fi
    
    log_action "Session initialization completed"
    echo -e "${GREEN}✅ Session initialized successfully${NC}"
    echo ""
}

show_status() {
    echo -e "${CYAN}📊 Current Implementation Status${NC}"
    echo ""
    
    # Read progress from files
    if [[ -f "$PROGRESS_FILE" ]]; then
        python3 -c "
import json
try:
    with open('$PROGRESS_FILE', 'r') as f:
        progress = json.load(f)
    
    status = progress.get('implementation_status', {})
    print(f'📈 Overall Progress:')
    print(f'   Total Tasks: {status.get(\"total_tasks\", 0)}')
    print(f'   Completed: {status.get(\"completed_tasks\", 0)}')
    print(f'   In Progress: {status.get(\"in_progress_tasks\", 0)}')
    print(f'   Pending: {status.get(\"pending_tasks\", 0)}')
    print(f'   Failed: {status.get(\"failed_tasks\", 0)}')
    print()
    
    priorities = progress.get('priority_progress', {})
    for i in range(1, 6):
        p = priorities.get(f'priority_{i}', {})
        total = p.get('total', 0)
        completed = p.get('completed', 0)
        if total > 0:
            pct = round(completed * 100 / total)
            print(f'📋 Priority {i}: {completed}/{total} ({pct}%) completed')
    
except Exception as e:
    print(f'Error reading progress: {e}')
"
    else
        echo -e "${YELLOW}No progress file found${NC}"
    fi
    
    echo ""
}

main_loop() {
    while true; do
        # Check current status
        check_current_status
        
        # Find next task
        local next_task=$(find_next_task)
        if [[ $? -ne 0 ]]; then
            echo -e "${GREEN}🎉 All tasks completed!${NC}"
            log_action "All implementation tasks completed"
            
            # Generate completion report
            echo -e "${CYAN}Generating completion report...${NC}"
            local completion_report="${IMPL_DIR}/completion_report_${TIMESTAMP}.md"
            cat > "$completion_report" << EOF
# Implementation Completion Report

**Session**: $TIMESTAMP
**Completed**: $(date)
**Project**: AI Journaling Assistant

## Summary
All 21 implementation tasks have been completed successfully!

## Statistics
$(show_status)

## Session Logs
- Session Log: $(basename "$SESSION_LOG")
- Implementation TODO: $(basename "$TODO_FILE")
- Progress Tracking: $(basename "$PROGRESS_FILE")

## Next Steps
1. Perform final system testing
2. Deploy to staging environment
3. Conduct user acceptance testing
4. Prepare for production deployment

**🎉 Implementation Phase Complete!**
EOF
            echo -e "${GREEN}✅ Completion report generated: $(basename "$completion_report")${NC}"
            
            # Ask if user wants to merge back to original branch  
            echo -e "${WHITE}All tasks completed! Do you want to merge this session back to $ORIGINAL_BRANCH? (y/n):${NC}"
            read -p "Merge to $ORIGINAL_BRANCH? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                complete_session_with_merge "$SESSION_BRANCH"
            else
                echo -e "${CYAN}Session branch $SESSION_BRANCH kept for manual merge later${NC}"
                echo -e "${WHITE}To merge later: git checkout $ORIGINAL_BRANCH && git merge $SESSION_BRANCH${NC}"
            fi
            
            break
        fi
        
        echo -e "${YELLOW}Next task to implement: $next_task${NC}"
        echo ""
        
        # Ask if user wants to proceed
        echo -e "${WHITE}Do you want to implement this task now?${NC}"
        echo -e "${WHITE}Options:${NC}"
        echo -e "${WHITE}  y - Yes, implement now${NC}"
        echo -e "${WHITE}  s - Skip this task for now${NC}"
        echo -e "${WHITE}  q - Quit and save progress${NC}"
        echo -e "${WHITE}  ? - Show task details${NC}"
        
        read -p "Choice (y/s/q/?): " -n 1 -r
        echo
        
        case $REPLY in
            [Yy])
                implement_task "$next_task"
                echo ""
                ;;
            [Ss])
                echo -e "${YELLOW}Skipping task: $next_task${NC}"
                # Could implement task skipping logic here
                echo -e "${RED}Task skipping not implemented yet${NC}"
                break
                ;;
            [Qq])
                echo -e "${CYAN}Saving progress and exiting...${NC}"
                log_action "Session ended by user request"
                break
                ;;
            [\?])
                # Show task details
                echo -e "${CYAN}Task Details:${NC}"
                local task_id=$(echo "$next_task" | sed 's/^\([0-9]*\.[0-9]*\).*/\1/')
                python3 -c "
import re
task_id = re.escape('$task_id')
with open('$TODO_FILE', 'r') as f:
    content = f.read()
    
task_pattern = r'### ' + task_id + r'.*?(?=### |---|\Z)'
match = re.search(task_pattern, content, re.DOTALL)
if match:
    print(match.group(0))
else:
    print('Task details not found')
"
                echo ""
                ;;
            *)
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                ;;
        esac
    done
    
    # Final session update
    echo "Session ended: $(date)" >> "$CURRENT_SESSION_FILE"
    log_action "Claude Work session completed"
    
    echo -e "${GREEN}✅ Claude Work session completed${NC}"
    echo -e "${WHITE}Session log: $SESSION_LOG${NC}"
    echo ""
}

main() {
    local command="${1:-work}"
    
    case "$command" in
        "work"|"--resume")
            print_banner
            initialize_session
            read_self_instructions
            main_loop
            ;;
        "status")
            show_status
            ;;
        "help")
            cat << EOF
Claude Work - AI Journaling Assistant Implementation Script

Usage: $0 [COMMAND]

Commands:
  work      Start interactive implementation session (default)
  --resume  Resume previous session
  status    Show current implementation progress
  help      Show this help message

Environment Variables:
  WORK_SESSION_ID    Custom session ID (default: timestamp)
  
Features:
  • 📋 Self-instruction guided implementation
  • 🧪 Automated testing after each task
  • 📝 Comprehensive progress tracking
  • 🔄 Git integration with automated commits
  • ⚡ Interactive task selection and validation
  
The script follows a 5-phase implementation workflow:
  1. Session Initialization
  2. Task Preparation  
  3. Implementation Execution (manual)
  4. Testing and Validation (automated)
  5. Completion and Documentation (automated)

Files:
  implementation_results/implementation_todo.md    - Task tracking
  implementation_results/implementation_progress.json - Progress data
  implementation_results/claude_work_instructions.md - Self-instructions
  implementation_results/logs/session_*.log - Session logs
EOF
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Trap for cleanup on script exit
trap 'echo -e "${RED}Script interrupted${NC}"; echo "Session interrupted: $(date)" >> "$CURRENT_SESSION_FILE"; exit 1' INT TERM

# Check if script is being executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi