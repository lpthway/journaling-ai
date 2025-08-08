#!/bin/bash

# Extract the parse_claude_json function from the main script and test it
echo "Testing parse_claude_json function extracted from claude_work.sh..."

# Source the main script to get the function
source /home/abrasko/Projects/journaling-ai/claude_work.sh 2>/dev/null

# Test with different Claude CLI event types
echo ""
echo "=== Test 1: System message ==="
parse_claude_json '{"type":"system"}'

echo ""
echo "=== Test 2: User message ==="
parse_claude_json '{"type":"user"}'

echo ""
echo "=== Test 3: Assistant message ==="
parse_claude_json '{"type":"assistant","content":"I will help you implement this feature"}'

echo ""
echo "=== Test 4: Result with tool_use (THIS IS THE IMPORTANT ONE!) ==="
parse_claude_json '{"type":"result","content":[{"type":"tool_use","id":"tool_123","name":"create_file","input":{"filePath":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

echo ""
echo "=== Test 5: Result with replace_string_in_file ==="
parse_claude_json '{"type":"result","content":[{"type":"tool_use","id":"tool_456","name":"replace_string_in_file","input":{"filePath":"/home/config.json","oldString":"old value","newString":"new value"}}]}'

echo ""
echo "If Test 4 and 5 show tool usage details, the parser is working correctly!"
