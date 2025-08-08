# Self-Instruction for Creating claude_work_vs_code.sh

## My Task
Create a new automation script `claude_work_vs_code.sh` that leverages the Claude Code VS Code extension instead of direct Claude CLI calls, based on the existing `claude_work.sh` architecture.

## My Approach

### Phase 1: Research & Setup
1. **Study Extension Documentation**
   - Research Claude Code extension API at docs.anthropic.com/en/docs/claude-code/overview
   - Understand available commands and integration points
   - Identify how to programmatically trigger extension features

2. **Analyze Current Script**
   - Map all functions in `claude_work.sh` to identify what needs vs code integration
   - Identify functions that can remain unchanged (git operations, file parsing, session management)
   - Document the critical integration points

### Phase 2: Core Architecture
1. **Create Base Script Structure**
   - Copy essential configuration and session management from original
   - Adapt paths and variables for VS Code extension workflow
   - Maintain compatibility with existing TODO files and progress tracking

2. **Design Extension Interface Layer**
   - Create wrapper functions for VS Code extension calls
   - Design context passing mechanisms (files, selections, tasks)
   - Plan error handling for extension interactions

### Phase 3: Implementation Engine
1. **Replace Claude CLI Integration**
   - Replace `run_claude_with_quota_monitoring()` with extension calls
   - Eliminate complex JSON streaming parsing
   - Use VS Code's command palette or extension API

2. **File Operation Strategy**
   - Use extension's tab awareness instead of manual file reading
   - Leverage automatic context from open files
   - Implement file opening/closing automation

### Phase 4: User Experience
1. **Visual Workflow Integration**
   - Use VS Code's diff viewer for change review
   - Implement confirmation dialogs in VS Code
   - Progress indicators in status bar or notifications

2. **Interactive Elements**
   - Keyboard shortcut integration (Alt+Cmd+K)
   - Selection-based context for targeted changes
   - Visual feedback for task progress

## Key Functions to Create

### Extension Interface Functions
```bash
# Core extension interaction
call_claude_extension_with_task()
open_task_files_in_vscode()
trigger_claude_with_selection()
confirm_changes_via_diff()

# Context management
prepare_task_context()
set_vscode_workspace()
select_relevant_code()

# UI integration
show_task_progress_in_vscode()
prompt_user_in_editor()
display_diff_for_review()
```

### Adapted Core Functions
```bash
# Keep but adapt these from original
initialize_session()
find_next_task()
update_task_status()
commit_changes()
handle_quota_exhausted()

# Simplify these significantly
vscode_implement_task()  # Much simpler than automated_implement_task
validate_via_diff()      # Replace complex validation logic
```

## Implementation Strategy

### Start Simple
1. Create minimal working version for one task type
2. Test extension integration with basic file operations
3. Verify diff viewing and confirmation workflow
4. Gradually add complexity

### Maintain Compatibility
- Keep same TODO file format and progress tracking
- Preserve git workflow and session management
- Maintain auto-resume functionality
- Support same command-line arguments

### Focus Areas
1. **Simplification**: Remove complex CLI parsing logic
2. **Visual Enhancement**: Better user feedback and confirmation
3. **Reliability**: More stable file operations via extension
4. **Usability**: Intuitive workflow with familiar VS Code interface

## Success Criteria for Each Function

### `vscode_implement_task()`
- Opens relevant files automatically in VS Code
- Triggers Claude extension with proper task context
- Shows visual diff of proposed changes
- Allows user confirmation before applying
- Integrates with git workflow

### Extension Integration
- Can programmatically call Claude Code extension
- Passes task description and file context effectively
- Receives and processes extension responses
- Handles errors gracefully with fallbacks

### User Experience
- Clear visual feedback on progress
- Intuitive confirmation workflows
- Better error messages with actionable guidance
- Seamless integration with existing VS Code workflow

## Error Handling Strategy
1. **Extension Availability**: Check if extension is installed and active
2. **Fallback Options**: Graceful degradation to manual mode
3. **Context Issues**: Handle cases where files aren't open or selected
4. **Permission Problems**: Better error messages for VS Code access issues

## Testing Plan
1. **Unit Testing**: Test each wrapper function individually
2. **Integration Testing**: Full task workflow from start to finish
3. **Edge Cases**: Error conditions, quota limits, file conflicts
4. **User Experience**: Actual usage with real implementation tasks

## Documentation Requirements
1. **Setup Instructions**: How to install and configure Claude Code extension
2. **Usage Guide**: How the new workflow differs from original script
3. **Troubleshooting**: Common issues and solutions
4. **Migration Guide**: When to use vs code version vs original

## My Next Actions
1. Research Claude Code extension documentation thoroughly
2. Create minimal prototype to test extension integration
3. Validate core assumptions about extension capabilities
4. Begin implementing based on findings from prototype
5. Test incrementally with real tasks from TODO list

## Key Decisions to Make
1. **Extension API**: How exactly to trigger Claude Code programmatically
2. **Context Passing**: Best way to provide task context to extension
3. **Confirmation Flow**: How to implement visual diff review and approval
4. **Error Recovery**: Fallback strategies when extension isn't available
5. **Performance**: Whether extension approach is faster/more reliable

## Success Metrics
- Reduced complexity compared to original script (fewer lines, simpler logic)
- Better user experience (visual feedback, intuitive workflow)
- Improved reliability (fewer validation false positives)
- Maintained functionality (all 21 tasks can still be automated)
- Enhanced debugging (visual diffs make issues obvious)
