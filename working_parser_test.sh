#!/bin/bash

# Working Claude CLI parser test
echo "Testing corrected Claude CLI JSON parser..."

# Test JSON that simulates Claude CLI result message with tool usage
test_json='{"type":"result","content":[{"type":"tool_use","id":"tool_123","name":"create_file","input":{"filePath":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

echo "Test JSON: $test_json"
echo ""
echo "Running corrected parser:"

# Working parser function
python3 -c "
import json
import sys
from datetime import datetime

try:
    # Get JSON from command line argument
    line = sys.argv[1] if len(sys.argv) > 1 else ''
    if not line:
        print('No input')
        sys.exit(0)
    
    data = json.loads(line)
    event_type = data.get('type', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    print(f'Event type: {event_type}')
    
    if event_type == 'result':
        print(f'🎯 [{timestamp}] Found RESULT event - this is where tool usage appears!')
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
                        
                        if tool_name == 'create_file':
                            file_path = tool_input.get('filePath', 'unknown')
                            content_preview = str(tool_input.get('content', ''))[:50]
                            print(f'📄 Creating: {file_path}')
                            print(f'💾 Content preview: {content_preview}...')
                            print('✅ SUCCESS: This shows real implementation work!')
                        else:
                            print(f'⚙️  Tool input: {tool_input}')

except Exception as e:
    print(f'Error: {e}')
" "$test_json"

echo ""
echo "✅ This is the format that will show real-time Claude implementation work!"
