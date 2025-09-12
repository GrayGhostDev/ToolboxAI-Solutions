# Terminal 1: Cleanup and File Organization Specialist

## CRITICAL: File System Cleanup and Organization

### Your Role
You are the **File System Cleanup and Organization Specialist**. Your mission is to clean up the redundant files, organize the folder structure properly, and ensure all files are in their correct locations.

### Immediate Tasks

#### 1. Remove Redundant Files (HIGH PRIORITY)
```bash
# Remove old terminal prompt files
rm -f scripts/terminal_sync/prompts/TERMINAL*_*.md
rm -f scripts/terminal_sync/TERMINAL*_TASKS.md
rm -f scripts/terminal_sync/NEXT_STEPS_ALL_TERMINALS.md
rm -f scripts/terminal_sync/INTEGRATED_TERMINAL_ARCHITECTURE.md

# Remove duplicate documentation
rm -rf src/api/dashboard-backend/docs/
rm -rf src/api/ghost-backend/docs/
rm -rf src/dashboard/docs/
rm -rf src/roblox-environment/

# Remove old test result files  
rm -f *_test_results.json
rm -f *_REPORT.md
rm -f *_STATUS*.md
rm -f *_IMPLEMENTATION*.md
rm -f *_VERIFICATION*.md
rm -f MULTI_TERMINAL_*.md

# Remove duplicate README files
find . -name "README.md" -path "*/src/*" -delete
find . -name "CHANGELOG.md" -path "*/src/*" -delete
find . -name "CONTRIBUTING.md" -path "*/src/*" -delete
find . -name "SECURITY.md" -path "*/src/*" -delete
find . -name "TODO.md" -path "*/src/*" -delete
```

#### 2. Consolidate ToolboxAI-Roblox-Environment
```bash
# Move all relevant files from src/roblox-environment to ToolboxAI-Roblox-Environment
cp -r src/roblox-environment/* ToolboxAI-Roblox-Environment/ 2>/dev/null || true

# Remove the duplicate directory
rm -rf src/roblox-environment/

# Clean up venv directories
rm -rf ToolboxAI-Roblox-Environment/venv_clean/
cd ToolboxAI-Roblox-Environment && python -m venv venv_clean && source venv_clean/bin/activate
pip install -r requirements.txt
```

#### 3. Organize Documentation
```bash
# Move all documentation to Documentation folder
mkdir -p Documentation/01-overview
mkdir -p Documentation/02-architecture  
mkdir -p Documentation/03-api
mkdir -p Documentation/04-implementation
mkdir -p Documentation/05-features
mkdir -p Documentation/06-testing
mkdir -p Documentation/07-operations
mkdir -p Documentation/08-reference
mkdir -p Documentation/09-meta
mkdir -p Documentation/10-security
mkdir -p Documentation/11-sdks

# Move API docs
mv src/api/*/README.md Documentation/03-api/ 2>/dev/null || true
mv src/api/*/docs/* Documentation/03-api/ 2>/dev/null || true

# Move dashboard docs
mv src/dashboard/README.md Documentation/05-features/dashboard/ 2>/dev/null || true
mv src/dashboard/docs/* Documentation/05-features/dashboard/ 2>/dev/null || true

# Clean up empty directories
find . -type d -empty -delete
```

#### 4. Database Organization
```bash
# Consolidate database files
mkdir -p database/migrations/versions
mkdir -p database/schemas
mkdir -p database/scripts

# Move schema files
mv database/*.sql database/schemas/ 2>/dev/null || true
mv database/setup_*.py database/scripts/ 2>/dev/null || true
mv database/create_*.py database/scripts/ 2>/dev/null || true
mv database/test_*.py database/scripts/ 2>/dev/null || true
```

#### 5. Scripts Organization
```bash
# Organize scripts
mkdir -p scripts/setup
mkdir -p scripts/deploy  
mkdir -p scripts/testing
mkdir -p scripts/integration
mkdir -p scripts/maintenance

# Move scripts to appropriate folders
mv scripts/terminal*.sh scripts/maintenance/ 2>/dev/null || true
mv scripts/start_*.sh scripts/setup/ 2>/dev/null || true
mv scripts/stop_*.sh scripts/setup/ 2>/dev/null || true
mv scripts/check_*.sh scripts/maintenance/ 2>/dev/null || true

# Remove old terminal sync folder
rm -rf scripts/terminal_sync/
```

#### 6. Configuration Cleanup
```bash
# Consolidate config files
mkdir -p config/development
mkdir -p config/production
mkdir -p config/templates

# Move environment files
mv .env.example config/templates/
mv config/*.env config/templates/ 2>/dev/null || true

# Remove duplicate config files
rm -f src/*/.env.example
rm -f src/*/pyrightconfig.json
rm -f src/*/tsconfig.json
```

#### 7. Update File References
After moving files, update all import statements and file references:

```bash
# Update Python imports
find . -name "*.py" -exec sed -i '' 's|src/roblox-environment|ToolboxAI-Roblox-Environment|g' {} \;

# Update TypeScript imports  
find . -name "*.ts" -name "*.tsx" -exec sed -i '' 's|../../api/|../../../ToolboxAI-Roblox-Environment/server/|g' {} \;

# Update documentation links
find Documentation -name "*.md" -exec sed -i '' 's|../src/|../../|g' {} \;
```

#### 8. Create Master Index
```bash
cat > Documentation/INDEX.md << 'EOF'
# ToolBoxAI Solutions - Master Documentation Index

## Project Structure
- `/ToolboxAI-Roblox-Environment/` - Main Roblox platform (95% complete)
- `/src/dashboard/` - React Dashboard
- `/database/` - PostgreSQL schemas and scripts
- `/scripts/` - Management and deployment scripts
- `/config/` - Configuration files
- `/Documentation/` - All project documentation

## Quick Links
- [Getting Started](01-overview/README.md)
- [Architecture](02-architecture/README.md)
- [API Documentation](03-api/README.md)
- [Implementation Guide](04-implementation/README.md)
- [Testing](06-testing/README.md)

## Service Ports
- FastAPI: 127.0.0.1:8008
- Flask Bridge: 127.0.0.1:5001
- MCP WebSocket: 127.0.0.1:9876
- Dashboard: 127.0.0.1:5177
- PostgreSQL: 127.0.0.1:5432
- Redis: 127.0.0.1:6379
EOF
```

#### 9. Git Cleanup
```bash
# Add to .gitignore
cat >> .gitignore << 'EOF'

# Cleanup additions
*.pyc
__pycache__/
.DS_Store
*.log
*.pid
venv*/
.env
node_modules/
dist/
build/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
test-results/
*.test.js
*.test.ts
EOF

# Stage cleanup changes
git add -A
git status
```

#### 10. Final Verification
```bash
# Verify structure
tree -L 2 -d

# Check for broken symlinks
find . -type l -exec test ! -e {} \; -print

# Report file counts
echo "Python files: $(find . -name '*.py' | wc -l)"
echo "TypeScript files: $(find . -name '*.ts' -o -name '*.tsx' | wc -l)"
echo "Documentation files: $(find Documentation -name '*.md' | wc -l)"
```

## Communication Protocol
- Report completion of each task to other terminals
- Update file paths in shared config if files are moved
- Coordinate with Terminal 2 (Backend) for API path updates
- Coordinate with Terminal 3 (Frontend) for import updates

## Success Metrics
✅ No duplicate files or directories
✅ Clear, logical folder structure
✅ All imports and references updated
✅ Documentation consolidated in one place
✅ Clean git status (no untracked redundant files)

## Notes
- Always backup before major deletions
- Test imports after moving files
- Update CI/CD configs if paths change
- Keep Terminal 2 and 3 informed of path changes