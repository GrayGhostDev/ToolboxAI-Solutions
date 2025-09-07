#!/bin/bash

# ToolBoxAI-Solutions Project Backup Script
# Creates a complete backup before cleanup operations

set -e

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
BACKUP_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions-Backup-$(date +%Y%m%d-%H%M%S)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔒 Creating project backup..."
echo "Source: $PROJECT_ROOT"
echo "Backup: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Copy entire project (excluding node_modules and venv for size)
echo "📁 Copying project files..."
rsync -av --exclude='node_modules' \
          --exclude='venv' \
          --exclude='venv_clean' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='*.pyc' \
          --exclude='.DS_Store' \
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

Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)
File Count: $(find "$BACKUP_DIR" -type f | wc -l)

Restore Instructions:
1. Stop any running services
2. Remove current project directory
3. Copy backup to original location
4. Restore node_modules: npm install
5. Restore virtual environments: python -m venv venv_clean
6. Install dependencies: pip install -r requirements.txt
EOF

echo "✅ Backup completed successfully!"
echo "📁 Backup location: $BACKUP_DIR"
echo "📋 Manifest: $BACKUP_DIR/BACKUP_MANIFEST.txt"
echo ""
echo "🔍 Backup verification:"
echo "   Files backed up: $(find "$BACKUP_DIR" -type f | wc -l)"
echo "   Backup size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "⚠️  IMPORTANT: Keep this backup until cleanup is verified successful!"
