#!/bin/bash

# Corrected Claude CLI JSON Parser Function
# This replaces the parse_claude_json function in claude_work.sh

parse_claude_json() {
    local line="$1"
    if [[ -n "$line" ]]; then
        # Parse Claude CLI stream-json format (system/user/assistant/result messages)
        python3 << 'PYTHON_EOF'
import json
import sys
from datetime import datetime
import os

# Get the line from environment variable to avoid shell escaping issues
line = os.environ.get('PARSE_LINE', '')

try:
    data = json.loads(line)
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    # Handle Claude CLI message-based format
    if 'type' in data:
        msg_type = data['type']
        
        if msg_type == 'system':
            print(f'🧠 [{timestamp}] System message')
            
        elif msg_type == 'user':
            print(f'👤 [{timestamp}] User message processed')
            
        elif msg_type == 'assistant':
            print(f'🤖 [{timestamp}] Assistant is processing...')
            
        elif msg_type == 'result':
            # This contains the actual implementation work and tool usage
            content = data.get('content', [])
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text = item.get('text', '')
                            if text.strip():
                                # Display Claude's reasoning and explanations
                                print(f'💭 [{timestamp}] Claude: {text[:200]}...' if len(text) > 200 else f'💭 [{timestamp}] Claude: {text}')
                        
                        elif item.get('type') == 'tool_use':
                            # This is the key improvement - show actual tool usage with parameters
                            tool_name = item.get('name', 'unknown')
                            tool_input = item.get('input', {})
                            tool_id = item.get('id', 'unknown')
                            
                            print(f'🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                            
                            # Show specific tool parameters for common tools
                            if tool_name == 'create_file' and 'file_path' in tool_input:
                                file_path = tool_input['file_path']
                                content_preview = str(tool_input.get('content', ''))[:100]
                                print(f'   📄 Creating: {file_path}')
                                print(f'   💾 Content preview: {content_preview}...')
                                
                            elif tool_name == 'replace_string_in_file' and 'filePath' in tool_input:
                                file_path = tool_input['filePath']
                                old_str = str(tool_input.get('oldString', ''))[:50]
                                new_str = str(tool_input.get('newString', ''))[:50]
                                print(f'   📝 Editing: {file_path}')
                                print(f'   🔄 Replacing: {old_str}... -> {new_str}...')
                                
                            elif tool_name == 'run_in_terminal' and 'command' in tool_input:
                                command = tool_input['command']
                                explanation = tool_input.get('explanation', 'Running command')
                                print(f'   💻 Command: {command}')
                                print(f'   📋 Purpose: {explanation}')
                                
                            else:
                                # Generic parameter display for other tools
                                if tool_input:
                                    print(f'   ⚙️  Parameters: {str(tool_input)[:150]}...' if len(str(tool_input)) > 150 else f'   ⚙️  Parameters: {tool_input}')
            
            elif isinstance(content, str) and content.strip():
                print(f'💬 [{timestamp}] Response: {content[:200]}...' if len(content) > 200 else f'💬 [{timestamp}] Response: {content}')
        
        # Handle token usage and performance metrics
        elif 'usage' in data:
            usage = data['usage']
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            print(f'📊 [{timestamp}] Token usage: {input_tokens} in + {output_tokens} out = {total_tokens} total')
            
        # Handle streaming events
        elif 'event' in data:
            event = data['event']
            print(f'📡 [{timestamp}] Event: {event}')
            
        else:
            # Handle any other structured data
            print(f'📡 [{timestamp}] Data: {str(data)[:100]}...' if len(str(data)) > 100 else f'📡 [{timestamp}] Data: {data}')
    
    # Handle direct message format (some Claude CLI versions)
    elif 'content' in data or 'message' in data:
        content = data.get('content', data.get('message', ''))
        if isinstance(content, str) and content.strip():
            print(f'💬 [{timestamp}] Direct: {content[:200]}...' if len(content) > 200 else f'💬 [{timestamp}] Direct: {content}')
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    text = item.get('text', '')
                    if text.strip():
                        print(f'💭 [{timestamp}] Text: {text[:200]}...' if len(text) > 200 else f'💭 [{timestamp}] Text: {text}')
    
    else:
        # Fallback: try to show any readable content
        readable_content = str(data)
        if len(readable_content.strip()) > 0 and len(readable_content) < 300:
            print(f'🔍 [{timestamp}] Raw: {readable_content}')

except json.JSONDecodeError:
    # If it's not JSON, show as direct output
    if line and len(line.strip()) > 0:
        print(f'📄 Direct output: {line}')
except Exception as e:
    # For debugging, show parsing errors (limited to avoid spam)
    if line and len(line.strip()) > 0 and len(line) < 500:
        print(f'🔍 Parse error for: {line}')
PYTHON_EOF
    fi
}

# Test the function
echo "🧪 Testing corrected parse_claude_json function..."

# Export test line as environment variable and test
export PARSE_LINE='{"type":"result","content":[{"type":"tool_use","name":"create_file","id":"tool_123","input":{"file_path":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'
echo "Testing tool usage parsing:"
parse_claude_json "$PARSE_LINE"

echo ""
echo "✅ Function test complete. This corrected function should replace the one in claude_work.sh"
