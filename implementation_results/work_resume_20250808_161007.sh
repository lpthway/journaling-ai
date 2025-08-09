#!/bin/bash
# Resume Implementation Script - Generated automatically
# Resume from task: phase-5
# Generated: Sa 9. Aug 09:34:29 CEST 2025

export WORK_SESSION_ID="20250808_161007"
export RESUME_FROM_TASK="phase-5"

echo "🔄 Resuming implementation from task: phase-5"
echo "📅 Original session: 20250808_161007"
echo "⏳ Waiting for Claude quota to refresh..."

# Wait a bit before resuming
sleep 5

# Resume the work
cd "/home/abrasko/Projects/journaling-ai"
./claude_work.sh --resume

if [[ $? -eq 0 ]]; then
    echo "✅ Resume script completed successfully"
    echo "🧹 Cleaning up resume script..."
    rm -f "$0"
    echo "✅ Resume script removed"
else
    echo "❌ Resume failed - keeping script for retry"
    echo "💡 You can run this script again: $0"
fi
