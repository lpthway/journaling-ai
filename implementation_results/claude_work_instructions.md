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
# 3. Create proper documentation in docs/ folder (see Documentation Requirements below)
# 4. Commit changes to git with descriptive message
git add .
git commit -m "Phase 5: Completed task [TASK_NAME] - Finalized feature and updated documentation"
echo "Committed final changes"
# 5. Merge the feature branch back to the main branch
git checkout main
git pull origin main
git merge $BRANCH_NAME --no-ff -m "Merging phase branch [$BRANCH_NAME] into main"
git push origin main
echo "Merged $BRANCH_NAME into main and pushed changes"
# 6. Update progress summary in implementation_todo.md
# 7. Log completion in session log
```

## Documentation Requirements (Critical - Do Not Skip)

### For Every Completed Task, Create:

> **Note**: If you have already completed tasks without documentation, see "Retroactive Documentation" section below.

#### 1. Task Implementation Documentation
Create folder: `docs/implementations/task-[TASK_ID]-[SHORT_NAME]/`

**Required Files:**
```bash
# Implementation Summary
docs/implementations/task-[TASK_ID]-[SHORT_NAME]/implementation-summary.md
```
**Content:**
- Task objective and success criteria
- Approach taken and why
- Challenges encountered and solutions
- Time invested vs. estimated
- Dependencies used or created

**Code Changes Documentation**
```bash
docs/implementations/task-[TASK_ID]-[SHORT_NAME]/code-changes.md
```
**Content:**
- List of all files modified/created
- Before/after code snippets for key changes
- Rationale for significant design decisions
- Performance or security implications

**Testing Documentation**
```bash
docs/implementations/task-[TASK_ID]-[SHORT_NAME]/testing-results.md
```
**Content:**
- Test cases created or modified
- Test execution results
- Edge cases covered
- Performance test results (if applicable)

#### 2. API Documentation (If Backend Changes)
Update or create: `docs/api/[FEATURE_NAME].md`

**Required Content:**
- New endpoint documentation with examples
- Request/response schemas
- Authentication requirements
- Error responses and codes
- Rate limiting information
- Usage examples with curl commands

#### 3. User Documentation (If Frontend Changes)
Update or create: `docs/user-guides/[FEATURE_NAME].md`

**Required Content:**
- How to use the new feature
- Screenshots or mockups
- Step-by-step instructions
- Common use cases
- Troubleshooting for user issues

#### 4. Architecture Documentation (If Structural Changes)
Update: `docs/architecture/[COMPONENT_NAME].md`

**Required Content:**
- Component diagram updates
- Data flow changes
- Database schema modifications
- Integration points with other components
- Security considerations

#### 5. Configuration Documentation (If Config Changes)
Update: `docs/setup/configuration.md`

**Required Content:**
- New environment variables
- Configuration file changes
- Default values and recommendations
- Migration steps for existing installations

### Documentation Templates

#### Implementation Summary Template:
```markdown
# Task [TASK_ID]: [TASK_NAME]

## Objective
[What was supposed to be accomplished]

## Approach
[How it was implemented and why this approach was chosen]

## Changes Made
### Files Modified:
- `path/to/file1.ext` - [Brief description of changes]
- `path/to/file2.ext` - [Brief description of changes]

### New Files Created:
- `path/to/newfile.ext` - [Purpose and functionality]

## Challenges & Solutions
[Any issues encountered and how they were resolved]

## Testing
[What was tested and results]

## Impact Analysis
### Performance Impact:
[Any performance considerations]

### Security Impact:
[Any security implications]

### Backward Compatibility:
[Impact on existing functionality]

## Time Investment
- Estimated: [X hours]
- Actual: [Y hours]
- Variance: [Analysis of difference]

## Future Considerations
[Any follow-up work or improvements needed]
```

#### API Documentation Template:
```markdown
# [FEATURE_NAME] API Documentation

## Endpoints

### [HTTP_METHOD] /api/[endpoint]
[Brief description of what this endpoint does]

#### Request
**Headers:**
```
Content-Type: application/json
Authorization: Bearer [token]
```

**Body:**
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

#### Response
**Success (200):**
```json
{
  "status": "success",
  "data": {
    "id": 123,
    "result": "value"
  }
}
```

**Error (400):**
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": ["field1 is required"]
}
```

#### Usage Example
```bash
curl -X POST https://api.example.com/api/endpoint \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-token" \
  -d '{"field1": "value1"}'
```
```

### Documentation Checklist for Each Task:

#### Before Marking Task Complete:
- [ ] Implementation summary created with all required sections
- [ ] Code changes documented with rationale
- [ ] Testing results documented
- [ ] API documentation updated (if backend changes)
- [ ] User guide updated (if frontend changes)
- [ ] Architecture docs updated (if structural changes)
- [ ] Configuration docs updated (if config changes)
- [ ] All documentation links work and formatting is correct
- [ ] Documentation reviewed for clarity and completeness

#### Quality Standards for Documentation:
- [ ] **Clear and Concise**: Easy to understand for other developers
- [ ] **Complete**: Covers all aspects of the implementation
- [ ] **Accurate**: Reflects actual implementation, not intended
- [ ] **Examples Included**: Real, working examples where applicable
- [ ] **Future-Focused**: Helps future maintenance and extension
- [ ] **Professional**: Properly formatted and proofread

## Retroactive Documentation (For Already Completed Tasks)

### When to Create Retroactive Documentation:
- At the start of any new session, check for completed tasks (✅) without documentation
- Before starting new development work
- When encountering undocumented code during maintenance
- As a dedicated documentation sprint

### Process for Retroactive Documentation:

#### 1. Identify Undocumented Completed Tasks
```bash
# Check implementation_todo.md for completed tasks (✅) without documentation
# Look for tasks marked COMPLETED but missing docs/implementations/task-[ID]/ folders
```

#### 2. Gather Information for Each Task
**From Git History:**
```bash
# Find commits related to the task
git log --oneline --grep="[TASK_ID]"
git log --oneline --since="[START_DATE]" --until="[END_DATE]"

# Check what files were changed
git show [COMMIT_HASH] --name-only
git diff [COMMIT_HASH]~1 [COMMIT_HASH]
```

**From Code Analysis:**
- Review the current state of affected files
- Identify the functionality that was implemented
- Understand the design decisions made

#### 3. Create Retroactive Documentation

**Simplified Template for Retroactive Documentation:**
```markdown
# Task [TASK_ID]: [TASK_NAME] (Retroactive Documentation)

## Objective
[What was accomplished - derived from task description and implementation]

## Implementation Analysis
[Analysis of what was actually implemented based on code review]

## Files Modified/Created
[List based on git history and current state]

## Functionality Added
[Description of the features/functionality that was implemented]

## Testing Status
[Current test coverage for this functionality]

## Architecture Impact
[How this change fits into the overall system]

## Usage
[How to use the implemented functionality]

## Notes
- This documentation was created retroactively
- Implementation completed on: [DATE]
- Documentation created on: [TODAY'S DATE]
```

#### 4. Prioritize Retroactive Documentation

**High Priority (Do First):**
- Tasks that affect public APIs
- Complex business logic implementations
- Security-related changes
- Database schema modifications

**Medium Priority:**
- UI/UX improvements
- Performance optimizations
- Refactoring tasks

**Low Priority:**
- Bug fixes with obvious solutions
- Simple configuration changes
- Cosmetic updates

#### 5. Retroactive Documentation Workflow
```bash
# For each undocumented completed task:

# 1. Create documentation folder
mkdir -p docs/implementations/task-[TASK_ID]-[SHORT_NAME]

# 2. Analyze git history
git log --oneline --grep="[TASK_ID]" > analysis.txt
git diff --name-only [RELEVANT_COMMITS] >> analysis.txt

# 3. Create implementation summary (use retroactive template)
# 4. Document key code changes with explanations
# 5. Note current testing status
# 6. Update relevant API/user/architecture docs

# 7. Commit retroactive documentation
git add docs/
git commit -m "Retroactive documentation for task [TASK_ID]: [TASK_NAME]

- Created implementation summary based on code analysis
- Documented functionality and usage
- Added to documentation system for future reference"
```

### Retroactive Documentation Checklist:

#### For Each Completed Task Without Documentation:
- [ ] Task implementation analyzed and understood
- [ ] Git history reviewed for changes
- [ ] Implementation summary created (retroactive template)
- [ ] Key functionality documented
- [ ] API changes documented (if applicable)
- [ ] User impact documented (if applicable)
- [ ] Testing status noted
- [ ] Documentation committed to git

#### Quality Standards for Retroactive Documentation:
- [ ] **Accurate**: Reflects actual implementation, not original intention
- [ ] **Honest**: Notes that documentation is retroactive
- [ ] **Useful**: Provides value for future maintenance
- [ ] **Complete**: Covers all significant aspects of the implementation

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
- [ ] Task-specific documentation created in docs/ folder
- [ ] User guides updated for new features
- [ ] Architecture diagrams updated if structure changed
- [ ] Troubleshooting guides created for complex features

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