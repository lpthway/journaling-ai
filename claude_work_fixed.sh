#!/bin/bash

# =============================================================================
# FIXED: AI Journaling Assistant - Claude Work Implementation Script
# =============================================================================
# Purpose: Step-by-step implementation with CORRECT Claude CLI streaming
# Author: Claude Work Protocol v2.0 - FIXED STREAMING
# Date: $(date +%Y-%m-%d)
# =============================================================================

# This demonstrates the CORRECTED Claude CLI streaming parser

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failure

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Simple test function to demonstrate correct Claude CLI streaming
test_claude_streaming() {
    local prompt="$1"
    
    echo -e "${CYAN}🔬 Testing Claude CLI streaming with CORRECT parser...${NC}"
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT START ━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Function to parse Claude CLI's ACTUAL stream-json format
    parse_claude_cli_json() {
        local line="$1"
        python3 -c "
import json
import sys
from datetime import datetime

def format_content_blocks(content_blocks):
    \"\"\"Format content blocks for display\"\"\"
    output = []
    for block in content_blocks:
        if isinstance(block, dict):
            if block.get('type') == 'text':
                text = block.get('text', '').strip()
                if text:
                    # This is the ACTUAL implementation content!
                    output.append(f'💬 {text}')
            elif block.get('type') == 'tool_use':
                tool_name = block.get('name', 'unknown')
                tool_input = block.get('input', {})
                output.append(f'🔧 Tool: {tool_name}')
                if tool_input:
                    # Show actual tool parameters
                    input_str = str(tool_input)
                    if len(input_str) > 150:
                        input_str = input_str[:150] + '...'
                    output.append(f'   └─ Input: {input_str}')
    return output

try:
    data = json.loads('$line')
    msg_type = data.get('type', '')
    timestamp = datetime.now().strftime('%H:%M:%S')
    
    if msg_type == 'system':
        subtype = data.get('subtype', '')
        if subtype == 'init':
            session_id = data.get('session_id', 'unknown')
            model = data.get('model', 'unknown')
            tools = data.get('tools', [])
            print(f'🚀 [{timestamp}] Claude Code initialized!')
            print(f'   └─ Session: {session_id[:8]}...')
            print(f'   └─ Model: {model}')
            print(f'   └─ Tools: {len(tools)} available')
        else:
            print(f'🧠 [{timestamp}] System: {subtype}')
    
    elif msg_type == 'user':
        message = data.get('message', {})
        content = message.get('content', [])
        print(f'👤 [{timestamp}] Processing user request...')
        
    elif msg_type == 'assistant':
        message = data.get('message', {})
        content = message.get('content', [])
        usage = message.get('usage', {})
        
        print(f'🤖 [{timestamp}] Claude is implementing...')
        
        # Show token usage
        if usage:
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            if input_tokens or output_tokens:
                print(f'📊 [{timestamp}] Tokens: {input_tokens} in + {output_tokens} out')
        
        # THIS IS WHERE THE ACTUAL CONTENT APPEARS!
        if isinstance(content, list) and content:
            content_output = format_content_blocks(content)
            for line in content_output:
                print(f'   {line}')
                
    elif msg_type == 'result':
        subtype = data.get('subtype', '')
        duration_ms = data.get('duration_ms', 0)
        num_turns = data.get('num_turns', 0)
        total_cost_usd = data.get('total_cost_usd', 0)
        
        if subtype == 'success':
            print(f'✅ [{timestamp}] Implementation completed!')
            print(f'   └─ Duration: {duration_ms/1000:.1f}s')
            print(f'   └─ Turns: {num_turns}')
            print(f'   └─ Cost: \${total_cost_usd:.4f}')
        else:
            print(f'❌ [{timestamp}] Task finished: {subtype}')
    
    else:
        print(f'📡 [{timestamp}] Event: {msg_type}')

except json.JSONDecodeError:
    # Plain text output
    line_content = '$line'.strip()
    if line_content:
        print(f'📄 [{datetime.now().strftime(\"%H:%M:%S\")}] {line_content}')
except Exception as e:
    pass  # Skip parsing errors
" 2>/dev/null
    }
    
    # Stream Claude CLI output with correct parser
    timeout 30 claude -p "$prompt" --output-format stream-json --verbose 2>/dev/null | while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            parse_claude_cli_json "$line"
        fi
    done
    
    echo ""
    echo -e "${WHITE}━━━━━━━━━━━━━━━━━━━━━━━━━ CLAUDE OUTPUT END ━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Test completed with CORRECT Claude CLI parser${NC}"
}

# Main function
main() {
    echo -e "${PURPLE}"
    echo "============================================================================="
    echo "           FIXED CLAUDE CLI STREAMING DEMO"
    echo "============================================================================="
    echo -e "${NC}"
    echo -e "${CYAN}This demonstrates the CORRECT way to parse Claude CLI streaming.${NC}"
    echo -e "${WHITE}The issue was: parsing for Anthropic API events instead of Claude CLI events${NC}"
    echo ""
    
    local test_prompt="Create a simple Python function called 'hello_world' that returns 'Hello, World!'"
    
    echo -e "${YELLOW}Testing with prompt: $test_prompt${NC}"
    echo ""
    
    test_claude_streaming "$test_prompt"
    
    echo ""
    echo -e "${GREEN}🔍 Key findings:${NC}"
    echo -e "${WHITE}• Claude CLI stream-json uses 'system', 'user', 'assistant', 'result' message types${NC}"
    echo -e "${WHITE}• NOT Anthropic API events like 'content_block_start', 'content_block_delta'${NC}"
    echo -e "${WHITE}• Actual implementation content is in 'assistant' messages with content blocks${NC}"
    echo -e "${WHITE}• Tool usage and parameters are fully visible with correct parsing${NC}"
    echo ""
    echo -e "${CYAN}✨ This fixed parser should show Claude's actual implementation work!${NC}"
}

# Run the demo
main "$@"
