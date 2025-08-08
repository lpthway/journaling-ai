# Phase 3: Implementation Planning

## Your Tasks:
1. Detailed code examination
2. Create implementation plan
3. Break down into steps
4. Prepare for execution

## Implementation Planning Protocol:
```bash
# 1. Create detailed plan file
cat > implementation_results/active/$TASK_ID/implementation_plan.md << 'EOF'
# Implementation Plan: [TASK_NAME]

## Current State Analysis:
[Document current code state]

## Step-by-Step Implementation:
### Step 1: [Description]
- Files to modify: [list]
- Changes needed: [specific changes]
- Testing approach: [how to test]

### Step 2: [Description]
- Files to modify: [list]
- Changes needed: [specific changes]
- Testing approach: [how to test]

[Continue for all steps...]

## Dependencies & Order:
[List implementation order and dependencies]

## Rollback Plan:
[How to undo changes if something goes wrong]
EOF

# 2. Log the plan
echo "Implementation plan created for $TASK_ID" >> $SESSION_LOG
echo "Plan location: implementation_results/active/$TASK_ID/implementation_plan.md" >> $SESSION_LOG
```

## Code Analysis Steps:
1. Use **Read** tool to examine each file that needs modification
2. Understand current code structure and patterns
3. Identify integration points and dependencies
4. Plan changes that maintain code quality
5. Consider backward compatibility

## Quality Checks:
- [ ] Implementation maintains existing patterns
- [ ] Changes are minimal and focused
- [ ] No breaking changes unless necessary
- [ ] Clear testing strategy defined

## Success Criteria:
- [ ] Detailed implementation plan created
- [ ] All files to modify have been examined
- [ ] Step-by-step approach documented
- [ ] Ready for code implementation
