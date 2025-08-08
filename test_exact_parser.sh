#!/bin/bash

# Test the EXACT parse_claude_json function from claude_work.sh after our fixes
cd /home/abrasko/Projects/journaling-ai

echo "🧪 Testing the UPDATED parse_claude_json function with real Claude CLI output..."

# Define the exact function as it exists in claude_work.sh after our fixes
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
                        
                        # Show specific tool details
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', tool_input.get('file_path', 'unknown'))
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'📄 Creating: {file_path}')
                            print(f'💾 Content preview: {content_preview}...')
                        elif tool_name == 'Write':
                            file_path = tool_input.get('file_path', 'unknown')
                            content_preview = str(tool_input.get('content', ''))[:100]
                            print(f'📄 Writing to: {file_path}')
                            print(f'💾 Content preview: {content_preview}...')
                        elif tool_name == 'replace_string_in_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            old_str_preview = str(tool_input.get('oldString', ''))[:50]
                            print(f'📝 Editing: {file_path}')
                            print(f'🔄 Replacing: {old_str_preview}...')
                        elif tool_name == 'read_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            start_line = tool_input.get('startLine', 'N/A')
                            end_line = tool_input.get('endLine', 'N/A')
                            print(f'📖 Reading: {file_path} (lines {start_line}-{end_line})')
                        elif tool_name == 'run_in_terminal':
                            command = tool_input.get('command', 'unknown')
                            print(f'⚡ Running: {command[:50]}...' if len(command) > 50 else f'⚡ Running: {command}')
                        elif tool_name == 'list_dir':
                            path = tool_input.get('path', 'unknown')
                            print(f'📁 Listing directory: {path}')
                        else:
                            # Generic tool display
                            print(f'⚙️  Tool: {tool_name} with {len(str(tool_input))} chars of input')
                    elif item_type == 'text':
                        text_content = item.get('text', '')
                        if text_content and len(text_content.strip()) > 0:
                            print(f'🤖 [{timestamp}] Claude: {text_content[:200]}...' if len(text_content) > 200 else f'🤖 [{timestamp}] Claude: {text_content}')
        else:
            print(f'🤖 [{timestamp}] Assistant response (non-array content)')
    elif event_type == 'result':
        result_text = data.get('result', '')
        duration_ms = data.get('duration_ms', 0)
        print(f'✅ [{timestamp}] Completed: {result_text} ({duration_ms}ms)')
    else:
        print(f'📡 [{timestamp}] Event: {event_type}')

except json.JSONDecodeError:
    # Not valid JSON, might be direct text output
    if line and len(line.strip()) > 0:
        print(f'📄 [{timestamp}] Direct output: {line}')
except Exception as e:
    # For debugging
    if line and len(line.strip()) > 0 and len(line) < 200:
        print(f'🔍 [{timestamp}] Raw: {line}')
" 2>/dev/null
    fi
}

echo ""
echo "Test 1: Real Claude CLI tool usage (Write tool)"
test_json='{"type":"assistant","message":{"content":[{"type":"tool_use","id":"toolu_018ufD1KjPK4Fq4wtS9aqgc5","name":"Write","input":{"file_path":"/home/abrasko/Projects/journaling-ai/hello.py","content":"def hello_world():\n    print(\"Hello, World!\")"}}]}}'
echo "Input: ${test_json:0:100}..."
echo "Output:"
parse_claude_json "$test_json"

echo ""
echo "Test 2: System initialization"
test_json2='{"type":"system","subtype":"init","session_id":"test123","model":"claude-sonnet-4-20250514"}'
echo "Input: $test_json2"
echo "Output:"
parse_claude_json "$test_json2"

echo ""
echo "Test 3: Claude text response"
test_json3='{"type":"assistant","message":{"content":[{"type":"text","text":"I will create the hello.py file for you."}]}}'
echo "Input: $test_json3"
echo "Output:"
parse_claude_json "$test_json3"

echo ""
echo "✅ All tests completed! The parser should now work correctly in claude_work.sh"
