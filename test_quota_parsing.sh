#!/bin/bash

# Function definitions
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
    return $?
}

# Test cases
echo "=== Testing Quota Parsing System ==="
echo

# Test 1: Timestamp format (actual Claude format)
echo "Test 1: Timestamp format"
quota_msg1="Claude AI usage limit reached|1754578800"
echo "Input: $quota_msg1"
parsed1=$(parse_quota_reset_time "$quota_msg1")
echo "Parsed: $parsed1"

if [[ -n "$parsed1" ]]; then
    echo "Wait calculation:"
    calculate_wait_time "$parsed1"
else
    echo "❌ Parsing failed"
fi

echo
echo "----------------------------------------"
echo

# Test 2: Text format
echo "Test 2: Text format"
quota_msg2="Claude usage limit reached. Your limit will reset at 5pm (Europe/Berlin)."
echo "Input: $quota_msg2"
parsed2=$(parse_quota_reset_time "$quota_msg2")
echo "Parsed: $parsed2"

if [[ -n "$parsed2" ]]; then
    echo "Wait calculation:"
    calculate_wait_time "$parsed2"
else
    echo "❌ Parsing failed"
fi

echo
echo "=== Test Complete ==="
