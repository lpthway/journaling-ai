# Claude Work Instructions - Self-Management Prompt

## Core Purpose
This is your self-instruction prompt for `claude_work.sh`. Read this EVERY time you start working to understand where you are, what you've done, and what comes next.

## Current Status Check (Read First)

### 1. Where Am I?
**Check these files in order:**
1. `implementation_results/implementation_todo.md` - Current task status and progress
2. `implementation_results/implementation_progress.json` - Machine-readable progress data  
3. `implementation_results/current_session.md` - What you were last working on
4. Latest implementation log in `implementation_results/logs/` - Detailed work history

### 2. What Have I Done?
**Review completed items:**
- Count completed tasks in `implementation_todo.md` (look for ✅ status)
- Review recent implementation logs for context
- Check test results from previous sessions
- Verify any code changes were committed to git

### 3. What's Next?
**Priority decision logic:**
1. **If interrupted mid-task**: Continue the IN_PROGRESS (🔄) item
2. **If task failed**: Analyze failure and retry or escalate
3. **If priority level complete**: Move to next priority level
4. **If all tasks done**: Generate completion report

## Implementation Workflow (Follow This Process)

### Phase 1: Session Initialization
```bash
# 1. Update current session tracking
echo "Session started: $(date)" > implementation_results/current_session.md
echo "Working on: [TASK_ID] [TASK_NAME]" >> implementation_results/current_session.md

# 2. Create session log file  
SESSION_LOG="implementation_results/logs/session_$(date +%Y%m%d_%H%M%S).log"
echo "=== Claude Work Session Started ===" > $SESSION_LOG
echo "Time: $(date)" >> $SESSION_LOG

# 3. Set up virtual environment (always use venv from root directory)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# 4. Activate virtual environment
source venv/bin/activate
echo "Virtual environment activated."

# 5. Create a new branch for this session phase
BRANCH_NAME="phase-$(date +%Y%m%d_%H%M%S)"
git checkout -b $BRANCH_NAME
echo "New branch created: $BRANCH_NAME"
```

### Phase 2: Task Selection and Preparation
```bash
# 1. Find next pending task (⏳) in Priority 1, then 2, then 3, etc.
# 2. Update task status to IN_PROGRESS (🔄) in implementation_todo.md
# 3. Check dependencies are met
# 4. Review affected files and success criteria
# 5. Plan implementation approach
```

### Phase 3: Implementation Execution
```bash
# 1. Make code changes
# 2. Test changes immediately  
# 3. Log all actions in session log
# 4. If tests fail, fix and retry
# 5. If implementation fails, mark as FAILED (❌) and log reason
# 6. Commit changes if applicable
git add .
git commit -m "Phase 3: Implemented [TASK_NAME] - [Briefly describe what was done, e.g., added new feature or fixed issue]"
echo "Committed changes for phase 3"
```

### Phase 4: Testing and Validation
```bash
# 1. Run automated tests for changed functionality
# 2. Verify success criteria are met
# 3. Run broader test suite if changes are significant
# 4. Log all test results
# 5. Commit changes if tests pass
git add .
git commit -m "Phase 4: Completed unit tests for [TASK_NAME] - [Briefly describe what was validated, e.g., added tests for form fields]"
echo "Committed testing results"
```

### Phase 5: Completion and Documentation
```bash
# 1. Update task status to COMPLETED (✅) in implementation_todo.md
# 2. Add implementation notes and actual time spent
# 3. Commit changes to git with descriptive message
git add .
git commit -m "Phase 5: Completed task [TASK_NAME] - Finalized feature and updated documentation"
echo "Committed final changes"
# 4. Merge the feature branch back to the main branch
git checkout main
git pull origin main
git merge $BRANCH_NAME --no-ff -m "Merging phase branch [$BRANCH_NAME] into main"
git push origin main
echo "Merged $BRANCH_NAME into main and pushed changes"
# 5. Update progress summary in implementation_todo.md
# 6. Log completion in session log
```

## Self-Reflection Questions (Ask Yourself)

### Before Starting Each Task:
- [ ] Do I understand what this task is supposed to accomplish?
- [ ] Have I identified all the files I need to change?
- [ ] Do I know what success looks like?
- [ ] Are the dependencies for this task met?
- [ ] Do I have a clear implementation plan?

### During Implementation:
- [ ] Am I making progress toward the success criteria?
- [ ] Are my changes breaking existing functionality?
- [ ] Should I test intermediate steps?
- [ ] Do I need to update my approach?
- [ ] Am I logging my actions adequately?

### After Each Task:
- [ ] Did I achieve the success criteria?
- [ ] Do all tests pass?
- [ ] Are there any side effects I need to address?
- [ ] What did I learn that might help with future tasks?
- [ ] Should I update my approach for similar tasks?

## Error Handling and Recovery

### When Implementation Fails:
1. **Log the failure details** in session log
2. **Update task status to FAILED (❌)** with reason
3. **Analyze the root cause** - code issue, dependency problem, or approach error?
4. **Decide on retry strategy** - same approach or different approach?
5. **If stuck, escalate** by creating detailed issue report

### When Tests Fail:
1. **Don't mark task as complete**
2. **Investigate test failures** - are they related to your changes?
3. **Fix the underlying issue**, don't just make tests pass
4. **Re-run full test suite** to ensure no regressions
5. **Only proceed when all tests pass**

## Progress Tracking Requirements

### Must Update After Each Task:
1. **implementation_todo.md**: Task status, actual effort, implementation notes
2. **implementation_progress.json**: Machine-readable progress data
3. **Session log**: Detailed work performed
4. **Git commits**: Code changes with descriptive messages

### Daily Progress Summary:
At end of each work session, create summary:
```markdown
## Daily Progress - [DATE]
- **Tasks Completed**: X items
- **Time Invested**: X hours  
- **Priority Progress**: Priority X: Y/Z items complete
- **Blockers Encountered**: [List any issues]
- **Next Session Plan**: [What to work on next]
```

## Quality Standards

### Code Quality:
- [ ] Code follows existing project patterns
- [ ] No console.log statements in production code
- [ ] Proper error handling implemented
- [ ] Security best practices followed
- [ ] Performance implications considered

### Testing Requirements:
- [ ] All existing tests still pass
- [ ] New functionality has appropriate tests
- [ ] Edge cases are handled
- [ ] Security vulnerabilities are tested
- [ ] Performance hasn't degraded

### Documentation:
- [ ] Implementation notes are clear and detailed
- [ ] Code changes are well-commented
- [ ] API changes are documented
- [ ] Configuration changes are noted

## Emergency Procedures

### If System Becomes Unstable:
1. **Stop implementation immediately**
2. **Run full test suite** to identify scope of issues
3. **Check git status** and consider reverting recent changes
4. **Document the instability** in detail
5. **Focus on stability before continuing**

### If Quota/Time Limits Hit:
1. **Update current session status**
2. **Commit any working changes**  
3. **Update implementation_todo.md** with current progress
4. **Create detailed resume notes** for next session
5. **Log stopping point and next steps**

## Success Metrics

### Track These Metrics:
- **Task Completion Rate**: Completed vs. Total tasks
- **Time Accuracy**: Actual vs. Estimated hours
- **Test Pass Rate**: Percentage of tests passing
- **Rework Rate**: How often you need to redo tasks
- **Dependency Blocking**: How often dependencies block progress

### Quality Indicators:
- **Zero test regressions** after each task
- **Consistent git commit messages**
- **Detailed implementation notes**
- **Proactive error handling**
- **Security-first approach**

---

## Remember: You Are Building Production Software

This is not a prototype or experiment. Every change you make should be:
- **Production-ready quality**
- **Thoroughly tested**
- **Well-documented**
- **Security-conscious**
- **Performance-aware**

Take your time, do it right, and always verify your work before moving to the next task.

---

**Last Updated**: 2025-08-07
**Use this prompt every time you start a claude_work.sh session**