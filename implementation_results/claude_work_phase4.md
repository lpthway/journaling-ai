# Phase 4: Code Implementation

## Your Tasks:
1. Execute implementation plan
2. Make code changes systematically
3. Test each change
4. Document progress

## Implementation Protocol:
```bash
# 1. Start implementation log
cat > implementation_results/active/$TASK_ID/implementation_log.md << 'EOF'
# Implementation Log: [TASK_NAME]

## Changes Made:
### [Timestamp] - [File Name]
- Change: [Description]
- Reason: [Why this change was needed]
- Testing: [How tested]
- Status: [Success/Failed/Pending]

EOF

# 2. Create backup before changes
git add .
git commit -m "Backup before implementing $TASK_ID"
echo "Backup commit created" >> $SESSION_LOG
```

## Implementation Steps:
1. **Follow your implementation plan exactly**
2. **Make one change at a time**
3. **Test after each significant change**
4. **Document each change in implementation_log.md**

## Code Modification Guidelines:
- Use **Write** tool for new files
- Use **Edit** tool for modifying existing files
- Maintain consistent code style
- Add comments for complex logic
- Follow existing patterns

## Testing After Changes:
```bash
# Test the implementation
cd [relevant_directory]
[run appropriate tests based on task]

# Log test results
echo "Test results for [change]:" >> implementation_results/active/$TASK_ID/implementation_log.md
echo "[test output or description]" >> implementation_results/active/$TASK_ID/implementation_log.md
```

## Progress Tracking:
Update implementation_log.md after each file modification:
- What was changed
- Why it was changed  
- How it was tested
- Current status

## Success Criteria:
- [ ] All planned changes implemented
- [ ] Each change tested and working
- [ ] Implementation log updated
- [ ] Code follows project patterns
