#!/bin/bash

# Test the multi-line output handling
cd /home/abrasko/Projects/journaling-ai

echo "Testing multi-line parse_claude_json output handling..."

# Simulate the exact function from claude_work.sh
parse_claude_json() {
    local line="$1"
    if [[ -n "$line" ]]; then
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
    
    if event_type == 'result':
        content = data.get('content', [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'tool_use':
                    tool_name = item.get('name', 'unknown')
                    tool_id = item.get('id', 'unknown')
                    tool_input = item.get('input', {})
                    
                    print(f'🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                    
                    if tool_name == 'create_file':
                        file_path = tool_input.get('filePath', 'unknown')
                        content_preview = str(tool_input.get('content', ''))[:50]
                        print(f'📄 Creating: {file_path}')
                        print(f'💾 Content preview: {content_preview}...')

except Exception as e:
    pass
" 2>/dev/null
    fi
}

# Test with JSON that should produce multiple lines
test_json='{"type":"result","content":[{"type":"tool_use","id":"tool_123","name":"create_file","input":{"filePath":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

echo "Input JSON: $test_json"
echo ""
echo "Testing multi-line capture:"

# Test the multi-line handling
claude_activity=$(parse_claude_json "$test_json")
echo "Captured output:"
echo "«$claude_activity»"

echo ""
echo "Testing line-by-line display:"
if [[ -n "$claude_activity" ]]; then
    while IFS= read -r activity_line; do
        if [[ -n "$activity_line" ]]; then
            echo "│ $activity_line"
        fi
    done <<< "$claude_activity"
else
    echo "No output captured!"
fi

echo ""
echo "✅ Test completed!"
