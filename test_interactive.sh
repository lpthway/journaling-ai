#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

PROJECT_ROOT="/home/abrasko/Projects/journaling-ai"
IMPL_DIR="$PROJECT_ROOT/implementation_results"

# Simulate the interactive part directly
echo -e "${YELLOW}🚫 Cannot proceed: Claude quota exhausted${NC}"
echo ""

# Check for existing resume scripts
if ls "$IMPL_DIR"/work_resume_*.sh >/dev/null 2>&1; then
    echo -e "${CYAN}📋 Found existing resume scripts:${NC}"
    for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
        if [[ -f "$resume_script" ]]; then
            script_name=$(basename "$resume_script")
            echo -e "${GREEN}   📄 $script_name${NC}"
        fi
    done
    echo ""
    echo -e "${WHITE}Would you like to run the most recent resume script now?${NC}"
    echo -e "${YELLOW}It will wait for quota reset and automatically continue.${NC}"
    echo ""
    read -p "Run resume script now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Find the most recent resume script
        latest_script=$(ls -t "$IMPL_DIR"/work_resume_*.sh | head -1)
        script_name=$(basename "$latest_script")
        echo -e "${GREEN}🚀 Starting resume script: $script_name${NC}"
        echo -e "${CYAN}💡 Press Ctrl+C anytime to cancel and resume manually later${NC}"
        echo ""
        # Change to project root and run the script
        cd "$PROJECT_ROOT"
        echo "Would exec: bash ./implementation_results/$script_name"
    else
        echo -e "${WHITE}💡 You can run resume scripts manually later:${NC}"
        for resume_script in "$IMPL_DIR"/work_resume_*.sh; do
            if [[ -f "$resume_script" ]]; then
                script_name=$(basename "$resume_script")
                echo -e "${WHITE}   ./implementation_results/$script_name${NC}"
            fi
        done
    fi
else
    echo -e "${WHITE}No existing resume scripts found.${NC}"
    echo -e "${WHITE}Please wait for quota reset or try again later.${NC}"
fi
echo ""
echo -e "${CYAN}💡 Run './claude_work.sh quota' to check status anytime${NC}"
echo "Done!"
