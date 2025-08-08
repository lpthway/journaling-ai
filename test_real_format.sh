#!/bin/bash

# Test the updated parse_claude_json function with actual Claude CLI output
cd /home/abrasko/Projects/journaling-ai

echo "Testing updated parser with actual Claude CLI output..."

# Simulate the function from claude_work.sh with the assistant fixes
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
    
    if event_type == 'system':
        subtype = data.get('subtype', '')
        if subtype == 'init':
            print(f'🧠 [{timestamp}] Claude session initialized')
        else:
            print(f'🧠 [{timestamp}] System: {subtype}')
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
                        
                        print(f'🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                        
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'📄 Creating: {file_path}')
                            print(f'💾 Content preview: {content_preview}...')
                    elif item_type == 'text':
                        text_content = item.get('text', '')
                        if text_content and len(text_content.strip()) > 0:
                            print(f'🤖 [{timestamp}] Claude: {text_content}')
        else:
            print(f'🤖 [{timestamp}] Assistant response (non-array content)')
    elif event_type == 'result':
        result_text = data.get('result', '')
        duration_ms = data.get('duration_ms', 0)
        print(f'✅ [{timestamp}] Completed: {result_text} ({duration_ms}ms)')
    else:
        print(f'📡 [{timestamp}] Event: {event_type}')

except Exception as e:
    print(f'❌ Error: {e}')
" 2>/dev/null
    fi
}

echo ""
echo "Test 1: System init message"
test1='{"type":"system","subtype":"init","cwd":"/home/abrasko/Projects/journaling-ai","session_id":"test"}'
echo "Input: $test1"
echo "Output:"
parse_claude_json "$test1"

echo ""
echo "Test 2: Assistant text response"
test2='{"type":"assistant","message":{"content":[{"type":"text","text":"Hello, this is a test"}]}}'
echo "Input: $test2"
echo "Output:"
parse_claude_json "$test2"

echo ""
echo "Test 3: Result message"
test3='{"type":"result","subtype":"success","is_error":false,"duration_ms":1983,"result":"Hello, this is a test"}'
echo "Input: $test3"
echo "Output:"
parse_claude_json "$test3"

echo ""
echo "✅ Testing completed!"
