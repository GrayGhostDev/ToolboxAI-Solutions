#!/bin/bash
# Setup Automatic Cleanup Scheduling
# Based on CLEANUP_INTEGRATED.md scheduling protocols

PROJECT_ROOT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
CLEANUP_SCRIPT="$PROJECT_ROOT/scripts/terminal_sync/intelligent_cleanup.py"
EMERGENCY_SCRIPT="$PROJECT_ROOT/scripts/terminal_sync/emergency_cleanup.sh"

echo "======================================"
echo "🕐 Setup Automatic Cleanup Scheduling"
echo "======================================"
echo ""

# Check if scripts exist
if [ ! -f "$CLEANUP_SCRIPT" ]; then
    echo "❌ Error: Cleanup script not found at $CLEANUP_SCRIPT"
    exit 1
fi

if [ ! -f "$EMERGENCY_SCRIPT" ]; then
    echo "❌ Error: Emergency script not found at $EMERGENCY_SCRIPT"
    exit 1
fi

# Make scripts executable
chmod +x "$CLEANUP_SCRIPT"
chmod +x "$EMERGENCY_SCRIPT"

# Function to add cron job if it doesn't exist
add_cron_job() {
    local schedule="$1"
    local command="$2"
    local description="$3"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$command"; then
        echo "✓ $description already scheduled"
    else
        # Add the cron job
        (crontab -l 2>/dev/null; echo "# $description"; echo "$schedule $command") | crontab -
        echo "✅ Added: $description"
    fi
}

echo "📋 Setting up cron jobs..."
echo ""

# Daily cleanup at 3 AM
add_cron_job \
    "0 3 * * *" \
    "/usr/bin/python3 $CLEANUP_SCRIPT --type python node logs >/dev/null 2>&1" \
    "ToolBoxAI Daily Cleanup (3 AM)"

# Weekly comprehensive cleanup on Sunday at 2 AM
add_cron_job \
    "0 2 * * 0" \
    "/usr/bin/python3 $CLEANUP_SCRIPT --aggressive >/dev/null 2>&1" \
    "ToolBoxAI Weekly Deep Cleanup (Sunday 2 AM)"

# Emergency check every 6 hours
add_cron_job \
    "0 */6 * * *" \
    "$EMERGENCY_SCRIPT >/dev/null 2>&1" \
    "ToolBoxAI Emergency Space Check (Every 6 hours)"

echo ""
echo "======================================"
echo "📅 Current Cron Schedule"
echo "======================================"
crontab -l | grep -E "ToolBoxAI|intelligent_cleanup|emergency_cleanup" || echo "No ToolBoxAI cleanup jobs found"

echo ""
echo "======================================"
echo "🛠️ Manual Commands"
echo "======================================"
echo "Run standard cleanup:"
echo "  python $CLEANUP_SCRIPT"
echo ""
echo "Run aggressive cleanup:"
echo "  python $CLEANUP_SCRIPT --aggressive"
echo ""
echo "Run emergency cleanup:"
echo "  $EMERGENCY_SCRIPT"
echo ""
echo "Preview cleanup (dry run):"
echo "  python $CLEANUP_SCRIPT --dry-run"
echo ""
echo "View cron jobs:"
echo "  crontab -l"
echo ""
echo "Remove cleanup jobs:"
echo "  crontab -l | grep -v 'ToolBoxAI' | crontab -"
echo ""
echo "✅ Automatic cleanup setup complete!"