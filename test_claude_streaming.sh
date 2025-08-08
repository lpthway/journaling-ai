#!/bin/bash

# Test script to verify the corrected Claude CLI streaming parser
echo "🔧 Testing Claude CLI streaming with corrected parser..."

# Source the functions from claude_work.sh
source claude_work.sh

# Test the parse_claude_json function with Claude CLI format examples
test_claude_cli_message() {
    local message="$1"
    echo "📨 Testing message: $message"
    
    # Create a temporary function that calls parse_claude_json
    bash -c "
        source claude_work.sh
        parse_claude_json '$message'
    "
    echo ""
}

echo "🧪 Testing Claude CLI message formats..."
echo ""

# Test system message
test_claude_cli_message '{"type":"system"}'

# Test user message
test_claude_cli_message '{"type":"user"}'

# Test assistant message
test_claude_cli_message '{"type":"assistant"}'

# Test result with tool usage
test_claude_cli_message '{"type":"result","content":[{"type":"tool_use","name":"create_file","id":"tool_123","input":{"file_path":"/home/test.py","content":"def hello():\n    return \"Hello World\""}}]}'

# Test result with text content
test_claude_cli_message '{"type":"result","content":[{"type":"text","text":"I will create a simple Python function for you."}]}'

# Test token usage
test_claude_cli_message '{"usage":{"input_tokens":50,"output_tokens":25}}'

echo "✅ Claude CLI streaming parser test complete!"
