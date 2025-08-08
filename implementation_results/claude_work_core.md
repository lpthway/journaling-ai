# Claude Work Core Instructions

## Status Check (Read First)
1. Check `implementation_results/implementation_todo.md` - Current task status
2. Check `implementation_results/current_session.md` - Last work done
3. Check `implementation_results/implementation_progress.json` - Progress data

## What's Next Logic:
- **IN_PROGRESS (🔄)**: Continue interrupted task
- **FAILED (❌)**: Analyze and retry
- **Priority complete**: Move to next priority
- **All done**: Generate completion report

## Critical Rules:
1. **ALWAYS activate venv before Python commands**: `source venv/bin/activate`
2. **Check task completion status**: Skip completed tasks unless forced
3. **Use proper docs structure**: Store docs in `/docs/` with organized folders
4. **Test after each change**: Validate syntax and functionality
5. **Document systematically**: Update task index and create completion reports
6. **Follow git workflow**: Branch → Implement → Test → Merge
7. **Use exact tool names**: Write, Edit, Read, LS, Bash, Grep, Glob only

## 5-Phase Workflow:
1. **Session Init** → Set up environment, branch, tracking
2. **Task Prep** → Select task, update status, plan approach  
3. **Implementation** → Code changes, immediate testing
4. **Testing** → Full validation, fix issues
5. **Documentation** → Create docs, commit, merge

## Quality Gates (Must Pass):
- [ ] All tests pass
- [ ] Documentation complete and professional
- [ ] Code follows existing patterns
- [ ] Security implications considered
- [ ] Git commits descriptive and atomic

## File Updates Required Each Task:
- `implementation_todo.md` - Task status and notes
- `implementation_progress.json` - Machine-readable progress
- Session log - Detailed work history
- Git commits - Code changes with messages

## Templates Available:
- Implementation Summary Template
- API Documentation Template  
- Retroactive Documentation Template
- See phase-specific instructions for details

---
**Remember**: Production software - thoroughly tested, well-documented, security-conscious
