#!/bin/bash

# Extract and test just the parse_claude_json function from the main script
parse_claude_json() {
    local line="$1"
    if [[ -n "$line" ]]; then
        python3 -c "
import json
import sys
from datetime import datetime

try:
    line = sys.argv[1] if len(sys.argv) > 1 else ''; data = json.loads(line) if line else {}
    event_type = data.get('type', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Claude CLI uses different message types: system, user, assistant, result
    if event_type == 'system':
        print(f'🧠 [{timestamp}] System message')
    elif event_type == 'user':
        print(f'👤 [{timestamp}] User message processed')
    elif event_type == 'assistant':
        content = data.get('content', '')
        if content and isinstance(content, str) and len(content.strip()) > 0:
            # Real assistant text content
            print(f'🤖 [{timestamp}] Claude: {content[:100]}...' if len(content) > 100 else f'🤖 [{timestamp}] Claude: {content}')
        else:
            print(f'🤖 [{timestamp}] Assistant is processing...')
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
                        
                        print(f'🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                        
                        # Show specific tool details
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', tool_input.get('file_path', 'unknown'))
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'📄 Creating: {file_path}')
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
                            print(f'👀 Reading: {file_path} (lines {start_line}-{end_line})')
                        elif tool_name == 'run_in_terminal':
                            command = tool_input.get('command', 'unknown')
                            print(f'⚡ Running: {command[:50]}...' if len(command) > 50 else f'⚡ Running: {command}')
                        elif tool_name == 'list_dir':
                            path = tool_input.get('path', 'unknown')
                            print(f'📁 Listing directory: {path}')
                        else:
                            # Generic tool display
                            print(f'⚙️  Tool parameters: {str(tool_input)[:100]}...' if len(str(tool_input)) > 100 else f'⚙️  Tool parameters: {tool_input}')
                    elif item_type == 'text':
                        text_content = item.get('text', '')
                        if text_content and len(text_content.strip()) > 0:
                            print(f'💬 [{timestamp}] {text_content[:200]}...' if len(text_content) > 200 else f'💬 [{timestamp}] {text_content}')
    elif event_type == 'error':
        error_msg = data.get('error', {}).get('message', 'Unknown error')
        print(f'❌ [{timestamp}] Error: {error_msg}')
    elif event_type == 'ping':
        print(f'💓 [{timestamp}] Connection alive')
    else:
        # For debugging other event types
        if event_type:
            print(f'📡 [{timestamp}] Event: {event_type}')

except json.JSONDecodeError:
    # Not valid JSON, might be direct text output
    if line and len(line.strip()) > 0:
        print(f'📄 [{timestamp}] Direct output: {line}')
except Exception as e:
    # For debugging
    if line and len(line.strip()) > 0 and len(line) < 200:
        print(f'🔍 [{timestamp}] Raw: {line}')
" "$line" 2>/dev/null
    fi
}

echo "Testing fixed parse_claude_json function..."

# Test with tool usage
test_json='{"type":"result","content":[{"type":"tool_use","id":"tool_123","name":"create_file","input":{"filePath":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

echo "Input: $test_json"
echo "Output:"
parse_claude_json "$test_json"

echo ""
echo "Testing with multiple events:"

# Test system message
parse_claude_json '{"type":"system"}'

# Test user message  
parse_claude_json '{"type":"user"}'

# Test assistant message
parse_claude_json '{"type":"assistant","content":"I need to create a file"}'
