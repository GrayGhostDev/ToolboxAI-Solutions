#!/bin/bash

# ToolBoxAI-Solutions Complete Cleanup Execution Script
# Executes the complete cleanup and reorganization process

set -e

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 ToolBoxAI-Solutions Complete Cleanup & Reorganization"
echo "========================================================"
echo "Project root: $PROJECT_ROOT"
echo "Script directory: $SCRIPT_DIR"
echo ""

# Function to run script with error handling
run_script() {
    local script_name="$1"
    local script_path="$SCRIPT_DIR/$script_name"
    local description="$2"
    
    echo "🔄 Running: $description"
    echo "Script: $script_name"
    echo "----------------------------------------"
    
    if [[ -f "$script_path" ]]; then
        if bash "$script_path"; then
            echo "✅ $description completed successfully"
        else
            echo "❌ $description failed"
            echo "🛑 Stopping cleanup process"
            exit 1
        fi
    else
        echo "❌ Script not found: $script_path"
        echo "🛑 Stopping cleanup process"
        exit 1
    fi
    
    echo ""
}

# Function to confirm before proceeding
confirm_step() {
    local step_name="$1"
    local description="$2"
    
    echo "⚠️  $step_name"
    echo "$description"
    echo ""
    read -p "Do you want to continue? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operation cancelled by user"
        exit 1
    fi
}

# Main execution flow
echo "📋 This script will perform the following operations:"
echo "   1. Create a complete backup of the project"
echo "   2. Remove duplicate files and directories"
echo "   3. Reorganize the project structure"
echo "   4. Update all file references and imports"
echo "   5. Validate the cleanup was successful"
echo ""

confirm_step "BACKUP CREATION" "This will create a complete backup of your project before making any changes."

# Step 1: Create backup
run_script "backup_project.sh" "Project backup creation"

confirm_step "DUPLICATE REMOVAL" "This will remove duplicate files and conflicting configurations."

# Step 2: Remove duplicates
run_script "remove_duplicates.sh" "Duplicate file removal"

confirm_step "STRUCTURAL REORGANIZATION" "This will reorganize the entire project structure and move files to new locations."

# Step 3: Reorganize structure
run_script "reorganize_structure.sh" "Structural reorganization"

confirm_step "REFERENCE UPDATES" "This will update all import paths, configuration references, and file paths."

# Step 4: Update references
run_script "update_references.sh" "Reference and import path updates"

confirm_step "VALIDATION" "This will validate that the cleanup was successful and test basic functionality."

# Step 5: Validate cleanup
run_script "validate_cleanup.sh" "Cleanup validation and testing"

echo "🎉 CLEANUP COMPLETED SUCCESSFULLY!"
echo "=================================="
echo ""
echo "📊 Summary of completed operations:"
echo "   ✅ Project backup created"
echo "   ✅ Duplicate files removed"
echo "   ✅ Project structure reorganized"
echo "   ✅ References and imports updated"
echo "   ✅ Cleanup validated"
echo ""
echo "🎯 Next steps:"
echo "   1. Install dependencies:"
echo "      cd $PROJECT_ROOT"
echo "      npm install"
echo "      cd src/roblox-environment && pip install -r requirements.txt"
echo ""
echo "   2. Test the reorganized project:"
echo "      npm run test"
echo "      cd src/roblox-environment && python -m pytest"
echo ""
echo "   3. Update any remaining hardcoded paths in your IDE"
echo ""
echo "   4. Commit the changes to version control:"
echo "      git add ."
echo "      git commit -m 'feat: complete project cleanup and reorganization'"
echo ""
echo "   5. Update team documentation with new structure"
echo ""
echo "📁 New project structure:"
echo "   docs/           - All documentation"
echo "   src/            - Source code"
echo "     ├── roblox-environment/  - Main Roblox platform"
echo "     ├── dashboard/           - React dashboard"
echo "     ├── api/                 - API components"
echo "     └── shared/              - Shared utilities"
echo "   scripts/        - Build and utility scripts"
echo "   config/         - Configuration files"
echo "   tests/          - Test suites"
echo "   tools/          - Development tools"
echo ""
echo "⚠️  IMPORTANT: Keep your backup until you've verified everything works correctly!"
echo "   Backup location: $PROJECT_ROOT-Backup-*"
echo ""
echo "🔗 For detailed information, see: $PROJECT_ROOT/CLEANUP_PLAN.md"
