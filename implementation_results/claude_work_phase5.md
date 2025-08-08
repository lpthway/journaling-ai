# Phase 5: Testing & Documentation

## Your Tasks:
1. Comprehensive testing
2. Create task completion documentation
3. Commit and merge changes
4. Update task status

## Testing Protocol:
```bash
# 1. Ensure virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# 2. Run comprehensive tests
echo "=== Final Testing Phase ===" >> $SESSION_LOG

# Backend tests (if applicable)
if [ -d "backend" ]; then
    cd backend
    source ../venv/bin/activate  # Ensure venv is active
    python -m pytest tests/ -v >> ../implementation_results/active/$TASK_ID/test_results.txt 2>&1
    cd ..
fi

# Frontend tests (if applicable)
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    cd frontend
    npm test >> ../implementation_results/active/$TASK_ID/test_results.txt 2>&1
    cd ..
fi

# Integration tests (if applicable)
if [ -f "test_integration.py" ]; then
    source venv/bin/activate  # Ensure venv is active
    python test_integration.py >> implementation_results/active/$TASK_ID/test_results.txt 2>&1
fi

# 3. Document test results
echo "Test results logged to: implementation_results/active/$TASK_ID/test_results.txt" >> $SESSION_LOG
```

## Documentation Creation:
```bash
# 1. Check if task is already completed (skip doc rebuilding)
if grep -q "Status: COMPLETED" implementation_results/tasks/$TASK_ID.md 2>/dev/null; then
    echo "Task $TASK_ID already completed - skipping documentation rebuild" >> $SESSION_LOG
    echo "Use 'force-redoc' flag to override this behavior" >> $SESSION_LOG
    return 0
fi

# 2. Create proper docs folder structure
mkdir -p docs/tasks/$TASK_ID
mkdir -p docs/implementations/$(date +%Y)/$(date +%m)
mkdir -p docs/testing/$(date +%Y%m%d)

# 3. Create completion documentation in proper docs structure
cat > docs/tasks/$TASK_ID/completion_report.md << 'EOF'
# Task Completion Report: [TASK_NAME]

**Task ID:** $TASK_ID  
**Completion Date:** $(date)  
**Session:** $BRANCH_NAME  

## Task Summary:
[Brief description of what was accomplished]

## Implementation Details:
### Files Modified:
- [file1]: [description of changes]
- [file2]: [description of changes]

### Key Changes:
1. [Change 1]: [Description and impact]
2. [Change 2]: [Description and impact]

## Testing Results:
[Summary of test results - see docs/testing/$(date +%Y%m%d)/$TASK_ID/ for detailed results]

## Known Issues:
[Any remaining issues or limitations]

## Usage Instructions:
[How to use the new functionality]

## Future Improvements:
[Suggestions for future enhancements]

## References:
- Implementation details: docs/implementations/$(date +%Y)/$(date +%m)/$TASK_ID/
- Test results: docs/testing/$(date +%Y%m%d)/$TASK_ID/
- Code changes: See git commit history for session $BRANCH_NAME
EOF

# 4. Copy implementation details to docs structure
cp -r implementation_results/active/$TASK_ID/* docs/implementations/$(date +%Y)/$(date +%m)/$TASK_ID/ 2>/dev/null || true

# 5. Copy test results to docs structure  
mkdir -p docs/testing/$(date +%Y%m%d)/$TASK_ID/
cp implementation_results/active/$TASK_ID/test_results.txt docs/testing/$(date +%Y%m%d)/$TASK_ID/ 2>/dev/null || true

# 6. Create cross-references in main docs
echo "- [$TASK_ID] [TASK_NAME] - $(date) - [View Report](tasks/$TASK_ID/completion_report.md)" >> docs/task_index.md

# 7. Legacy compatibility - keep copy in implementation_results
cp docs/tasks/$TASK_ID/completion_report.md implementation_results/active/$TASK_ID/completion_report.md

# 2. Update task status
echo "Status: COMPLETED" >> implementation_results/tasks/$TASK_ID.md
echo "Completion Date: $(date)" >> implementation_results/tasks/$TASK_ID.md
echo "Session: $BRANCH_NAME" >> implementation_results/tasks/$TASK_ID.md
```

## Git Workflow:
```bash
# 1. Stage all changes
git add .

# 2. Commit with detailed message
git commit -m "Implement $TASK_ID: [TASK_NAME]

- [Brief summary of changes]
- Files modified: [list key files]
- Testing: [test status]
- Resolves: [any issue references]"

# 3. Switch to main and merge
git checkout main
git merge $BRANCH_NAME

# 4. Clean up branch
git branch -d $BRANCH_NAME

# 5. Update session tracking
echo "Task $TASK_ID completed successfully" >> implementation_results/current_session.md
echo "Session ended: $(date)" >> implementation_results/current_session.md
```

## Final Verification:
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Changes committed and merged
- [ ] Task marked as completed
- [ ] Session properly closed

## Success Criteria:
- [ ] Comprehensive testing completed
- [ ] Completion report created
- [ ] Code committed to main branch
- [ ] Task status updated to COMPLETED
