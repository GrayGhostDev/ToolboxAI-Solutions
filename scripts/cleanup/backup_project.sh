#!/bin/bash

# ToolBoxAI-Solutions Project Backup Script
# Creates a complete backup before cleanup operations

set -e

# Determine project root dynamically (allow override)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/project_backup_$(date +%Y%m%d-%H%M%S)}"

echo "🔒 Creating project backup..."
echo "Source: $PROJECT_ROOT"
echo "Backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy entire project (excluding heavy/transient dirs)
echo "📁 Copying project files..."
rsync -av --exclude='node_modules' \
          --exclude='venv' \
          --exclude='.venv' \
          --exclude='venv_clean' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='*.pyc' \
          --exclude='.DS_Store' \
          --exclude='logs' \
          "$PROJECT_ROOT/" "$BACKUP_DIR/"

# Create backup manifest
echo "📋 Creating backup manifest..."
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
ToolBoxAI-Solutions Project Backup
==================================
Backup Date: $(date)
Source: $PROJECT_ROOT
Backup Location: $BACKUP_DIR

Backup Contents:
- All source code files
- Configuration files
- Documentation
- Scripts and utilities
- Test files

Excluded:
- node_modules directories
- Python virtual environments
- __pycache__ directories
- .git directory
- Compiled Python files
- System files (.DS_Store)
- logs directory

Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)
File Count: $(find "$BACKUP_DIR" -type f | wc -l)

Restore Instructions:
1. Stop any running services
2. Restore backup to original location
3. Restore JS deps: npm install
4. Restore Python venvs: python -m venv venv_clean && pip install -r requirements.txt
EOF

echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR"
echo "📋 Manifest: $BACKUP_DIR/BACKUP_MANIFEST.txt"
