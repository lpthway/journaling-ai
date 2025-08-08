# Documentation Templates

## Task Template
```markdown
# Task: [TASK_NAME]

## Status: [PENDING/IN_PROGRESS/COMPLETED]

## Priority: [HIGH/MEDIUM/LOW]

## Description:
[Clear description of what needs to be done]

## Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes:
[Any technical considerations or constraints]

## Files Likely to be Modified:
- [file1]: [reason]
- [file2]: [reason]

## Testing Requirements:
[How to verify the task is complete]

## Dependencies:
[Any other tasks or systems this depends on]
```

## Analysis Template
```markdown
# Analysis: [TASK_NAME]

## Problem Understanding:
[What problem are we solving?]

## Current State:
[How does the system currently work?]

## Desired State:
[How should it work after changes?]

## Technical Approach:
[High-level implementation strategy]

## Risk Assessment:
### Low Risk:
- [item]

### Medium Risk:
- [item]

### High Risk:
- [item]

## Time Estimate:
[Rough estimate of implementation time]
```

## Implementation Plan Template
```markdown
# Implementation Plan: [TASK_NAME]

## Overview:
[Brief summary of the implementation approach]

## Step-by-Step Implementation:

### Step 1: [Title]
**Objective:** [What this step accomplishes]
**Files to modify:**
- [file]: [specific changes]
**Testing:** [How to verify this step]
**Dependencies:** [What must be done first]

### Step 2: [Title]
[Same format as Step 1]

## Integration Points:
[How this connects with existing systems]

## Rollback Strategy:
[How to undo changes if needed]

## Quality Gates:
- [ ] Code follows project standards
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
```

## Test Results Template
```markdown
# Test Results: [TASK_NAME]

## Test Summary:
- **Total Tests:** [number]
- **Passed:** [number] 
- **Failed:** [number]
- **Skipped:** [number]

## Test Categories:

### Unit Tests:
[Results and details]

### Integration Tests:
[Results and details]

### Manual Testing:
[What was tested manually and results]

## Failed Tests:
[Details of any failures and remediation]

## Performance Impact:
[Any performance changes observed]
```
