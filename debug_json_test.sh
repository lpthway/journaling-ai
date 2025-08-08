#!/bin/bash

echo "Testing minimal JSON parser..."

# Simple test function
test_json_parsing() {
    local input_json="$1"
    echo "Input: $input_json"
    
    python3 -c "
import json
import sys
from datetime import datetime

try:
    line = '$input_json'
    print(f'Processing line: {line}')
    data = json.loads(line)
    print(f'Parsed JSON successfully: {data}')
    event_type = data.get('type', '')
    print(f'Event type: {event_type}')
    
    if event_type == 'result':
        print('✅ Found result event - this is where tool usage appears!')
        content = data.get('content', [])
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'tool_use':
                tool_name = item.get('name', 'unknown')
                print(f'🔧 Tool found: {tool_name}')
                print('✅ SUCCESS: This would show real implementation work!')

except Exception as e:
    print(f'❌ Error: {e}')
" 2>/dev/null
}

# Test with a simple result event
echo "=== Testing result event ==="
test_json_parsing '{"type":"result","content":[{"type":"tool_use","id":"tool_123","name":"create_file","input":{"filePath":"/home/test.py"}}]}'

echo ""
echo "=== Testing system event ==="  
test_json_parsing '{"type":"system"}'

echo ""
echo "=== Testing user event ==="
test_json_parsing '{"type":"user"}'
