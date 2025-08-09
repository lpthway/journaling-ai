# Git Workflow Guide

## Simplified Branch Strategy

### Overview
The `claude_work.sh` script now follows a simplified, consistent git workflow designed to maintain a clean repository while supporting collaborative development.

### Key Principles
1. **Single Source of Truth**: All work merges into `main` branch
2. **Temporary Session Branches**: Each work session creates a temporary branch that gets cleaned up
3. **Automatic Cleanup**: Old and completed session branches are automatically removed
4. **Consistent Starting Point**: All sessions start from the latest `main` branch

### Workflow Steps

#### 1. Session Initialization
```bash
./claude_work.sh work
```
- Automatically switches to `main` branch
- Fetches and pulls latest changes
- Offers to clean up old session branches (>7 days)
- Creates new session branch: `phase-YYYYMMDD_HHMMSS`

#### 2. Development Work
- All work happens on the session branch
- Commits are made throughout the session
- Changes are isolated from `main` until completion

#### 3. Session Completion
- Work is merged back to `main` with `--no-ff` (preserves branch history)
- Session branch is automatically deleted locally
- If session branch was pushed, it's also deleted from remote
- Changes are pushed to `origin/main`

### Branch Naming Convention
- **Session branches**: `phase-YYYYMMDD_HHMMSS` (e.g., `phase-20250809_115616`)
- **Main branch**: `main` (always the target for merges)

### Automatic Cleanup Features

#### Session Branch Cleanup
- ✅ Automatic deletion after successful merge
- ✅ Local and remote cleanup
- ✅ Preserves merge history in `main`

#### Old Branch Cleanup  
- 🧹 Offers to delete local session branches older than 7 days
- 🧹 Identifies orphaned remote session branches
- 🧹 Interactive prompts for user confirmation

#### Repository Maintenance
- 🔄 Always starts from latest `main`
- 🔄 Fetches remote changes before work
- 🔄 Maintains clean branch structure

### Manual Commands (if needed)

#### Resume a specific session
```bash
# List available sessions
./claude_work.sh sessions

# Resume a specific session by ID
WORK_SESSION_ID=20250809_120500 ./claude_work.sh work

# Or run resume scripts (if available)
./implementation_results/work_resume_20250809_120500.sh
```

#### Clean up a specific session branch
```bash
git branch -d phase-YYYYMMDD_HHMMSS
git push origin --delete phase-YYYYMMDD_HHMMSS
```

#### View merge history
```bash
git log --oneline --graph --decorate
```

#### List all session branches
```bash
git branch -a | grep phase-
```

### Session Management

#### Interrupted Session Recovery
If your session gets interrupted (quota exhausted, connection lost, etc.):

1. **Check available sessions**: `./claude_work.sh sessions`
2. **Resume by session ID**: `WORK_SESSION_ID=YYYYMMDD_HHMMSS ./claude_work.sh work`
3. **Use resume scripts**: `./implementation_results/work_resume_*.sh` (automatic timing)

#### Session Resume Logic
- **Environment Variable**: `WORK_SESSION_ID=YYYYMMDD_HHMMSS` forces resume of specific session
- **Automatic Detection**: If already on a `phase-*` branch, continues that session
- **Branch Verification**: Checks if session branch exists before attempting switch
- **Smart Switching**: Automatically switches to existing session branch when resuming

#### Session States
- **New Session**: Creates `phase-YYYYMMDD_HHMMSS` from main
- **Active Session**: Working on existing session branch
- **Interrupted Session**: Session branch exists but not currently active
- **Completed Session**: Work merged to main, session branch cleaned up

### Benefits

1. **Simplified Mental Model**: Always work from main, merge back to main
2. **Clean Repository**: No accumulation of stale branches
3. **Collaboration Friendly**: Clear merge points and history
4. **Automated Maintenance**: Reduces manual branch management overhead
5. **Consistent Workflow**: Same process regardless of project phase

### Troubleshooting

#### If merge conflicts occur:
```bash
git checkout main
git pull origin main
git merge phase-YYYYMMDD_HHMMSS
# Resolve conflicts manually
git commit
git push origin main
git branch -d phase-YYYYMMDD_HHMMSS
```

#### If you need to abandon a session:
```bash
git checkout main
git branch -D phase-YYYYMMDD_HHMMSS  # Force delete if needed
```

#### If remote cleanup fails:
```bash
git push origin --delete phase-YYYYMMDD_HHMMSS
# Or use GitHub web interface to delete the branch
```

### Migration from Old Workflow

The old workflow created various types of branches (`claude-working`, inconsistent phase branches, etc.). This has been simplified to only use temporary session branches that merge to `main`.

All existing work has been preserved on the `main` branch, and obsolete branches have been cleaned up.
