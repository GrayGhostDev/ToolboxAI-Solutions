#!/bin/bash
# Emergency Space Recovery Script
# Based on CLEANUP_INTEGRATED.md emergency protocols

CRITICAL_THRESHOLD=95
PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Check disk usage
CURRENT_USAGE=$(df -h /Volumes/G-DRIVE\ ArmorATD | awk 'NR==2 {print int($5)}')

echo "=============================="
echo "🚨 Emergency Cleanup Check"
echo "=============================="
echo "Current disk usage: ${CURRENT_USAGE}%"
echo "Critical threshold: ${CRITICAL_THRESHOLD}%"
echo ""

if [ $CURRENT_USAGE -gt $CRITICAL_THRESHOLD ]; then
    echo "CRITICAL: Disk usage at ${CURRENT_USAGE}%"
    echo "Starting emergency cleanup..."
    echo ""
    
    # Clean temporary files
    echo "1. Cleaning temporary files..."
    find /tmp -type f -mtime +1 -delete 2>/dev/null
    find $PROJECT_ROOT -name "*.tmp" -delete 2>/dev/null
    
    # Clean all Python artifacts aggressively
    echo "2. Cleaning Python artifacts..."
    find $PROJECT_ROOT -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find $PROJECT_ROOT -type f -name "*.pyc" -delete 2>/dev/null
    find $PROJECT_ROOT -type f -name "*.pyo" -delete 2>/dev/null
    find $PROJECT_ROOT -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
    find $PROJECT_ROOT -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null
    find $PROJECT_ROOT -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
    
    # Clean all node_modules
    echo "3. Removing all node_modules..."
    find $PROJECT_ROOT -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null
    
    # Clean logs older than 7 days
    echo "4. Cleaning old logs..."
    find $PROJECT_ROOT -name "*.log" -mtime +7 -delete 2>/dev/null
    
    # Clear package manager caches
    echo "5. Clearing package caches..."
    npm cache clean --force 2>/dev/null || true
    pip cache purge 2>/dev/null || true
    
    # Clean build directories
    echo "6. Cleaning build artifacts..."
    find $PROJECT_ROOT -type d -name "dist" -exec rm -rf {} + 2>/dev/null
    find $PROJECT_ROOT -type d -name "build" -exec rm -rf {} + 2>/dev/null
    
    # Git cleanup
    echo "7. Running git garbage collection..."
    cd $PROJECT_ROOT && git gc --aggressive --prune=now 2>/dev/null
    
    # Check new usage
    NEW_USAGE=$(df -h /Volumes/G-DRIVE\ ArmorATD | awk 'NR==2 {print int($5)}')
    
    echo ""
    echo "=============================="
    echo "✅ Emergency cleanup complete"
    echo "=============================="
    echo "Disk usage before: ${CURRENT_USAGE}%"
    echo "Disk usage after: ${NEW_USAGE}%"
    echo "Space freed: $((CURRENT_USAGE - NEW_USAGE))%"
    
else
    echo "✅ Disk usage is healthy (${CURRENT_USAGE}%)"
    echo ""
    
    # Run normal cleanup if requested
    if [ "$1" == "--force" ]; then
        echo "Running standard cleanup..."
        python $PROJECT_ROOT/scripts/terminal_sync/intelligent_cleanup.py
    fi
fi

echo ""
echo "=============================="
echo "📊 Current Status"
echo "=============================="
df -h /Volumes/G-DRIVE\ ArmorATD