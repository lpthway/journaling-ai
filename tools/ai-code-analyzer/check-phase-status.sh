#!/bin/bash

# AI Code Analyzer - Phase Management Helper Script
# This script helps track phase completion and manages transitions

set -e

PROJECT_ROOT="/home/abrasko/Projects/journaling-ai/tools/ai-code-analyzer"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI Code Analyzer - Phase Management${NC}"
echo "=================================================="

# Function to check phase completion
check_phase_completion() {
    local phase_num=$1
    local phase_file="planning/phase-${phase_num}-*.md"
    
    if ls $phase_file 1> /dev/null 2>&1; then
        local file=$(ls $phase_file | head -1)
        local total_tasks=$(grep -c "^- \[ \]" "$file" 2>/dev/null || echo 0)
        local completed_tasks=$(grep -c "^- \[x\]" "$file" 2>/dev/null || echo 0)
        
        if [ "$total_tasks" -gt 0 ]; then
            local completion_percent=$((completed_tasks * 100 / total_tasks))
            echo -e "Phase $phase_num: ${completed_tasks}/${total_tasks} tasks (${completion_percent}%)"
            
            if [ "$completion_percent" -eq 100 ]; then
                echo -e "${GREEN}✅ Phase $phase_num is COMPLETE!${NC}"
                return 0
            else
                echo -e "${YELLOW}🔄 Phase $phase_num is IN PROGRESS${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}📋 Phase $phase_num planning file found but no tasks detected${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Phase $phase_num planning file not found${NC}"
        return 1
    fi
}

# Function to get current phase from project-todo.md
get_current_phase() {
    if grep -q "Phase 1.*CURRENT\|Phase 1.*IN PROGRESS" project-todo.md; then
        echo "1"
    elif grep -q "Phase 2.*CURRENT\|Phase 2.*IN PROGRESS" project-todo.md; then
        echo "2"
    elif grep -q "Phase 3.*CURRENT\|Phase 3.*IN PROGRESS" project-todo.md; then
        echo "3"
    else
        echo "unknown"
    fi
}

# Function to suggest next actions
suggest_next_actions() {
    local current_phase=$1
    
    echo -e "\n${BLUE}📋 Suggested Next Actions:${NC}"
    
    case $current_phase in
        1)
            if check_phase_completion 1; then
                echo -e "${GREEN}🎉 Ready to transition to Phase 2!${NC}"
                echo "1. Run final tests: pytest tests/ --coverage"
                echo "2. Merge Phase 1: git checkout main && git merge feature/phase-1-foundation"
                echo "3. Tag release: git tag v1.0.0-phase1-complete"
                echo "4. Start Phase 2: git checkout -b feature/phase-2-claude-integration"
                echo "5. Update project-todo.md phase status"
                echo "6. Begin Phase 2 planning: cat planning/phase-2-core-engine.md"
            else
                echo "Continue Phase 1 development:"
                echo "1. Check current tasks: cat planning/phase-1-foundation.md"
                echo "2. Continue current branch: git checkout feature/phase-1-foundation"
                echo "3. Focus on: Python project setup → Core data models → CLI framework"
            fi
            ;;
        2)
            if check_phase_completion 2; then
                echo -e "${GREEN}🎉 Ready to transition to Phase 3!${NC}"
                echo "1. Test end-to-end analysis workflow"
                echo "2. Merge Phase 2: git checkout main && git merge feature/phase-2-core-engine"
                echo "3. Tag release: git tag v2.0.0-phase2-complete"
                echo "4. Start Phase 3: git checkout -b feature/phase-3-advanced"
                echo "5. Update project-todo.md phase status"
                echo "6. Begin Phase 3 planning: cat planning/phase-3-advanced.md"
            else
                echo "Continue Phase 2 development:"
                echo "1. Check current tasks: cat planning/phase-2-core-engine.md"
                echo "2. Continue current branch: git checkout feature/phase-2-core-engine"
                echo "3. Focus on: Claude integration → Analysis workflows → Session management"
            fi
            ;;
        3)
            if check_phase_completion 3; then
                echo -e "${GREEN}🎉 Project Complete! Ready for production deployment!${NC}"
                echo "1. Final integration testing"
                echo "2. Merge Phase 3: git checkout main && git merge feature/phase-3-advanced"
                echo "3. Tag final release: git tag v3.0.0-production-ready"
                echo "4. Deploy to production environment"
                echo "5. Update documentation and examples"
            else
                echo "Continue Phase 3 development:"
                echo "1. Check current tasks: cat planning/phase-3-advanced.md"
                echo "2. Continue current branch: git checkout feature/phase-3-advanced"
                echo "3. Focus on: Multi-LLM support → Advanced analysis → Production deployment"
            fi
            ;;
        *)
            echo "Unknown phase. Check project-todo.md for current status."
            ;;
    esac
}

# Main execution
echo -e "\n${BLUE}📊 Phase Status Overview:${NC}"
check_phase_completion 1
check_phase_completion 2
check_phase_completion 3

current_phase=$(get_current_phase)
echo -e "\n${BLUE}🎯 Current Phase: ${YELLOW}Phase $current_phase${NC}"

suggest_next_actions $current_phase

echo -e "\n${BLUE}📝 Quick Context Commands:${NC}"
echo "- Read instructions: cat .ai-instructions.md | head -30"
echo "- Check progress: cat progress-tracker.md | tail -20"
echo "- View roadmap: cat project-todo.md | head -50"
echo "- Current phase plan: cat planning/phase-${current_phase}-*.md"

echo -e "\n${GREEN}🔄 Git Status:${NC}"
git status --short
git log --oneline -3

echo -e "\n=================================================="
echo -e "${GREEN}✅ Phase management check complete!${NC}"
