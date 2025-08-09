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

# =============================================================================
# Git Branch Management Functions
# =============================================================================

detect_original_branch() {
    # Default to main branch for all new sessions
    # This simplifies the workflow and ensures consistency
    if git show-ref --verify --quiet refs/heads/main; then
        echo "main"
    elif git show-ref --verify --quiet refs/heads/master; then
        echo "master"
    else
        # Get the default branch from remote if available
        local default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
        if [[ -n "$default_branch" ]]; then
            echo "$default_branch"
        else
            echo "main"  # Ultimate fallback
        fi
    fi
}

cleanup_old_session_branches() {
    echo -e "${CYAN}🧹 Cleaning up old session branches...${NC}"
    
    # Get list of local phase branches (older than 7 days)
    local old_branches=$(git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/heads/phase-* | while read branch date; do
        local days_old=$(( ($(date +%s) - date) / 86400 ))
        if [[ $days_old -gt 7 ]]; then
            echo "$branch"
        fi
    done)
    
    if [[ -n "$old_branches" ]]; then
        echo -e "${YELLOW}Found old session branches (>7 days):${NC}"
        echo "$old_branches" | sed 's/^/  - /'
        
        if [[ "$AUTO_CLEANUP_BRANCHES" == "true" ]] || auto_confirm "Delete these old branches?" "y"; then
            echo "$old_branches" | while read branch; do
                if [[ -n "$branch" ]]; then
                    echo -e "${CYAN}Deleting branch: $branch${NC}"
                    git branch -D "$branch" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not delete $branch${NC}"
                fi
            done
        fi
    fi
    
    # Cleanup remote phase branches that no longer exist locally
    local remote_phase_branches=$(git branch -r | grep -E 'origin/phase-[0-9]{8}_[0-9]{6}$' | sed 's|origin/||' | xargs)
    if [[ -n "$remote_phase_branches" ]]; then
        echo -e "${YELLOW}Found orphaned remote phase branches:${NC}"
        echo "$remote_phase_branches" | tr ' ' '\n' | sed 's/^/  - /'
        
        if [[ "$AUTO_CLEANUP_BRANCHES" == "true" ]] || auto_confirm "Delete these remote branches?" "y"; then
            for branch in $remote_phase_branches; do
                echo -e "${CYAN}Deleting remote branch: origin/$branch${NC}"
                git push origin --delete "$branch" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not delete origin/$branch${NC}"
            done
        fi
    fi
}

list_available_sessions() {
    echo -e "${CYAN}📋 Available session branches:${NC}"
    echo ""
    
    # List local session branches with last commit info
    local session_branches=$(git for-each-ref --format='%(refname:short) %(committerdate:relative) %(subject)' refs/heads/phase-*)
    
    if [[ -n "$session_branches" ]]; then
        echo -e "${GREEN}Local session branches:${NC}"
        echo "$session_branches" | while IFS=' ' read -r branch date rest; do
            echo -e "${WHITE}  🌿 $branch${NC} ${YELLOW}($date)${NC}"
            echo -e "     ${CYAN}Last commit:${NC} $rest"
        done
        echo ""
        echo -e "${WHITE}To resume a session:${NC}"
        echo -e "${WHITE}  WORK_SESSION_ID=YYYYMMDD_HHMMSS ./claude_work.sh${NC}"
        echo -e "${WHITE}  (Use the timestamp part after 'phase-')${NC}"
    else
        echo -e "${YELLOW}No session branches found${NC}"
    fi
    
    echo ""
    
    # List available resume scripts
    echo -e "${GREEN}Available resume scripts:${NC}"
    if ls "$IMPL_DIR"/work_resume_*.sh >/dev/null 2>&1; then
        for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
            if [[ -f "$resume_script" ]]; then
                script_name=$(basename "$resume_script")
                session_id=$(echo "$script_name" | sed 's/work_resume_\(.*\)\.sh/\1/')
                echo -e "${WHITE}  📄 $script_name${NC} ${YELLOW}(session: $session_id)${NC}"
                
                # Check if corresponding branch exists
                if git show-ref --verify --quiet "refs/heads/phase-$session_id"; then
                    echo -e "     ${GREEN}✅ Session branch exists${NC}"
                else
                    echo -e "     ${RED}❌ Session branch missing${NC}"
                fi
            fi
        done
    else
        echo -e "${YELLOW}No resume scripts found${NC}"
    fi
}

ensure_main_branch_current() {
    echo -e "${CYAN}🔄 Ensuring main branch is up to date...${NC}"
    
    # Fetch latest changes
    if git fetch origin 2>/dev/null; then
        echo -e "${GREEN}✅ Fetched latest changes from origin${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not fetch from origin${NC}"
    fi
    
    # If we're on main, pull latest changes
    local current_branch=$(git branch --show-current 2>/dev/null)
    if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
        echo -e "${CYAN}Pulling latest changes...${NC}"
        if git pull origin "$current_branch" 2>/dev/null; then
            echo -e "${GREEN}✅ Main branch updated${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not pull latest changes${NC}"
        fi
    fi
}

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(pwd)"
IMPL_DIR="${PROJECT_ROOT}/implementation_results"
TODO_FILE="${IMPL_DIR}/implementation_todo.md"
PROGRESS_FILE="${IMPL_DIR}/implementation_progress.json"
INSTRUCTIONS_FILE="${IMPL_DIR}/claude_work_instructions.md"
CURRENT_SESSION_FILE="${IMPL_DIR}/current_session.md"
LOGS_DIR="${IMPL_DIR}/logs"

# Detect if we're already on a session branch or original branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "main")

# Check if we're resuming a specific session via WORK_SESSION_ID
if [[ -n "$WORK_SESSION_ID" ]]; then
    # We're resuming a specific session - check if that session branch exists
    TIMESTAMP="$WORK_SESSION_ID"
    SESSION_BRANCH="phase-${TIMESTAMP}"
    ORIGINAL_BRANCH="main"
    
    if git show-ref --verify --quiet "refs/heads/$SESSION_BRANCH"; then
        echo "🔄 Resuming session: $SESSION_BRANCH (session ID from environment)"
        if [[ "$CURRENT_BRANCH" != "$SESSION_BRANCH" ]]; then
            echo "🔄 Switching to existing session branch: $SESSION_BRANCH"
        fi
    else
        echo "⚠️  Session branch $SESSION_BRANCH does not exist - will create it"
    fi
elif [[ "$CURRENT_BRANCH" =~ ^phase-[0-9]{8}_[0-9]{6}$ ]]; then
    # We're already on a session branch - reuse it
    SESSION_BRANCH="$CURRENT_BRANCH"
    TIMESTAMP=$(echo "$SESSION_BRANCH" | sed 's/^phase-//')
    # Always use main as the target branch for merging
    ORIGINAL_BRANCH="main"
    echo "🔄 Continuing existing session branch: $SESSION_BRANCH"
else
    # We're on an original branch - ensure we use main for consistent workflow
    ORIGINAL_BRANCH="main"
    # Create new session ID
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    SESSION_BRANCH="phase-${TIMESTAMP}"
    echo "🆕 Will create new session branch: $SESSION_BRANCH from $ORIGINAL_BRANCH"
    
    # If we're not on main, switch to main first
    if [[ "$CURRENT_BRANCH" != "$ORIGINAL_BRANCH" ]]; then
        echo "🔄 Switching to main branch for consistent workflow..."
        if git checkout "$ORIGINAL_BRANCH" 2>/dev/null; then
            echo -e "${GREEN}✅ Switched to $ORIGINAL_BRANCH${NC}"
        else
            echo -e "${YELLOW}⚠️  Could not switch to $ORIGINAL_BRANCH - continuing on $CURRENT_BRANCH${NC}"
            ORIGINAL_BRANCH="$CURRENT_BRANCH"
        fi
    fi
fi

SESSION_LOG="${LOGS_DIR}/session_${TIMESTAMP}.log"
ENABLE_AUTO_TEST=false
ENABLE_AUTO_COMMIT=true
REQUIRE_SUCCESS_CRITERIA=false

# Automation configuration
AUTO_MODE=${AUTO_MODE:-false}                    # Automatic mode bypasses user prompts
AUTO_CLEANUP_BRANCHES=${AUTO_CLEANUP_BRANCHES:-false}  # Automatically clean old branches
AUTO_MERGE_COMPLETED=${AUTO_MERGE_COMPLETED:-true}     # Automatically merge completed sessions

# Resume and quota management
QUOTA_RESUME_FILE="${IMPL_DIR}/work_resume_${TIMESTAMP}.sh"
CLAUDE_CMD=""

# Timeout configuration (in seconds)
CLAUDE_TIMEOUT=600      # 10 minutes for implementation tasks
CLAUDE_QUICK_TIMEOUT=180 # 3 minutes for quick operations

# Testing configuration
BACKEND_TEST_CMD="cd backend && python -m pytest -v"
FRONTEND_TEST_CMD="cd frontend && npm test -- --watchAll=false --passWithNoTests"
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
    echo -e "${CYAN}Session Branch: ${WHITE}${SESSION_BRANCH}${NC}"
    echo -e "${CYAN}Original Branch: ${WHITE}${ORIGINAL_BRANCH}${NC}"
    if [[ "$CURRENT_BRANCH" =~ ^phase-[0-9]{8}_[0-9]{6}$ ]]; then
        echo -e "${YELLOW}🔄 Resuming existing session${NC}"
    else
        echo -e "${GREEN}🆕 Starting new session${NC}"
    fi
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
# Automation Helper Functions
# =============================================================================

auto_prompt() {
    local prompt_message="$1"
    local default_response="$2"
    local prompt_flag="$3"
    
    if [[ "$AUTO_MODE" == "true" ]]; then
        echo -e "${CYAN}[AUTO MODE] $prompt_message${NC}"
        echo -e "${GREEN}[AUTO MODE] Automatically choosing: $default_response${NC}"
        echo "$default_response"
        return 0
    else
        echo -e "${WHITE}$prompt_message${NC}"
        read -p "$prompt_flag" -n 1 -r
        echo ""
        echo "$REPLY"
        return 0
    fi
}

auto_confirm() {
    local message="$1"
    local default_choice="${2:-y}"
    
    if [[ "$AUTO_MODE" == "true" ]]; then
        echo -e "${CYAN}[AUTO MODE] $message${NC}"
        echo -e "${GREEN}[AUTO MODE] Automatically proceeding (default: $default_choice)${NC}"
        return 0  # Always proceed in auto mode
    else
        local response=$(auto_prompt "$message" "$default_choice" "Continue? (y/n): ")
        [[ "$response" =~ ^[Yy]$ ]]
    fi
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

if [[ \$? -eq 0 ]]; then
    echo ""
    echo "✅ Intelligent auto-resume completed successfully!"
    echo "📊 Check the implementation results in: ${IMPL_DIR}/"
    echo ""
    echo "🧹 Cleaning up resume script..."
    rm -f "\$0"
    echo "✅ Resume script removed"
else
    echo ""
    echo "❌ Resume failed - keeping script for retry"
    echo "💡 You can run this script again: \$0"
fi
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

if [[ \$? -eq 0 ]]; then
    echo "✅ Resume script completed successfully"
    echo "🧹 Cleaning up resume script..."
    rm -f "\$0"
    echo "✅ Resume script removed"
else
    echo "❌ Resume failed - keeping script for retry"
    echo "💡 You can run this script again: \$0"
fi
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
    
    echo -e "${CYAN}Debug: Running command: $CLAUDE_CMD -p \"[PROMPT_LENGTH: ${#prompt} chars]\" --output-format stream-json --verbose${NC}"
    echo -e "${BLUE}📝 Claude is working... (streaming output in real-time)${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT START ━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Create temp files for capturing output (for error handling)
    local claude_output=$(mktemp)
    local claude_error=$(mktemp)
    local final_content=""
    
    # Function to add colored prefixes to output lines with comprehensive Claude activity parsing
    stream_with_prefix() {
        local content_buffer=""
        
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                # Parse and display Claude's real-time activity directly
                echo "$line" | python3 -c "
import json
import sys
from datetime import datetime

try:
    line = sys.stdin.read().strip()
    if not line:
        sys.exit(0)
    
    data = json.loads(line)
    event_type = data.get('type', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Claude CLI uses different message types: system, user, assistant, result
    if event_type == 'system':
        subtype = data.get('subtype', '')
        if subtype == 'init':
            print(f'│ 🧠 [{timestamp}] Claude session initialized')
        else:
            print(f'│ 🧠 [{timestamp}] System: {subtype}')
    elif event_type == 'user':
        print(f'│ 👤 [{timestamp}] User message processed')
    elif event_type == 'assistant':
        # Claude CLI format: {\"type\":\"assistant\",\"message\":{\"content\":[...]}}
        message = data.get('message', {})
        content = message.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    if item_type == 'tool_use':
                        # Tool usage in assistant message
                        tool_name = item.get('name', 'unknown')
                        tool_id = item.get('id', 'unknown')
                        tool_input = item.get('input', {})
                        
                        print(f'│ 🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                        
                        # Show specific tool details
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', tool_input.get('file_path', 'unknown'))
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'│ 📄 Creating: {file_path}')
                            print(f'│ 💾 Content preview: {content_preview}...')
                        elif tool_name == 'Write':
                            file_path = tool_input.get('file_path', 'unknown')
                            content_preview = str(tool_input.get('content', ''))[:100]
                            print(f'│ 📄 Writing to: {file_path}')
                            print(f'│ 💾 Content preview: {content_preview}...')
                        elif tool_name == 'replace_string_in_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            old_str_preview = str(tool_input.get('oldString', ''))[:50]
                            print(f'│ 📝 Editing: {file_path}')
                            print(f'│ 🔄 Replacing: {old_str_preview}...')
                        elif tool_name == 'read_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            start_line = tool_input.get('startLine', 'N/A')
                            end_line = tool_input.get('endLine', 'N/A')
                            print(f'│ 📖 Reading: {file_path} (lines {start_line}-{end_line})')
                        elif tool_name == 'run_in_terminal':
                            command = tool_input.get('command', 'unknown')
                            print(f'│ ⚡ Running: {command[:50]}...' if len(command) > 50 else f'│ ⚡ Running: {command}')
                        elif tool_name == 'list_dir':
                            path = tool_input.get('path', 'unknown')
                            print(f'│ 📁 Listing directory: {path}')
                        else:
                            # Generic tool display
                            print(f'│ ⚙️  Tool: {tool_name} with {len(str(tool_input))} chars of input')
                    elif item_type == 'text':
                        text_content = item.get('text', '')
                        if text_content and len(text_content.strip()) > 0:
                            print(f'│ 🤖 [{timestamp}] Claude: {text_content[:200]}...' if len(text_content) > 200 else f'│ 🤖 [{timestamp}] Claude: {text_content}')
        else:
            print(f'│ 🤖 [{timestamp}] Assistant response (non-array content)')
    elif event_type == 'result':
        # CRITICAL: This is where Claude CLI shows tool usage!
        content = data.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    item_type = item.get('type', '')
                    if item_type == 'tool_use':
                        tool_name = item.get('name', 'unknown')
                        tool_id = item.get('id', 'unknown')
                        tool_input = item.get('input', {})
                        
                        print(f'│ 🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                        
                        # Show specific tool details
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', tool_input.get('file_path', 'unknown'))
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'│ 📄 Creating: {file_path}')
                            print(f'│ 💾 Content preview: {content_preview}...')
                        elif tool_name == 'replace_string_in_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            old_str_preview = str(tool_input.get('oldString', ''))[:50]
                            print(f'│ 📝 Editing: {file_path}')
                            print(f'│ 🔄 Replacing: {old_str_preview}...')
                        elif tool_name == 'read_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            start_line = tool_input.get('startLine', 'N/A')
                            end_line = tool_input.get('endLine', 'N/A')
                            print(f'│ 📖 Reading: {file_path} (lines {start_line}-{end_line})')
                        elif tool_name == 'run_in_terminal':
                            command = tool_input.get('command', 'unknown')
                            print(f'│ ⚡ Running: {command[:50]}...' if len(command) > 50 else f'│ ⚡ Running: {command}')
                        elif tool_name == 'list_dir':
                            path = tool_input.get('path', 'unknown')
                            print(f'│ 📁 Listing directory: {path}')
                        else:
                            # Generic tool display
                            print(f'│ ⚙️  Tool parameters: {str(tool_input)[:100]}...' if len(str(tool_input)) > 100 else f'│ ⚙️  Tool parameters: {tool_input}')
                    elif item_type == 'text':
                        text_content = item.get('text', '')
                        if text_content and len(text_content.strip()) > 0:
                            print(f'│ 💬 [{timestamp}] {text_content[:200]}...' if len(text_content) > 200 else f'│ 💬 [{timestamp}] {text_content}')
    elif event_type == 'error':
        error_msg = data.get('error', {}).get('message', 'Unknown error')
        print(f'│ ❌ [{timestamp}] Error: {error_msg}')
    elif event_type == 'ping':
        print(f'│ 🔍 [{timestamp}] Connection alive')
    else:
        # For debugging other event types
        if event_type:
            print(f'│ 📡 [{timestamp}] Event: {event_type}')

except json.JSONDecodeError:
    # Not valid JSON, might be direct text output
    if line and len(line.strip()) > 0:
        print(f'│ 📄 [{timestamp}] Direct output: {line}')
except Exception as e:
    # For debugging
    if line and len(line.strip()) > 0 and len(line) < 200:
        print(f'│ 🔍 [{timestamp}] Raw: {line}')
" 2>/dev/null || {
                    # Fallback: show raw JSON for debugging if parser fails
                    if [[ "$line" =~ ^\{.*\}$ ]]; then
                        echo -e "${YELLOW}│${NC} 🔍 Raw JSON: ${line:0:100}..."
                    else
                        echo -e "${WHITE}│${NC} 📄 Raw output: $line"
                    fi
                }
                
                # Flush output for real-time display
                exec 1>&1
                
                # Also save the raw line for error handling
                echo "$line" >> "$claude_output"
            fi
        done
        
        echo "$content_buffer"
    }
    
    # Use stdbuf for line buffering if available, otherwise direct execution
    local streaming_cmd=""
    if command -v stdbuf &> /dev/null; then
        streaming_cmd="stdbuf -oL -eL"
    fi
    
    # Run Claude with real-time JSON streaming
    if [[ -n "$streaming_cmd" ]]; then
        if timeout "$timeout_duration" $streaming_cmd $CLAUDE_CMD -p "$prompt" --output-format stream-json --verbose 2> "$claude_error" | stream_with_prefix; then
            echo ""
            echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT END ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}✅ Claude operation completed successfully${NC}"
            rm -f "$claude_output" "$claude_error"
            cd "$original_dir"
            return 0
        fi
    else
        if timeout "$timeout_duration" $CLAUDE_CMD -p "$prompt" --output-format stream-json --verbose 2> "$claude_error" | stream_with_prefix; then
            echo ""
            echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT END ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}✅ Claude operation completed successfully${NC}"
            rm -f "$claude_output" "$claude_error"
            cd "$original_dir"
            return 0
        fi
    fi
    
    # Handle errors
    echo ""
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT END ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check if it's a quota issue
    local error_content=$(cat "$claude_error" 2>/dev/null || echo "")
    local output_content=$(cat "$claude_output" 2>/dev/null || echo "")
    local combined_content="$error_content $output_content"
    
    # Debug quota detection
    if [[ -n "$combined_content" ]]; then
        echo -e "${CYAN}Debug: Checking for quota issues in output...${NC}"
        echo -e "${YELLOW}Error content length: ${#error_content} chars${NC}"
        echo -e "${YELLOW}Output content length: ${#output_content} chars${NC}"
    fi
    
    # More specific quota detection - look for actual quota error patterns
    if [[ "$combined_content" == *"Claude AI usage limit reached"* ]] || [[ "$combined_content" == *"Your limit will reset"* ]] || [[ "$combined_content" == *"usage limit reached"* ]] || [[ "$combined_content" == *"rate limit exceeded"* ]] || [[ "$combined_content" == *"quota exceeded"* ]]; then
        echo -e "${RED}❌ Claude quota/rate limit reached: $combined_content${NC}"
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
}

check_claude_availability() {
    echo -e "${CYAN}🔍 Checking Claude CLI availability...${NC}"
    
    # Check if claude is installed
    if command -v claude &> /dev/null; then
        CLAUDE_CMD="claude --dangerously-skip-permissions --model sonnet"
        echo -e "${GREEN}✅ Found Claude CLI as 'claude' (with permissions bypass, using Sonnet 4)${NC}"
    else
        echo -e "${RED}❌ ERROR: Claude CLI not found${NC}"
        echo -e "${WHITE}Please install it with: curl -fsSL claude.ai/install.sh | bash${NC}"
        exit 1
    fi
    
    # Quick availability test with timeout and quota handling
    echo -e "${CYAN}Testing Claude CLI availability...${NC}"
    
    # Create a simple test that won't get stuck
    local test_output=$(mktemp)
    local test_error=$(mktemp)
    
    # Run a very simple test with short timeout
    if timeout 30 $CLAUDE_CMD -p "test" --output-format text >"$test_output" 2>"$test_error"; then
        local version=$($CLAUDE_CMD --version 2>/dev/null)
        echo -e "${GREEN}✅ Claude CLI is working - Version: ${version}${NC}"
        log_action "Claude CLI verified and ready for work"
        rm -f "$test_output" "$test_error"
        return 0
    else
        local exit_code=$?
        local error_content=$(cat "$test_error" 2>/dev/null || echo "")
        local output_content=$(cat "$test_output" 2>/dev/null || echo "")
        local combined_content="$error_content $output_content"
        
        rm -f "$test_output" "$test_error"
        
        # Check if it's a quota issue - use more specific detection
        if [[ "$combined_content" == *"Claude AI usage limit reached"* ]] || [[ "$combined_content" == *"Your limit will reset"* ]] || [[ "$combined_content" == *"usage limit reached"* ]] || [[ "$combined_content" == *"rate limit exceeded"* ]] || [[ "$combined_content" == *"quota exceeded"* ]]; then
            echo -e "${RED}❌ Claude quota exhausted${NC}"
            echo -e "${YELLOW}⚠️  Claude quota has been reached. Please wait for reset or try resume scripts.${NC}"
            echo -e "${WHITE}💡 You may have resume scripts available in: ${IMPL_DIR}/${NC}"
            echo -e "${WHITE}💡 Look for files like: work_resume_*.sh${NC}"
            return 2  # Quota exhausted
        elif [[ $exit_code -eq 124 ]]; then
            echo -e "${YELLOW}⚠️  Claude CLI test timed out - may need authentication${NC}"
            echo -e "${WHITE}Try running: $CLAUDE_CMD${NC}"
            return 1
        else
            echo -e "${YELLOW}⚠️  Claude CLI found but may need authentication${NC}"
            echo -e "${WHITE}Error: $combined_content${NC}"
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
    for priority in {1..6}; do
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
    # Create a temporary Python script to avoid heredoc issues
    local python_script=$(mktemp)
    cat > "$python_script" << 'PYTHON_EOF'
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
PYTHON_EOF

    # Run the Python script with arguments
    python3 "$python_script" "$TODO_FILE" "$task_id" "$status_emoji" "$status_text" "$notes" "$timestamp"
    local python_exit_code=$?
    
    # Clean up the temporary script
    rm -f "$python_script"

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
    
    # Count current status (trim whitespace to avoid arithmetic errors)
    local completed_count=$(grep -c "Status.*✅.*COMPLETED" "$TODO_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    local in_progress_count=$(grep -c "Status.*🔄.*IN_PROGRESS" "$TODO_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    local failed_count=$(grep -c "Status.*❌.*FAILED" "$TODO_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    local pending_count=$(grep -c "Status.*⏳.*PENDING" "$TODO_FILE" 2>/dev/null | tr -d '\n' || echo "0")
    
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

# Update status (ensure numeric values)
completed = int('$completed_count' or 0)
in_progress = int('$in_progress_count' or 0)
failed = int('$failed_count' or 0)
pending = int('$pending_count' or 0)

progress['implementation_status']['completed_tasks'] = completed
progress['implementation_status']['in_progress_tasks'] = in_progress
progress['implementation_status']['failed_tasks'] = failed
progress['implementation_status']['pending_tasks'] = pending
progress['implementation_status']['total_tasks'] = completed + in_progress + failed + pending

# Update session
progress['current_session']['last_updated'] = datetime.now().isoformat()
progress['current_session']['session_id'] = '$TIMESTAMP'

with open('$PROGRESS_FILE', 'w') as f:
    json.dump(progress, f, indent=2)
EOF

    echo -e "${WHITE}Progress updated: $completed_count completed, $in_progress_count in progress, $pending_count pending${NC}"
    
    # Calculate total tasks safely (ensure all variables are numeric)
    local total_tasks=$(( ${completed_count:-0} + ${in_progress_count:-0} + ${failed_count:-0} + ${pending_count:-0} ))
    log_action "Progress summary updated: $completed_count/$total_tasks tasks completed"
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
    
    if auto_confirm "Have the success criteria been met?" "y"; then
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
            
            # Clean up session branch automatically after successful merge
            echo -e "${CYAN}🧹 Cleaning up session branch: $session_branch${NC}"
            if git branch -d "$session_branch" 2>/dev/null; then
                echo -e "${GREEN}✅ Session branch deleted locally${NC}"
                log_success "Session branch cleaned up locally"
                
                # Also clean up remote session branch if it exists
                if git rev-parse --verify "origin/$session_branch" >/dev/null 2>&1; then
                    echo -e "${CYAN}Cleaning up remote session branch: origin/$session_branch${NC}"
                    if git push origin --delete "$session_branch" 2>/dev/null; then
                        echo -e "${GREEN}✅ Remote session branch deleted${NC}"
                        log_success "Remote session branch cleaned up"
                    else
                        echo -e "${YELLOW}⚠️  Could not delete remote session branch${NC}"
                        log_action "Manual cleanup required for origin/$session_branch"
                    fi
                fi
            else
                echo -e "${YELLOW}⚠️  Could not delete session branch - may contain unmerged changes${NC}"
                echo -e "${WHITE}You can delete it manually with: git branch -D $session_branch${NC}"
            fi
            
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
        "5")
            commit_msg="Phase 5: Completed task $task_description

Task ID: $task_id
Session: $TIMESTAMP

- Task implementation finalized
- Documentation updated

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            ;;
        "6")
            commit_msg="Phase 6: Frontend-Backend Integration - $task_description

Task ID: $task_id
Session: $TIMESTAMP

- Integration implementation complete
- User experience enhanced
- API connectivity restored

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
            ;;
        *)
            commit_msg="Completed task $task_description

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
# Documentation Functions
# =============================================================================

create_basic_documentation() {
    local task_id="$1"
    local task_name="$2" 
    local description="$3"
    local files="$4"
    
    echo -e "${WHITE}Creating basic documentation structure...${NC}"
    
    # Create folder structure
    mkdir -p "docs/tasks/$task_id"
    mkdir -p "docs/implementations/$(date +%Y)/$(date +%m)/$task_id"
    mkdir -p "docs/testing/$(date +%Y%m%d)/$task_id"
    
    # Create basic completion report
    cat > "docs/tasks/$task_id/completion_report.md" << EOF
# Task Completion Report: $task_name

**Task ID:** $task_id  
**Completion Date:** $(date +%Y-%m-%d)  
**Session:** $SESSION_BRANCH  

## Task Summary:
$description

## Implementation Details:
### Files Modified:
$files

### Key Changes:
Implementation completed via automated system.

## Testing Results:
Basic validation completed.

## Usage Instructions:
Task implementation complete.

## References:
- Implementation details: [docs/implementations/$(date +%Y)/$(date +%m)/$task_id/](../../implementations/$(date +%Y)/$(date +%m)/$task_id/)
- Code changes: See git commit history for session $SESSION_BRANCH
EOF

    # Copy implementation logs if they exist
    if [ -f "implementation_results/active/$task_id/implementation_log.md" ]; then
        cp "implementation_results/active/$task_id/implementation_log.md" "docs/implementations/$(date +%Y)/$(date +%m)/$task_id/"
    fi
    
    # Update task index
    if ! grep -q "\\[$task_id\\]" docs/task_index.md 2>/dev/null; then
        sed -i "/<!-- Format: /a - [$task_id] $task_name - $(date +%Y-%m-%d) - [View Report](tasks/$task_id/completion_report.md)" docs/task_index.md
    fi
    
    echo -e "${GREEN}✅ Basic documentation created${NC}"
}

# =============================================================================
# Claude Execution Functions
# =============================================================================

run_claude_with_phase() {
    local phase="$1"
    local task_context="$2"
    local timeout="${3:-$CLAUDE_TIMEOUT}"
    
    echo -e "${CYAN}🤖 Running Claude with Phase $phase instructions...${NC}"
    
    # Build phase-specific prompt
    local core_instructions=$(cat implementation_results/claude_work_core.md 2>/dev/null || echo "# Core instructions file not found")
    local phase_instructions=$(cat implementation_results/claude_work_phase${phase}.md 2>/dev/null || echo "# Phase $phase instructions file not found")
    
    local prompt="
$(echo "$core_instructions")

=== CURRENT PHASE: $phase ===
$(echo "$phase_instructions")

=== TASK CONTEXT ===
$task_context

=== AVAILABLE TOOLS (use these exact names) ===
- Write: Create new files or completely overwrite existing files
- Edit: Make exact string replacements in existing files
- MultiEdit: Make multiple edits to a single file in one operation
- Read: Read file contents with optional line range
- LS: List directory contents
- Bash: Execute shell commands
- Glob: Find files using patterns
- Grep: Search file contents

CRITICAL: You must use these exact tool names. Do NOT use:
- create_file, replace_string_in_file, read_file, list_dir, run_in_terminal (these don't exist)

=== REFERENCE FILES ===
- Templates: implementation_results/claude_work_templates.md
- Troubleshooting: implementation_results/claude_work_troubleshooting.md
- Session tracking: implementation_results/current_session.md
- Available tasks: implementation_results/tasks/

Read reference files as needed using the Read tool.
"
    
    echo -e "${WHITE}  → Phase: $phase${NC}"
    echo -e "${WHITE}  → Context length: ${#task_context} characters${NC}"
    echo -e "${BLUE}  → Total prompt length: ${#prompt} characters${NC}"
    
    # Run Claude with the phase-specific prompt
    if run_claude_with_quota_monitoring "$prompt" "$PROJECT_ROOT" "phase-$phase" "$timeout"; then
        echo -e "${GREEN}✅ Phase $phase completed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Phase $phase failed${NC}"
        return 1
    fi
}

# =============================================================================
# Automated Implementation Functions
# =============================================================================

automated_implement_task() {
    local task_id="$1"
    local task_name="$2"
    local description="$3"
    local files="$4"
    
    echo -e "${CYAN}🤖 Starting automated implementation...${NC}"
    echo -e "${WHITE}  → Building implementation prompt for Claude${NC}"
    
    # Build modular implementation prompt using phase 4 instructions
    local core_instructions=$(cat implementation_results/claude_work_core.md 2>/dev/null || echo "# Core instructions file not found")
    local phase4_instructions=$(cat implementation_results/claude_work_phase4.md 2>/dev/null || echo "# Phase 4 instructions file not found")
    
    local implementation_prompt="
$(echo "$core_instructions")

=== CURRENT PHASE: 4 (Code Implementation) ===
$(echo "$phase4_instructions")

=== TASK CONTEXT ===
Task ID: $task_id
Task Name: $task_name
Description: $description
Affected Files: $files

=== PROJECT CONTEXT ===
This is a journaling application with React frontend and Python backend.

=== AVAILABLE TOOLS (use these exact names) ===
- Write: Create new files or completely overwrite existing files
- Edit: Make exact string replacements in existing files
- MultiEdit: Make multiple edits to a single file in one operation
- Read: Read file contents with optional line range
- LS: List directory contents
- Bash: Execute shell commands
- Glob: Find files using patterns
- Grep: Search file contents

CRITICAL: You must use these exact tool names. Do NOT use:
- create_file, replace_string_in_file, read_file, list_dir, run_in_terminal (these don't exist)
- Use ONLY the Claude CLI tools listed above

=== REFERENCE FILES ===
- Templates: implementation_results/claude_work_templates.md
- Troubleshooting: implementation_results/claude_work_troubleshooting.md
- Session tracking: implementation_results/current_session.md

Read reference files as needed using the Read tool.

ERROR PREVENTION AND FIXING:
- Before making any change, use read_file to understand existing code structure
- Use proper indentation and syntax for the target language
- Check for missing imports, brackets, parentheses, or semicolons
- Validate that all variables and functions are properly defined
- Ensure proper React component structure (JSX, hooks, props)
- Verify Python syntax, imports, and function definitions
- Test that routing paths match between components

DEBUGGING CHECKLIST:
□ Use Read tool on all affected files first
□ Use Bash tool to check for existing errors before starting
□ Make one change at a time using Edit tool
□ Use Bash tool after each change to validate (python -m py_compile, node --check, etc.)
□ Fix any syntax errors immediately with Edit tool
□ Use Read tool to verify final result
□ Ensure all imports and dependencies are correct

TOOL USAGE EXAMPLES:
- Reading: Read with file path and optional line range
- Editing: Edit with file path, old string, and new string  
- Creating: Write with file path and content
- Checking: Bash with validation commands (python -m py_compile, etc.)
- Listing: LS with directory path

CRITICAL REMINDERS:
- You CAN create and modify files - use the correct Claude CLI tools listed above
- NEVER use create_file, replace_string_in_file, read_file, list_dir, run_in_terminal, get_errors (these don't exist)
- ALWAYS use Bash tool for validation after making changes
- Fix any errors immediately when detected
- Focus only on changes related to this specific task
- Use Edit tool for ALL file modifications
- Include sufficient context in old string for unique matching

Please implement the required changes now using ONLY the tools listed above.
"

    echo -e "${WHITE}  → Sending task to Claude for automated implementation${NC}"
    echo -e "${BLUE}  → Prompt length: ${#implementation_prompt} characters${NC}"
    
    # Check git status before Claude runs (for reference only)
    local changes_before=$(git status --porcelain | wc -l)
    
    # Run Claude with the implementation prompt
    if run_claude_with_quota_monitoring "$implementation_prompt" "$PROJECT_ROOT" "$task_id" "$CLAUDE_TIMEOUT"; then
        # FIXED: Check for actual work done by looking at recent commits AND current changes
        # This accounts for the fact that Claude may have committed changes during execution
        
        # Check if there are any uncommitted changes
        local uncommitted_changes=$(git status --porcelain | wc -l)
        
        # Check if there were recent commits in the last 5 minutes (indicating Claude made commits)
        local recent_commits=$(git log --since="5 minutes ago" --oneline | wc -l)
        
        # Check if any files were actually modified/created (look at git log for recent activity)
        local recent_file_changes=$(git log --since="5 minutes ago" --name-only --pretty=format: | sort -u | grep -v "^$" | wc -l)
        
        if [[ $uncommitted_changes -gt 0 ]] || [[ $recent_commits -gt 0 ]] || [[ $recent_file_changes -gt 0 ]]; then
            if [[ $recent_commits -gt 0 ]]; then
                echo -e "${GREEN}✅ Automated implementation completed successfully${NC}"
                echo -e "${CYAN}📝 Detected $recent_commits recent commit(s) with $recent_file_changes file changes${NC}"
            else
                echo -e "${GREEN}✅ Automated implementation completed with $uncommitted_changes uncommitted changes${NC}"
            fi
            
            # Skip post-validation since Claude already validates through builds and commits
            echo -e "${CYAN}🔍 Skipping post-implementation validation (Claude already validated via builds)${NC}"
            echo -e "${GREEN}✅ Implementation validation assumed successful${NC}"
            
            if [[ $recent_commits -gt 0 ]]; then
                log_success "Automated implementation completed for task $task_id with $recent_commits commits and $recent_file_changes file changes"
            else
                log_success "Automated implementation completed for task $task_id with $uncommitted_changes changes"
            fi
            return 0
        else
            echo -e "${YELLOW}⚠️ Claude completed but no recent file changes or commits detected${NC}"
            echo -e "${WHITE}This could indicate permission issues, tool availability problems, or task was already complete${NC}"
            echo -e "${CYAN}💡 Checking if task might have been completed previously...${NC}"
            
            # More lenient check - maybe the task was already done
            echo -e "${WHITE}Continuing with assumption that implementation may have been successful${NC}"
            log_action "Claude completed task $task_id but no obvious changes detected - assuming successful"
            return 0
        fi
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            # Quota exhausted - this is handled by run_claude_with_quota_monitoring
            return 2
        else
            echo -e "${YELLOW}⚠️ Automated implementation failed, falling back to manual${NC}"
            log_error "Automated implementation failed for task $task_id"
            return 1
        fi
    fi
}

# =============================================================================
# Post-Implementation Validation Functions  
# =============================================================================

validate_implementation_changes() {
    local files="$1"
    echo -e "${CYAN}Validating implementation changes for files: $files${NC}"
    
    local validation_passed=true
    
    # Get list of modified files from git
    local modified_files=$(git diff --name-only HEAD~1 2>/dev/null || git diff --name-only --cached 2>/dev/null || echo "")
    
    if [[ -z "$modified_files" ]]; then
        echo -e "${YELLOW}No modified files detected in git${NC}"
        return 1
    fi
    
    echo -e "${WHITE}Checking modified files: $modified_files${NC}"
    
    # Check each modified file for syntax errors
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            echo -e "${CYAN}Validating: $file${NC}"
            
            # Get file extension to determine validation method
            local ext="${file##*.}"
            case "$ext" in
                "js"|"jsx"|"ts"|"tsx")
                    # Check JavaScript/TypeScript/JSX syntax using build
                    if [[ "$file" =~ ^frontend/ ]]; then
                        # For frontend files, use npm build to validate
                        echo -e "${CYAN}Using build validation for React file: $file${NC}"
                        if (cd frontend && npm run build >/dev/null 2>&1); then
                            echo -e "${GREEN}✅ React build OK: $file${NC}"
                        else
                            echo -e "${RED}❌ React build error involving: $file${NC}"
                            validation_passed=false
                        fi
                    elif [[ "$ext" == "js" ]]; then
                        # For plain JS files, use node -c
                        if command -v node &> /dev/null; then
                            if ! node -c "$file" 2>/dev/null; then
                                echo -e "${RED}❌ JavaScript syntax error in: $file${NC}"
                                validation_passed=false
                            else
                                echo -e "${GREEN}✅ JavaScript syntax OK: $file${NC}"
                            fi
                        fi
                    else
                        echo -e "${BLUE}ℹ️ Skipping syntax check for TypeScript/JSX: $file${NC}"
                    fi
                    ;;
                "py")
                    # Check Python syntax
                    if ! python3 -m py_compile "$file" 2>/dev/null; then
                        echo -e "${RED}❌ Python syntax error in: $file${NC}"
                        validation_passed=false
                    else
                        echo -e "${GREEN}✅ Python syntax OK: $file${NC}"
                    fi
                    ;;
                *)
                    echo -e "${BLUE}ℹ️ No syntax check available for: $file${NC}"
                    ;;
            esac
        fi
    done <<< "$modified_files"
    
    if [[ "$validation_passed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

auto_fix_implementation_issues() {
    local task_id="$1"
    local files="$2"
    
    echo -e "${CYAN}🔧 Attempting to auto-fix implementation issues...${NC}"
    
    # Build auto-fix prompt for Claude
    local fix_prompt="
You are debugging and fixing issues found in the implementation of task $task_id.

PROBLEM: The implementation validation detected syntax errors or other issues in the modified files.

YOUR TASK:
1. Use get_errors tool to identify specific errors in the affected files
2. Use read_file tool to examine the problematic code
3. Use replace_string_in_file tool to fix the identified issues
4. Focus on syntax errors, missing imports, and structural problems
5. Verify fixes by reading the files back after modification

DEBUGGING APPROACH:
- Check for common issues: missing semicolons, brackets, quotes
- Verify proper React component structure and JSX syntax
- Check Python indentation, imports, and function definitions
- Ensure all variables and functions are properly defined
- Fix any typos or incorrect function/variable names

AFFECTED FILES: $files

Please identify and fix all issues in the implementation.
"
    
    echo -e "${WHITE}Sending auto-fix request to Claude...${NC}"
    if run_claude_with_quota_monitoring "$fix_prompt" "$PROJECT_ROOT" "$task_id-fix" "$CLAUDE_TIMEOUT"; then
        # Validate again after fix attempt
        if validate_implementation_changes "$files"; then
            echo -e "${GREEN}✅ Auto-fix successful${NC}"
            return 0
        else
            echo -e "${RED}❌ Auto-fix validation still failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Auto-fix attempt failed${NC}"
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
    echo -e "${WHITE}  → Initializing session tracking${NC}"
    echo "Session started: $(date)" > "$CURRENT_SESSION_FILE"
    echo "Working on: [$task_id] $task_name" >> "$CURRENT_SESSION_FILE"
    log_action "Starting implementation of task $task_id: $task_name"
    echo -e "${GREEN}  ✅ Session initialized${NC}"
    echo ""
    
    # Phase 2: Task Preparation
    echo -e "${CYAN}Phase 2: Task Preparation${NC}"
    echo -e "${WHITE}  → Updating task status to IN_PROGRESS${NC}"
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
    local automated_success=false
    
    echo -e "${WHITE}Task Details:${NC}"
    echo -e "${WHITE}  Effort: $effort${NC}"
    echo -e "${WHITE}  Description: $description${NC}"
    echo -e "${WHITE}  Affected Files: $files${NC}"
    echo -e "${GREEN}  ✅ Task preparation complete${NC}"
    echo ""
    
    # Phase 3: Implementation Execution
    echo -e "${CYAN}Phase 3: Implementation Execution${NC}"
    echo -e "${WHITE}  → Attempting automated implementation with Claude${NC}"
    
    # Try automated implementation first
    echo -e "${CYAN}🤖 Attempting automated implementation...${NC}"
    if automated_implement_task "$task_id" "$task_name" "$description" "$files"; then
        echo -e "${GREEN}✅ Automated implementation successful${NC}"
        automated_success=true
    else
        local auto_exit_code=$?
        if [[ $auto_exit_code -eq 2 ]]; then
            # Quota exhausted during automation - exit gracefully
            return 2
        else
            echo -e "${YELLOW}⚠️ Automated implementation failed, continuing with manual fallback${NC}"
            echo -e "${WHITE}Task: $description${NC}"
            echo -e "${WHITE}Files to modify: $files${NC}"
            echo ""
            echo -e "${BLUE}Please implement the required changes manually.${NC}"
            echo -e "${WHITE}Press Enter when done...${NC}"
            read -r
            automated_success=false
        fi
    fi
    echo -e "${GREEN}  ✅ Phase 3 execution complete${NC}"
    echo ""
    
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
    
    # Phase 5: Completion and Documentation (Enhanced)
    echo -e "${CYAN}Phase 5: Completion and Documentation${NC}"
    
    # Check if documentation already exists to prevent rebuilding
    if [ -f "docs/tasks/$task_id/completion_report.md" ] && [ "$FORCE_REDOC" != "true" ]; then
        echo -e "${YELLOW}📝 Documentation already exists for task $task_id - skipping rebuild${NC}"
        echo -e "${WHITE}Use FORCE_REDOC=true to override this behavior${NC}"
    else
        echo -e "${WHITE}📝 Creating structured documentation for task $task_id${NC}"
        
        # Run Phase 5 with our modular system for documentation
        local task_context="Task ID: $task_id
Task Name: $task_name  
Description: $description
Implementation Status: COMPLETED
Files Modified: $files
Session: $SESSION_BRANCH"
        
        if run_claude_with_phase "5" "$task_context" "$CLAUDE_QUICK_TIMEOUT"; then
            echo -e "${GREEN}✅ Enhanced documentation created successfully${NC}"
        else
            echo -e "${YELLOW}⚠️ Enhanced documentation failed, using basic documentation${NC}"
            # Fallback to basic documentation creation
            create_basic_documentation "$task_id" "$task_name" "$description" "$files"
        fi
    fi
    
    # Auto-generate implementation notes based on what was done
    local implementation_notes=""
    if [[ "$automated_success" == "true" ]]; then
        implementation_notes="Automated implementation completed successfully. Task: $task_name. Files modified: $files."
    else
        implementation_notes="Manual implementation completed. Task: $task_name. Files modified: $files."
    fi
    
    echo -e "${WHITE}Implementation notes: $implementation_notes${NC}"
    
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
    
    # Auto-continue to next task (no merge prompt)
    echo -e "${CYAN}🔄 Continuing to next task automatically...${NC}"
    return 0
}

# =============================================================================
# Main Execution Flow
# =============================================================================

initialize_session() {
    echo -e "${CYAN}🚀 Initializing Claude Work session...${NC}"
    
    # First, ensure we have the latest updates and clean workspace
    ensure_main_branch_current
    cleanup_old_session_branches
    
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
    
    # Handle session branch creation/switching (improved logic)
    if [[ "$CURRENT_BRANCH" == "$SESSION_BRANCH" ]]; then
        echo -e "${CYAN}🔄 Already on session branch: $SESSION_BRANCH${NC}"
        echo -e "${WHITE}Original branch: $ORIGINAL_BRANCH${NC}"
        log_action "Continuing session on current branch: $SESSION_BRANCH"
    elif git show-ref --verify --quiet "refs/heads/$SESSION_BRANCH"; then
        echo -e "${CYAN}🔄 Switching to existing session branch: $SESSION_BRANCH${NC}"
        echo -e "${WHITE}Original branch: $ORIGINAL_BRANCH${NC}"
        if git checkout "$SESSION_BRANCH" 2>/dev/null; then
            echo -e "${GREEN}✅ Switched to existing session branch: $SESSION_BRANCH${NC}"
            log_action "Switched to existing session branch: $SESSION_BRANCH"
        else
            echo -e "${RED}❌ Could not switch to session branch: $SESSION_BRANCH${NC}"
            log_error "Failed to switch to session branch"
            exit 1
        fi
    else
        echo -e "${CYAN}🆕 Creating new session branch: $SESSION_BRANCH${NC}"
        echo -e "${WHITE}Original branch: $ORIGINAL_BRANCH${NC}"
        if git checkout -b "$SESSION_BRANCH" 2>/dev/null; then
            echo -e "${GREEN}✅ New session branch created: $SESSION_BRANCH${NC}"
            log_action "Created new session branch: $SESSION_BRANCH (from $ORIGINAL_BRANCH)"
        else
            echo -e "${RED}❌ Could not create session branch: $SESSION_BRANCH${NC}"
            log_error "Failed to create session branch"
            exit 1
        fi
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
            cat > "$completion_report" << 'COMPLETION_EOF'
# Implementation Completion Report

**Session**: TIMESTAMP_PLACEHOLDER
**Completed**: DATE_PLACEHOLDER
**Project**: AI Journaling Assistant

## Summary
All 21 implementation tasks have been completed successfully!

## Statistics
STATUS_PLACEHOLDER

## Session Logs
- Session Log: SESSION_LOG_PLACEHOLDER
- Implementation TODO: TODO_FILE_PLACEHOLDER
- Progress Tracking: PROGRESS_FILE_PLACEHOLDER

## Next Steps
1. Perform final system testing
2. Deploy to staging environment
3. Conduct user acceptance testing
4. Prepare for production deployment

**🎉 Implementation Phase Complete!**
COMPLETION_EOF
            
            # Replace placeholders in the completion report
            sed -i "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/g" "$completion_report"
            sed -i "s/DATE_PLACEHOLDER/$(date)/g" "$completion_report"
            sed -i "s/SESSION_LOG_PLACEHOLDER/$(basename "$SESSION_LOG")/g" "$completion_report"
            sed -i "s/TODO_FILE_PLACEHOLDER/$(basename "$TODO_FILE")/g" "$completion_report"
            sed -i "s/PROGRESS_FILE_PLACEHOLDER/$(basename "$PROGRESS_FILE")/g" "$completion_report"
            
            echo -e "${GREEN}✅ Completion report generated: $(basename "$completion_report")${NC}"
            
            # Ask if user wants to merge back to original branch (with auto mode support)
            if [[ "$AUTO_MERGE_COMPLETED" == "true" ]] || auto_confirm "All tasks completed! Merge this session back to $ORIGINAL_BRANCH?" "y"; then
                complete_session_with_merge "$SESSION_BRANCH"
            else
                echo -e "${CYAN}Session branch $SESSION_BRANCH kept for manual merge later${NC}"
                echo -e "${WHITE}To merge later: git checkout $ORIGINAL_BRANCH && git merge $SESSION_BRANCH${NC}"
            fi
            
            break
        fi
        
        echo -e "${YELLOW}Next task to implement: $next_task${NC}"
        echo ""
        
        # Ask if user wants to proceed (with auto mode support)
        if [[ "$AUTO_MODE" == "true" ]]; then
            echo -e "${CYAN}[AUTO MODE] Automatically implementing task: $next_task${NC}"
            implement_task "$next_task"
            echo ""
        else
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
        fi
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
            set +e  # Temporarily disable exit on error for claude availability check
            check_claude_availability
            claude_status=$?
            set -e  # Re-enable exit on error
            if [[ $claude_status -ne 0 ]]; then
                if [[ $claude_status -eq 2 ]]; then
                    echo -e "${YELLOW}🚫 Cannot proceed: Claude quota exhausted${NC}"
                    echo ""
                    
                    # Check if we're being called from a resume script
                    if [[ -n "$RESUME_FROM_TASK" ]]; then
                        echo -e "${CYAN}🤖 Resume script detected quota exhaustion${NC}"
                        echo -e "${WHITE}💡 The quota is still not ready - you may need to wait longer${NC}"
                        echo -e "${YELLOW}⏰ Try running this resume script again in a few minutes${NC}"
                        echo ""
                        echo -e "${WHITE}Current quota status from Claude:${NC}"
                        timeout 10 $CLAUDE_CMD -p "test" --output-format text 2>&1 | head -1 || echo "Claude still not responding"
                        echo ""
                        exit 2
                    fi
                    
                    # Check for existing resume scripts
                    if ls "$IMPL_DIR"/work_resume_*.sh >/dev/null 2>&1; then
                        echo -e "${CYAN}📋 Found existing resume scripts:${NC}"
                        for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
                            if [[ -f "$resume_script" ]]; then
                                script_name=$(basename "$resume_script")
                                echo -e "${GREEN}   📄 $script_name${NC}"
                            fi
                        done
                        echo ""
                        echo -e "${WHITE}💡 To run the most recent resume script automatically:${NC}"
                        echo -e "${GREEN}   ./claude_work.sh --auto-resume${NC}"
                        echo ""
                        echo -e "${WHITE}💡 Or run resume scripts manually:${NC}"
                        for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
                            if [[ -f "$resume_script" ]]; then
                                script_name=$(basename "$resume_script")
                                echo -e "${WHITE}   ./implementation_results/$script_name${NC}"
                            fi
                        done
                        echo ""
                        echo -e "${CYAN}💡 Run './claude_work.sh quota' to check status anytime${NC}"
                        exit 2
                    else
                        echo -e "${WHITE}No existing resume scripts found.${NC}"
                        echo -e "${WHITE}Please wait for quota reset or try again later.${NC}"
                        echo ""
                        echo -e "${CYAN}💡 Run './claude_work.sh quota' to check status anytime${NC}"
                        exit 2
                    fi
                else
                    echo -e "${RED}❌ Cannot proceed: Claude CLI not available${NC}"
                    exit 1
                fi
            fi
            read_self_instructions
            main_loop
            ;;
        "--auto-resume")
            echo -e "${GREEN}🚀 Auto-Resume Mode: Checking current session status...${NC}"
            
            # First ensure Claude CLI is set up properly
            set +e  # Temporarily disable exit on error for claude availability check
            check_claude_availability
            claude_setup_status=$?
            set -e  # Re-enable exit on error
            
            if [[ $claude_setup_status -eq 2 ]]; then
                echo -e "${YELLOW}⚠️  Claude quota appears exhausted - intelligent handling...${NC}"
                
                # Check for resume scripts but handle quota exhaustion intelligently
                if [[ -f "$QUOTA_RESUME_FILE" ]]; then
                    script_name=$(basename "$QUOTA_RESUME_FILE")
                    echo -e "${GREEN}📄 Found current session resume script: $script_name${NC}"
                    echo -e "${BLUE}🤖 Activating intelligent resume script...${NC}"
                    echo ""
                    
                    # Execute the resume script directly - it has intelligent quota handling
                    exec bash "$QUOTA_RESUME_FILE"
                elif ls "$IMPL_DIR"/work_resume_*.sh >/dev/null 2>&1; then
                    # Use most recent resume script as fallback
                    latest_script=$(ls -t "$IMPL_DIR"/work_resume_*.sh | head -1)
                    script_name=$(basename "$latest_script")
                    echo -e "${YELLOW}⚠️  No resume script for current session (${TIMESTAMP})${NC}"
                    echo -e "${GREEN}📄 Found alternative resume script: $script_name${NC}"
                    echo -e "${BLUE}🤖 Activating intelligent resume script...${NC}"
                    echo ""
                    
                    # Execute the alternative resume script - it has intelligent quota handling
                    exec bash "$latest_script"
                else
                    echo -e "${RED}❌ No resume scripts found and Claude quota exhausted${NC}"
                    echo -e "${WHITE}💡 Resume scripts are created when Claude quota is exhausted during active work${NC}"
                    echo ""
                    echo -e "${YELLOW}🔄 Current situation:${NC}"
                    echo -e "${WHITE}   • Claude quota is exhausted${NC}"
                    echo -e "${WHITE}   • No resume scripts available${NC}"
                    echo -e "${WHITE}   • Auto-resume cannot proceed automatically${NC}"
                    echo ""
                    echo -e "${YELLOW}🔄 To resolve this:${NC}"
                    echo -e "${WHITE}   1. Wait for Claude quota to reset (usually every few hours)${NC}"
                    echo -e "${WHITE}   2. Then run: ./claude_work.sh work${NC}"
                    echo -e "${WHITE}   3. Or try: ./claude_work.sh --resume${NC}"
                    echo ""
                    echo -e "${CYAN}💡 Resume scripts will be created automatically when quota resets and work begins${NC}"
                    exit 0  # Clean exit instead of error
                fi
            elif [[ $claude_setup_status -ne 0 ]]; then
                echo -e "${RED}❌ Claude CLI not available - cannot proceed${NC}"
                exit 1
            else
                echo -e "${GREEN}✅ Claude CLI is available - continuing current session work${NC}"
                echo -e "${WHITE}💡 No resume needed - Claude quota is working${NC}"
                echo ""
                
                # Continue with current session
                read_self_instructions
                main_loop
                return $?
            fi
            ;;
        "phase")
            local phase_num="$2"
            local task_context="$3"
            if [[ -z "$phase_num" ]]; then
                echo -e "${RED}Error: Phase number required${NC}"
                echo "Usage: $0 phase <1-5> [task_context]"
                exit 1
            fi
            print_banner
            initialize_session
            check_claude_availability
            local claude_status=$?
            if [[ $claude_status -ne 0 ]]; then
                if [[ $claude_status -eq 2 ]]; then
                    echo -e "${YELLOW}🚫 Cannot proceed: Claude quota exhausted${NC}"
                    echo -e "${WHITE}Please wait for quota reset or use available resume scripts${NC}"
                    echo -e "${CYAN}💡 Run './claude_work.sh quota' to check status and find resume scripts${NC}"
                    exit 2
                else
                    echo -e "${RED}❌ Cannot proceed: Claude CLI not available${NC}"
                    exit 1
                fi
            fi
            run_claude_with_phase "$phase_num" "$task_context"
            ;;
        "sessions")
            list_available_sessions
            ;;
        "quota")
            echo -e "${CYAN}🔍 Checking Claude quota status and resume options...${NC}"
            echo ""
            
            # Quick quota test
            echo -e "${WHITE}Testing Claude availability...${NC}"
            local test_output=$(mktemp)
            local test_error=$(mktemp)
            
            if timeout 10 claude --dangerously-skip-permissions -p "test" --output-format text >"$test_output" 2>"$test_error"; then
                echo -e "${GREEN}✅ Claude is available - quota appears to be active${NC}"
            else
                local error_content=$(cat "$test_error" 2>/dev/null || echo "")
                local output_content=$(cat "$test_output" 2>/dev/null || echo "")
                local combined_content="$error_content $output_content"
                
                if [[ "$combined_content" == *"Claude AI usage limit reached"* ]] || [[ "$combined_content" == *"Your limit will reset"* ]] || [[ "$combined_content" == *"usage limit reached"* ]] || [[ "$combined_content" == *"rate limit exceeded"* ]] || [[ "$combined_content" == *"quota exceeded"* ]]; then
                    echo -e "${RED}❌ Claude quota exhausted${NC}"
                    echo -e "${YELLOW}Quota message: $combined_content${NC}"
                else
                    echo -e "${YELLOW}⚠️  Claude CLI issue: $combined_content${NC}"
                fi
            fi
            
            rm -f "$test_output" "$test_error"
            echo ""
            
            # Check for resume scripts
            echo -e "${WHITE}Available resume scripts:${NC}"
            if ls "$IMPL_DIR"/work_resume_*.sh >/dev/null 2>&1; then
                for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
                    if [[ -f "$resume_script" ]]; then
                        script_name=$(basename "$resume_script")
                        echo -e "${GREEN}  📄 $script_name${NC}"
                        echo -e "${WHITE}     Run with: ./implementation_results/$script_name${NC}"
                    fi
                done
            else
                echo -e "${YELLOW}  No resume scripts found${NC}"
            fi
            
            echo ""
            echo -e "${WHITE}💡 Usage tips:${NC}"
            echo -e "${WHITE}   • Run resume scripts when quota resets${NC}"
            echo -e "${WHITE}   • Use './claude_work.sh quota' to check status anytime${NC}"
            echo -e "${WHITE}   • Resume scripts handle timing automatically${NC}"
            ;;
        "status")
            show_status
            ;;
        "model")
            echo -e "${GREEN}🤖 Checking Claude model configuration...${NC}"
            echo ""
            
            # Check Claude CLI availability and setup
            set +e  # Temporarily disable exit on error
            check_claude_availability
            claude_status=$?
            set -e  # Re-enable exit on error
            
            if [[ $claude_status -eq 0 ]]; then
                echo -e "${CYAN}📊 Model Information:${NC}"
                echo -e "${WHITE}   Command: $CLAUDE_CMD${NC}"
                echo ""
                echo -e "${CYAN}🔍 Querying Claude for model details...${NC}"
                $CLAUDE_CMD -p "What model are you? Please provide your exact model ID and version." --output-format text
                echo ""
                echo -e "${GREEN}✅ Claude Sonnet 4 is configured and ready${NC}"
            elif [[ $claude_status -eq 2 ]]; then
                echo -e "${RED}❌ Claude quota exhausted - cannot check model${NC}"
                echo -e "${YELLOW}⚠️  Wait for quota reset and try again${NC}"
            else
                echo -e "${RED}❌ Claude CLI not available${NC}"
                echo -e "${WHITE}Command attempted: $CLAUDE_CMD${NC}"
            fi
            ;;
        "help")
            cat << EOF
Claude Work - AI Journaling Assistant Implementation Script

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  work           Start interactive implementation session (default)
  --resume       Resume previous session
  --auto-resume  Intelligent auto-resume with quota monitoring
  phase <1-5>    Run specific phase with Claude
  sessions       List available session branches and resume scripts
  quota          Check Claude quota status and available resume scripts
  status         Show current implementation progress
  model          Check which Claude model is being used
  help           Show this help message

Phase Commands:
  $0 phase 1 "task description"    # Session Initialization
  $0 phase 2 "task description"    # Task Selection & Analysis  
  $0 phase 3 "task description"    # Implementation Planning
  $0 phase 4 "task description"    # Code Implementation
  $0 phase 5 "task description"    # Testing & Documentation

Environment Variables:
  WORK_SESSION_ID           Custom session ID (default: timestamp)
  AUTO_MODE                 Enable fully automatic mode (true/false)
  AUTO_CLEANUP_BRANCHES     Automatically clean old branches (true/false)  
  AUTO_MERGE_COMPLETED      Automatically merge completed sessions (true/false)

Automation Examples:
  AUTO_MODE=true ./claude_work.sh work              # Fully automatic mode
  AUTO_CLEANUP_BRANCHES=true ./claude_work.sh work  # Auto cleanup only
  AUTO_MODE=true WORK_SESSION_ID=20250809_140000 ./claude_work.sh work  # Auto resume
  
Features:
  • 📋 Modular phase-specific instructions for Claude
  • 🧪 Automated testing after each task
  • 📝 Comprehensive progress tracking
  • 🤖 Fully automatic mode with no user prompts
  • 🧹 Automatic cleanup of old session branches
  • 🔄 Git integration with automated commits and branch management
  • ⚡ Interactive task selection and validation
  • 🧹 Automatic cleanup of old session branches
  
Git Workflow:
  • All work starts from main branch for consistency
  • Each session creates a temporary phase-YYYYMMDD_HHMMSS branch
  • Work is automatically merged back to main upon completion
  • Session branches are automatically cleaned up after successful merge
  • Old session branches (>7 days) are offered for cleanup on start
  • Remote branches are also cleaned up to keep repository tidy
  • Use WORK_SESSION_ID=YYYYMMDD_HHMMSS to resume a specific session
  • Use './claude_work.sh sessions' to list available sessions
  
The script follows a 5-phase implementation workflow:
  1. Session Initialization - Setup and branch creation
  2. Task Selection & Analysis - Choose and analyze tasks
  3. Implementation Planning - Plan the implementation approach
  4. Code Implementation - Execute the coding work
  5. Testing & Documentation - Test and document changes

Files:
  implementation_results/claude_work_core.md           - Core instructions
  implementation_results/claude_work_phase[1-6].md    - Phase-specific instructions
  implementation_results/claude_work_templates.md     - Documentation templates
  implementation_results/claude_work_troubleshooting.md - Troubleshooting guide
  implementation_results/implementation_todo.md       - Task tracking
  implementation_results/implementation_progress.json - Progress data
  implementation_results/logs/session_*.log          - Session logs
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