#!/bin/bash

# Debug test for the tool usage parsing
echo "🔍 Debugging tool usage parsing..."

# Test with a simple tool usage message
line='{"type":"result","content":[{"type":"tool_use","name":"create_file","id":"tool_123","input":{"file_path":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

echo "Input: $line"
echo "Output:"

python3 << 'EOF'
import json
import sys
from datetime import datetime

line = '''{"type":"result","content":[{"type":"tool_use","name":"create_file","id":"tool_123","input":{"file_path":"/home/test.py","content":"def hello():\\n    return \\"Hello World\\""}}]}'''

try:
    data = json.loads(line)
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    print(f"Parsed data: {data}")
    
    if 'type' in data:
        msg_type = data['type']
        print(f"Message type: {msg_type}")
        
        if msg_type == 'result':
            print("Processing result message...")
            content = data.get('content', [])
            print(f"Content: {content}")
            
            if isinstance(content, list):
                print(f"Content is list with {len(content)} items")
                for i, item in enumerate(content):
                    print(f"Item {i}: {item}")
                    if isinstance(item, dict):
                        if item.get('type') == 'tool_use':
                            tool_name = item.get('name', 'unknown')
                            tool_input = item.get('input', {})
                            tool_id = item.get('id', 'unknown')
                            
                            print(f'🔧 [{timestamp}] Using tool: {tool_name} (ID: {tool_id})')
                            
                            if tool_name == 'create_file' and 'file_path' in tool_input:
                                file_path = tool_input['file_path']
                                content_preview = str(tool_input.get('content', ''))[:100]
                                print(f'   📄 Creating: {file_path}')
                                print(f'   💾 Content preview: {content_preview}...')

except Exception as e:
    print(f"Error: {e}")
EOF
