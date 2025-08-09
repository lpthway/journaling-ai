#!/bin/bash
# Intelligent Auto-Resume Work Script - Generated with intelligent scheduling
# Resume from task: 6.1
# Scheduled resume time: 2025-08-09 19:00:00
# Generated: Sa 9. Aug 15:13:30 CEST 2025

export WORK_SESSION_ID="20250808_161007"
export RESUME_FROM_TASK="6.1"

echo "🤖 Intelligent Auto-Resume Work Script Activated"
echo "📅 Original session: 20250808_161007"
echo "⏰ Claude quota will reset at: 2025-08-09 19:00:00"
echo "🕐 Current time: $(date)"
echo ""

# Calculate remaining wait time dynamically (in case script is run later)
reset_timestamp=$(date -d "2025-08-09 19:00:00" +%s 2>/dev/null)
current_timestamp=$(date +%s)

if [[ -n "$reset_timestamp" ]] && [[ "$reset_timestamp" -gt "$current_timestamp" ]]; then
    wait_seconds=$(($reset_timestamp - $current_timestamp + 120))  # Add 2-minute buffer
else
    # Fallback: if we can't parse the time, assume quota is ready
    wait_seconds=0
    echo "⚠️  Could not calculate remaining time - assuming quota is ready"
fi

if [[ $wait_seconds -gt 0 ]]; then
    echo "⏳ Waiting $wait_seconds seconds ($(($wait_seconds / 60)) minutes) for quota reset..."
    echo "💡 You can safely close this terminal - the script will complete automatically"
    echo "🎯 Will auto-resume at: 2025-08-09 19:00:00"
    echo ""
    echo "⏱️  Countdown:"
    
    # Intelligent countdown with progress indicators
    while [[ $wait_seconds -gt 0 ]]; do
        hours=$(($wait_seconds / 3600))
        minutes=$(( ($wait_seconds % 3600) / 60 ))
        seconds=$(($wait_seconds % 60))
        
        if [[ $hours -gt 0 ]]; then
            printf "\r   🕐 %02d:%02d:%02d remaining - Resume at 2025-08-09 19:00:00" $hours $minutes $seconds
        else
            printf "\r   ⏰ %02d:%02d remaining - Resume at 2025-08-09 19:00:00" $minutes $seconds
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
        echo "   ./claude_work.sh --resume"
        exit 1
    fi
fi

echo "🔄 Resuming intelligent work from task: 6.1"
echo ""

# Resume the work
cd "/home/abrasko/Projects/journaling-ai"
./claude_work.sh --resume

if [[ $? -eq 0 ]]; then
    echo ""
    echo "✅ Intelligent auto-resume completed successfully!"
    echo "📊 Check the implementation results in: /home/abrasko/Projects/journaling-ai/implementation_results/"
    echo ""
    echo "🧹 Cleaning up resume script..."
    rm -f "$0"
    echo "✅ Resume script removed"
else
    echo ""
    echo "❌ Resume failed - keeping script for retry"
    echo "💡 You can run this script again: $0"
fi
