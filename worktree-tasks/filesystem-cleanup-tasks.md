# File System Cleanup & Organization Worktree Tasks
**Branch**: feature/filesystem-cleanup
**Ports**: Backend(8021), Dashboard(5192), MCP(9889), Coordinator(8900)

## 🚨 CRITICAL: 2025 Organization Standards

**MANDATORY**: Follow the documented repository structure from CLAUDE.md!

**Requirements**:
- ✅ Follow documented directory structure exactly
- ✅ Remove ALL temporary and partial files
- ✅ Archive outdated files properly
- ✅ Eliminate duplicate content
- ✅ Auto-accept enabled for corrections
- ❌ NO data loss - archive before deleting

## Primary Objectives

### 1. **Root Directory Cleanup**
   - Remove misplaced scripts and files from root
   - Keep only essential configuration files
   - Move development scripts to proper locations
   - Clean up outdated markdown files

### 2. **Documentation Organization**
   - Consolidate duplicate documentation
   - Remove outdated guides
   - Organize by documentation categories
   - Archive historical documentation

### 3. **File System Standardization**
   - Enforce documented directory structure
   - Remove temporary and backup files
   - Clean up cache and build artifacts
   - Standardize naming conventions

## Current State Analysis

### Root Directory Issues Identified
- **10+ markdown files** in root (should be in docs/)
- **Multiple shell scripts** misplaced in root
- **Session scripts** (`session-*.sh`) should be in scripts/
- **Worktree scripts** scattered in root
- **Temp files** (`.tmp`, `.bak`, `~`)

### Documented Directory Structure (from CLAUDE.md)
```
Root Directory Files (Essential Only):
- package.json, package-lock.json  # NPM workspace config
- pyproject.toml                   # Python project config
- requirements.txt                 # Python dependencies
- Makefile                        # Build automation
- .env, .env.example              # Environment variables
- pytest.ini                      # Test configuration
- render.yaml                     # Deployment config
- .gitignore                      # Git exclusions
- README.md                       # Main documentation
- CLAUDE.md                       # AI guidance
- .nvmrc                          # Node version
- .python-version                 # Python version

Directory Structure:
├── apps/              # Applications (backend, dashboard)
├── core/              # AI agents, MCP, coordinators
├── database/          # Models, migrations, services
├── roblox/            # Roblox-related code
├── scripts/           # All scripts organized
│   ├── maintenance/   # Maintenance scripts
│   └── testing/       # Test runners
├── config/            # Configuration files
│   └── env-templates/ # Environment templates
├── tests/             # All test files
├── docs/              # All documentation
├── infrastructure/    # Docker, K8s configs
├── toolboxai_settings/ # Settings module
├── toolboxai_utils/   # Utilities
└── venv/              # Virtual environment
```

## Current Tasks

### Phase 1: Root Directory Cleanup (Priority: CRITICAL)

**Files to Remove from Root:**
- [ ] `ALL_NEXT_STEPS_COMPLETE.md` → Move to Archive/
- [ ] `COMPLETE_USAGE_GUIDE.md` → Move to Archive/
- [ ] `GIT_WORKTREES_README.md` → Move to docs/development/
- [ ] `INTERACTIVE_SESSIONS_READY.md` → Move to Archive/
- [ ] `QUICK_TERMINAL_REFERENCE.md` → Move to Archive/
- [ ] `SETUP_COMPLETE.md` → Move to Archive/
- [ ] `TERMINAL_SESSIONS_COMPLETE.md` → Move to Archive/
- [ ] `TERMINAL_USAGE_GUIDE.md` → Move to Archive/
- [ ] `WORKTREE_AGENT_STATUS.md` → Move to docs/development/
- [ ] `check-sessions-status.sh` → Move to scripts/development/
- [ ] `run-all-worktrees.sh` → Move to scripts/development/
- [ ] `start-all-claude-sessions.sh` → Move to scripts/development/
- [ ] `start-all-sessions.sh` → Move to scripts/development/
- [ ] `start-all-worktree-sessions.sh` → Move to scripts/development/
- [ ] `start-interactive-sessions.sh` → Move to scripts/development/
- [ ] `test-interactive-sessions.sh` → Move to scripts/testing/
- [ ] `session-*.sh` (6 files) → Move to scripts/development/worktrees/
- [ ] `fix-imports.sh` → Move to scripts/maintenance/

**Files to Keep in Root:**
- ✅ `CLAUDE.md` - AI guidance (essential)
- ✅ `README.md` - Main documentation (essential)
- ✅ `TODO.md` - Production roadmap (essential)
- ✅ `package.json`, `package-lock.json` - NPM config (essential)
- ✅ `pyproject.toml`, `requirements.txt` - Python config (essential)
- ✅ `Makefile`, `pytest.ini` - Build/test config (essential)
- ✅ `.env.example`, `.gitignore` - Config files (essential)
- ✅ `.nvmrc`, `.python-version` - Version files (essential)

### Phase 2: Script Organization (Priority: HIGH)

**Create Directory Structure:**
- [ ] Create `scripts/development/` for development scripts
- [ ] Create `scripts/development/worktrees/` for worktree scripts
- [ ] Create `scripts/deployment/` for deployment scripts
- [ ] Create `scripts/database/` for database scripts
- [ ] Create `scripts/docker/` for Docker scripts

**Move Scripts:**
```bash
# Worktree scripts
scripts/development/worktrees/
├── session-backend.sh
├── session-bugfixes.sh
├── session-database-dev.sh
├── session-documentation.sh
├── session-experimental.sh
├── session-frontend-dashboard.sh
├── session-main.sh
├── session-roblox.sh
├── start-all-worktree-sessions.sh
├── start-all-sessions.sh
├── start-interactive-sessions.sh
├── test-interactive-sessions.sh
├── check-sessions-status.sh
└── run-all-worktrees.sh

# Maintenance scripts
scripts/maintenance/
└── fix-imports.sh
```

### Phase 3: Documentation Consolidation (Priority: HIGH)

**Move Documentation Files:**
- [ ] `WORKTREE_AGENT_STATUS.md` → `docs/development/worktree-agents/STATUS.md`
- [ ] `GIT_WORKTREES_README.md` → `docs/development/GIT_WORKTREES.md`
- [ ] All `*_COMPLETE.md` files → `Archive/2025-10-02/completion-reports/`
- [ ] All `*_USAGE_GUIDE.md` files → `Archive/2025-10-02/guides/`

**Documentation Structure:**
```
docs/
├── development/
│   ├── worktree-agents/
│   │   ├── STATUS.md
│   │   └── COORDINATION.md
│   ├── GIT_WORKTREES.md
│   └── DEVELOPMENT_SETUP.md
├── deployment/
├── api/
└── guides/
```

### Phase 4: Archive Old Files (Priority: MEDIUM)

**Archive Location:** `Archive/2025-10-02/`

**Files to Archive:**
- [ ] All completion status files (`*_COMPLETE.md`)
- [ ] All usage guides (`*_USAGE_GUIDE.md`)
- [ ] Old terminal session documentation
- [ ] Interactive session guides
- [ ] Setup completion reports

**Archive Structure:**
```
Archive/2025-10-02/
├── completion-reports/
│   ├── ALL_NEXT_STEPS_COMPLETE.md
│   ├── INTERACTIVE_SESSIONS_READY.md
│   ├── SETUP_COMPLETE.md
│   └── TERMINAL_SESSIONS_COMPLETE.md
├── guides/
│   ├── COMPLETE_USAGE_GUIDE.md
│   ├── QUICK_TERMINAL_REFERENCE.md
│   └── TERMINAL_USAGE_GUIDE.md
└── README.md (explain what's archived)
```

### Phase 5: Temporary File Cleanup (Priority: HIGH)

**Find and Remove:**
- [ ] `.tmp` files
- [ ] `.bak` backup files
- [ ] `~` editor backups
- [ ] `.DS_Store` macOS files
- [ ] `__pycache__/` directories
- [ ] `.pyc` compiled Python files
- [ ] `node_modules/.cache/` directories
- [ ] Build artifacts in wrong locations

**Safe Cleanup Commands:**
```bash
# Find temporary files
find . -name "*.tmp" -type f
find . -name "*.bak" -type f
find . -name "*~" -type f
find . -name ".DS_Store" -type f

# Find Python cache
find . -name "__pycache__" -type d
find . -name "*.pyc" -type f

# Review before deleting!
```

### Phase 6: Duplicate File Detection (Priority: MEDIUM)

**Check for Duplicates:**
- [ ] Duplicate documentation files
- [ ] Duplicate configuration files
- [ ] Duplicate scripts (different locations)
- [ ] Duplicate test files

**Tools:**
```bash
# Find duplicate files by size
find . -type f -exec md5 {} \; | sort | uniq -D -w 32

# Find duplicate file names
find . -type f -printf '%f\n' | sort | uniq -d
```

### Phase 7: Naming Convention Standardization (Priority: LOW)

**File Naming Rules:**
- Use kebab-case for files: `file-name.ext`
- Use snake_case for Python: `module_name.py`
- Use PascalCase for components: `ComponentName.tsx`
- Prefix test files: `test_*.py`, `*.test.ts`

**Files to Rename:**
- [ ] Inconsistent script names
- [ ] Mixed case documentation files
- [ ] Non-standard test file names

### Phase 8: Git Worktrees Cleanup (Priority: MEDIUM)

**Worktree Organization:**
- [ ] Remove completed worktrees (experimental, documentation, bugfixes)
- [ ] Verify worktree paths in `.git/worktrees/`
- [ ] Clean up worktree configuration
- [ ] Update `.git-worktrees-config` if needed

**Commands:**
```bash
# List current worktrees
git worktree list

# Remove completed worktrees
git worktree remove parallel-worktrees/experimental
git worktree remove parallel-worktrees/documentation
git worktree remove parallel-worktrees/bugfixes

# Prune deleted worktrees
git worktree prune
```

### Phase 9: Permission and Ownership Audit (Priority: LOW)

**Check Permissions:**
- [ ] Ensure scripts are executable (`chmod +x`)
- [ ] Verify no world-writable files
- [ ] Check ownership consistency
- [ ] Validate `.gitignore` patterns

**Fix Permissions:**
```bash
# Make scripts executable
find scripts/ -name "*.sh" -exec chmod +x {} \;

# Find world-writable files (security issue)
find . -type f -perm -002

# Find files owned by wrong user
find . ! -user $(whoami)
```

### Phase 10: Size Optimization (Priority: MEDIUM)

**Target Areas:**
- [ ] Remove large unused dependencies
- [ ] Clean npm/pip caches
- [ ] Remove old Docker images/volumes
- [ ] Compress large binary files
- [ ] Archive old logs

**Size Analysis:**
```bash
# Find largest directories
du -sh */ | sort -h | tail -20

# Find largest files
find . -type f -size +10M -exec ls -lh {} \; | sort -k5 -h

# Analyze node_modules size
du -sh node_modules
du -sh apps/dashboard/node_modules

# Clean caches
npm cache clean --force
pip cache purge
```

### Phase 11: .gitignore Validation (Priority: MEDIUM)

**Ensure Ignored:**
- [ ] All `__pycache__/` directories
- [ ] All `.pyc` files
- [ ] All `node_modules/` directories
- [ ] All `.env` files (except `.env.example`)
- [ ] All build artifacts (`dist/`, `build/`)
- [ ] All coverage reports
- [ ] All log files
- [ ] All `.DS_Store` files
- [ ] All editor configs (`.vscode/`, `.idea/`)

**Update .gitignore:**
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/

# Node
node_modules/
npm-debug.log*
.npm/

# Build artifacts
dist/
build/
*.egg-info/

# Environment
.env
.env.local
!.env.example

# OS
.DS_Store
Thumbs.db

# Editors
.vscode/
.idea/
*.swp
*~

# Temporary
*.tmp
*.bak
.cache/

# Coverage
coverage/
.coverage
htmlcov/
```

### Phase 12: Documentation Generation (Priority: LOW)

**Create Missing Docs:**
- [ ] `docs/development/DIRECTORY_STRUCTURE.md` - Explain organization
- [ ] `docs/development/FILE_NAMING.md` - Naming conventions
- [ ] `scripts/README.md` - Script documentation
- [ ] `Archive/README.md` - Archive explanation

**Update Existing Docs:**
- [ ] Update CLAUDE.md with cleaned structure
- [ ] Update README.md to reflect organization
- [ ] Update TODO.md with cleanup completion

## File Locations

### Scripts Directory
- **Development**: `scripts/development/`
- **Worktrees**: `scripts/development/worktrees/`
- **Maintenance**: `scripts/maintenance/`
- **Testing**: `scripts/testing/`
- **Database**: `scripts/database/`
- **Docker**: `scripts/docker/`
- **Deployment**: `scripts/deployment/`

### Documentation
- **Development Guides**: `docs/development/`
- **Deployment Guides**: `docs/deployment/`
- **API Docs**: `docs/api/`
- **Archived Docs**: `Archive/2025-10-02/`

### Archive
- **Location**: `Archive/2025-10-02/`
- **Categories**: completion-reports, guides, old-configs

## Tools and Commands

### Analysis Tools
```bash
# Disk usage analysis
du -sh * | sort -h

# Find large files
find . -size +10M -ls

# Count files by type
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -n

# Find empty directories
find . -type d -empty

# Find duplicate files
fdupes -r .
```

### Cleanup Commands
```bash
# Remove temporary files (CAREFUL!)
find . -name "*.tmp" -delete
find . -name "*.bak" -delete
find . -name "*~" -delete
find . -name ".DS_Store" -delete

# Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Clean npm cache
npm cache clean --force

# Clean Docker (if needed)
docker system prune -a --volumes
```

### Organization Commands
```bash
# Create directory structure
mkdir -p scripts/{development/worktrees,maintenance,testing,database,docker,deployment}
mkdir -p docs/{development/worktree-agents,deployment,guides}
mkdir -p Archive/2025-10-02/{completion-reports,guides,old-configs}

# Move files (example)
mv *.sh scripts/development/worktrees/
mv *_COMPLETE.md Archive/2025-10-02/completion-reports/
mv *_GUIDE.md Archive/2025-10-02/guides/

# Fix permissions
find scripts/ -name "*.sh" -exec chmod +x {} \;
```

## Safety Rules

### Before Deletion
1. **ALWAYS create archive first** - Never delete without archiving
2. **Review file contents** - Make sure it's actually obsolete
3. **Check git history** - Ensure not recently modified
4. **Search for references** - `git grep "filename"`
5. **Create backup** - `tar czf backup-$(date +%Y%m%d).tar.gz files/`

### Safe Deletion Process
```bash
# 1. Create archive
mkdir -p Archive/2025-10-02/pre-cleanup-backup
cp -r files-to-delete/ Archive/2025-10-02/pre-cleanup-backup/

# 2. List what will be deleted
find . -name "*.tmp" > files-to-delete.txt

# 3. Review list
cat files-to-delete.txt

# 4. Delete if confirmed
cat files-to-delete.txt | xargs rm

# 5. Commit archive
git add Archive/
git commit -m "Archive files before cleanup"
```

## Performance Targets

- **Root Directory**: < 20 files
- **Total Disk Usage**: Reduce by 500MB+
- **Temporary Files**: 0 remaining
- **Duplicate Files**: 0 remaining
- **Misplaced Files**: 0 remaining
- **Archive Created**: Complete backup

## Success Metrics

- ✅ Root directory contains only essential files (< 20 files)
- ✅ All scripts organized in `scripts/` with subdirectories
- ✅ All documentation in `docs/` or archived
- ✅ Zero temporary/backup files (`.tmp`, `.bak`, `~`)
- ✅ Zero duplicate files
- ✅ All files follow naming conventions
- ✅ Complete archive of deleted files created
- ✅ Updated .gitignore file
- ✅ Documentation reflects new structure
- ✅ Disk space reduced by 500MB+
- ✅ Git worktrees cleaned up
- ✅ Permissions validated and fixed

## Rollback Plan

```bash
# If cleanup causes issues:

# 1. Restore from archive
cp -r Archive/2025-10-02/pre-cleanup-backup/* .

# 2. Or restore from git (if committed)
git checkout HEAD~1 -- .

# 3. Or restore specific files
git checkout HEAD -- path/to/file
```

## Documentation to Create

After cleanup, create these guides:

1. **Directory Structure Guide** (`docs/development/DIRECTORY_STRUCTURE.md`)
   - Explain organization
   - Document each directory's purpose
   - Provide file placement guidelines

2. **File Naming Conventions** (`docs/development/FILE_NAMING.md`)
   - Naming rules for different file types
   - Examples of good vs bad names
   - Renaming procedures

3. **Cleanup Maintenance** (`docs/development/CLEANUP_MAINTENANCE.md`)
   - Regular cleanup tasks
   - Automated cleanup scripts
   - Prevention strategies

---

**REMEMBER**: Safety first! Archive before deleting. When in doubt, move to Archive/ instead of deleting!
