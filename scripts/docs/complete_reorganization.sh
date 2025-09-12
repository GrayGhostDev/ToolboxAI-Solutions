#!/bin/bash

# Documentation Reorganization Completion Script
# This script completes the reorganization of ToolBoxAI-Solutions documentation

echo "🚀 Starting documentation reorganization completion..."

# Function to safely move files
move_file() {
    if [ -f "$1" ]; then
        echo "Moving $1 to $2"
        mv "$1" "$2"
    else
        echo "⚠️  File not found: $1"
    fi
}

# Create any missing directories
echo "📁 Ensuring directory structure..."
mkdir -p 03-api/endpoints
mkdir -p 05-features/dashboards
mkdir -p 02-architecture/components

# API Documentation
echo "📚 Organizing API documentation..."
move_file "api/api-reference.md" "03-api/README.md"
move_file "api/authentication.md" "03-api/authentication.md"
move_file "api/endpoints.md" "03-api/endpoints/README.md"
move_file "api/errors.md" "03-api/error-handling.md"

# Implementation Documentation
echo "🔧 Organizing implementation documentation..."
move_file "coding-standards.md" "04-implementation/coding-standards.md"
move_file "testing-guidelines.md" "04-implementation/testing-guidelines.md"
move_file "deployment.md" "04-implementation/deployment.md"

# Feature Documentation
echo "✨ Organizing feature documentation..."
move_file "lesson-system.md" "05-features/lesson-system.md"
move_file "quiz-system.md" "05-features/quiz-system.md"
move_file "gamification-system.md" "05-features/gamification.md"
move_file "progress-tracking-system.md" "05-features/progress-tracking.md"
move_file "navigation-system.md" "05-features/navigation.md"
move_file "student-dashboard.md" "05-features/dashboards/student-dashboard.md"
move_file "educator-dashboard.md" "05-features/dashboards/educator-dashboard.md"
move_file "content-creation-system.md" "05-features/content-creation.md"

# User Guides
echo "👥 Organizing user guides..."
move_file "guides/admin-guide.md" "06-user-guides/admin-guide.md"
move_file "guides/educator-guide.md" "06-user-guides/educator-guide.md"
move_file "guides/student-user-guide.md" "06-user-guides/student-guide.md"
move_file "guides/user-guide.md" "06-user-guides/general-guide.md"

# Operations Documentation
echo "⚙️ Organizing operations documentation..."
move_file "installation.md" "07-operations/installation.md"
move_file "performance.md" "07-operations/performance.md"
move_file "security.md" "07-operations/security.md"
move_file "troubleshooting.md" "07-operations/troubleshooting.md"

# Reference Documentation
echo "📖 Organizing reference documentation..."
move_file "system-requirements.md" "08-reference/system-requirements.md"
move_file "user-roles.md" "08-reference/user-roles.md"
move_file "mvp-score-system.md" "08-reference/mvp-score-system.md"
move_file "guides/accessibility.md" "08-reference/accessibility.md"
move_file "guides/accessibility-testing.md" "08-reference/accessibility-testing.md"

# Meta Documentation
echo "📝 Organizing meta documentation..."
move_file "CLAUDE.md" "09-meta/CLAUDE.md"
move_file "changelog.md" "09-meta/changelog.md"
move_file "release-notes.md" "09-meta/release-notes.md"
move_file "contributing.md" "09-meta/contributing.md"
move_file "faq.md" "09-meta/faq.md"

# Design Components
echo "🏗️ Moving design components..."
move_file "design/agents.md" "02-architecture/components/agents.md"
move_file "design/lms-integration.md" "02-architecture/components/lms-integration.md"
move_file "design/plugin.md" "02-architecture/components/roblox-plugin.md"

# Clean up old directories
echo "🧹 Cleaning up old directories..."
if [ -d "api" ] && [ -z "$(ls -A api)" ]; then
    rmdir api
    echo "Removed empty api directory"
fi

if [ -d "guides" ] && [ -z "$(ls -A guides)" ]; then
    rmdir guides
    echo "Removed empty guides directory"
fi

if [ -d "design" ] && [ -z "$(ls -A design)" ]; then
    rmdir design
    echo "Removed empty design directory"
fi

# Remove duplicate files
echo "🗑️ Removing duplicate files..."
files_to_remove=(
    "data-models.md"
    "architecture.md"
    "project-overview.md"
    "getting-started.md"
    "README.md"
)

for file in "${files_to_remove[@]}"; do
    if [ -f "$file" ]; then
        echo "Removing duplicate: $file"
        rm "$file"
    fi
done

# Remove .DS_Store files
echo "🧹 Removing .DS_Store files..."
find . -name ".DS_Store" -type f -delete

# Create a new main README if needed
if [ ! -f "README.md" ]; then
    echo "📄 Creating main README..."
    cat > README.md << 'EOF'
# ToolBoxAI-Solutions Documentation

Welcome to the comprehensive documentation for ToolBoxAI-Solutions.

## 📚 Documentation Structure

All documentation has been reorganized into a clear hierarchical structure:

- **[01-overview/](01-overview/)** - Start here for project overview and getting started
- **[02-architecture/](02-architecture/)** - Technical architecture and data models
- **[03-api/](03-api/)** - API reference and integration guides
- **[04-implementation/](04-implementation/)** - Development guidelines and deployment
- **[05-features/](05-features/)** - Feature documentation
- **[06-user-guides/](06-user-guides/)** - Role-specific user guides
- **[07-operations/](07-operations/)** - Operations and maintenance
- **[08-reference/](08-reference/)** - Technical references and requirements
- **[09-meta/](09-meta/)** - Project metadata and contribution guidelines

## 🚀 Quick Start

Begin with the [Overview Documentation](01-overview/README.md) for a comprehensive introduction and navigation guide.

---

*For detailed navigation, see [01-overview/README.md](01-overview/README.md)*
EOF
fi

echo "✅ Documentation reorganization complete!"
echo ""
echo "📊 Summary:"
echo "- Files have been moved to their new locations"
echo "- Old directories have been cleaned up"
echo "- Duplicate files have been removed"
echo ""
echo "📝 Next steps:"
echo "1. Review the new structure in each numbered directory"
echo "2. Check REORGANIZATION_STATUS.md for remaining tasks"
echo "3. Create any missing documentation files as needed"
echo "4. Update any internal links in the documentation"

# Make the script remove itself after execution (optional)
# rm -- "$0"