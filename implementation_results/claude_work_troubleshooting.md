# Troubleshooting Guide

## Common Issues and Solutions

### Environment Issues

#### Virtual Environment Problems
**Problem:** Virtual environment not activating
```bash
# Solution 1: Verify venv exists and activate properly
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "Virtual env: $VIRTUAL_ENV"

# Solution 2: Check Python version and path
python3 --version
which python3
which python  # Should point to venv/bin/python when active

# Solution 3: Recreate if corrupted
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem:** Python commands not using virtual environment
```bash
# Solution: Always check and activate venv before Python commands
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Virtual environment not active - activating..."
    source venv/bin/activate
fi
# Verify correct Python is being used
which python
python --version
```

#### Dependency Issues
**Problem:** Package installation failures
```bash
# Solution: Update pip and try again
pip install --upgrade pip
pip install -r requirements.txt

# Alternative: Install packages individually
pip install [package_name]
```

### Documentation Issues

#### Duplicate Documentation Generation
**Problem:** System rebuilding docs for already completed tasks
```bash
# Solution: Check task status before documentation
if grep -q "Status: COMPLETED" implementation_results/tasks/$TASK_ID.md 2>/dev/null; then
    echo "Task already completed - skipping doc rebuild"
    exit 0
fi

# Force rebuild if needed
FORCE_REDOC=true ./claude_work.sh phase 5 "Force documentation rebuild"
```

#### Doc Folder Structure Missing
**Problem:** Documentation scattered across different locations
```bash
# Solution: Create proper docs structure
mkdir -p docs/tasks/
mkdir -p docs/implementations/$(date +%Y)/$(date +%m)/
mkdir -p docs/testing/$(date +%Y%m%d)/

# Verify structure
find docs/ -type d | sort
```

#### Missing Task Index
**Problem:** No central index of completed tasks
```bash
# Solution: Ensure task_index.md exists and is updated
if [ ! -f "docs/task_index.md" ]; then
    echo "Creating task index..."
    # Create from template (see claude_work_templates.md)
fi

# Add task to index
echo "- [$TASK_ID] $TASK_NAME - $(date) - [View Report](tasks/$TASK_ID/completion_report.md)" >> docs/task_index.md
```

#### Branch Creation Problems
**Problem:** Cannot create new branch
```bash
# Solution: Ensure clean working directory
git status
git add .
git commit -m "Cleanup before branch creation"
git checkout -b new-branch-name
```

#### Merge Conflicts
**Problem:** Conflicts when merging to main
```bash
# Solution: Resolve conflicts manually
git status  # See conflicted files
# Edit files to resolve conflicts
git add .
git commit -m "Resolve merge conflicts"
```

### Testing Issues

#### Tests Not Running
**Problem:** Test command fails
```bash
# Backend tests
cd backend
python -m pytest --version  # Check if pytest installed
pip install pytest  # Install if missing

# Frontend tests  
cd frontend
npm test -- --version  # Check if test runner available
npm install  # Install dependencies if missing
```

#### Test Failures
**Problem:** Tests fail after implementation
1. Check test output carefully
2. Verify changes don't break existing functionality
3. Update tests if requirements changed
4. Use debugging tools to investigate

### Code Implementation Issues

#### File Modification Problems
**Problem:** Cannot edit/write files
- Check file permissions
- Ensure correct file paths (absolute paths)
- Verify file exists before editing

#### Import/Module Errors
**Problem:** Python import errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify module structure
find . -name "__init__.py"

# Install missing packages
pip install [missing_package]
```

### Task Management Issues

#### Task Not Found
**Problem:** Cannot find task files
```bash
# List available tasks
find implementation_results/tasks -name "*.md" -type f

# Check task directory structure
ls -la implementation_results/tasks/
```

#### Session Tracking Problems
**Problem:** Session files missing or corrupted
```bash
# Recreate session tracking
mkdir -p implementation_results/logs
echo "Session restarted: $(date)" > implementation_results/current_session.md
```

## Debugging Commands

### System Information
```bash
# Check system resources
df -h  # Disk space
free -h  # Memory usage
ps aux | grep python  # Running Python processes

# Check network connectivity
ping -c 4 8.8.8.8
curl -I https://github.com
```

### Project State
```bash
# Check git status
git status
git log --oneline -10

# Check file structure
find . -type f -name "*.py" | head -20
find . -type f -name "*.js" | head -20

# Check running processes
lsof -i :3000  # Frontend port
lsof -i :8000  # Backend port
```

### Log Analysis
```bash
# Check recent logs
tail -50 implementation_results/logs/session_*.log

# Search for errors
grep -i error implementation_results/logs/*.log
grep -i failed implementation_results/logs/*.log
```

## Recovery Procedures

### Full Environment Reset
```bash
# 1. Backup current work
git add .
git commit -m "Backup before reset"

# 2. Reset virtual environment
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Verify git state
git status
git branch -a
```

### Session Recovery
```bash
# 1. Find last working state
git log --oneline -10

# 2. Checkout to known good state if needed
git checkout [commit_hash]

# 3. Restart session
source venv/bin/activate
echo "Recovery session: $(date)" > implementation_results/current_session.md
```

## Prevention Tips

1. **Always commit before major changes**
2. **Test incrementally, not all at once**
3. **Keep implementation steps small**
4. **Document issues as they occur**
5. **Verify environment setup before starting**
