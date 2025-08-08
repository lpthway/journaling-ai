# Phase 2: Task Selection & Analysis

## Your Tasks:
1. Identify task to work on
2. Create task folder structure
3. Initial analysis
4. Prepare implementation plan

## Analysis Protocol:
```bash
# 1. List available tasks
echo "Available tasks:" >> $SESSION_LOG
find implementation_results/tasks -name "*.md" -type f | sort >> $SESSION_LOG

# 2. Select task (use Read tool to examine task files)
# - Read task markdown files
# - Assess complexity and priority
# - Choose task to work on

# 3. Create task-specific folder
TASK_ID="[selected_task_id]"
mkdir -p implementation_results/active/$TASK_ID
echo "Working on task: $TASK_ID" >> $SESSION_LOG

# 4. Copy task file to active folder
cp implementation_results/tasks/$TASK_ID.md implementation_results/active/$TASK_ID/

# 5. Create initial analysis file
cat > implementation_results/active/$TASK_ID/analysis.md << 'EOF'
# Task Analysis: [TASK_NAME]

## Problem Understanding:
[Describe the task clearly]

## Technical Approach:
[High-level implementation strategy]

## Files to Modify:
[List specific files that need changes]

## Testing Strategy:
[How to verify the implementation works]

## Risks/Challenges:
[Potential issues to watch for]
EOF
```

## File Mapping Steps:
1. Use **Read** tool to understand task requirements
2. Use **LS** tool to explore relevant directories
3. Use **Read** tool to examine existing code structure
4. Document findings in analysis.md

## Success Criteria:
- [ ] Task selected and documented
- [ ] Analysis file created with technical approach
- [ ] Files to modify identified
- [ ] Ready for implementation planning
