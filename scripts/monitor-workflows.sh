#!/bin/bash
# ============================================
# GitHub Actions Workflow Monitor
# ============================================
# Monitor all active workflow runs and their status

set -e

REPO_DIR="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"
cd "$REPO_DIR"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      GitHub Actions Workflow Status Monitor               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get current workflows
echo "📊 Current Workflow Runs (Last 30)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

gh run list --limit 30 --json name,status,conclusion,createdAt,databaseId | \
  jq -r '.[] | 
    select(.createdAt > (now - 3600 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | 
    "\(.name | .[0:45] | ljust(47)) | \(.status | ljust(12)) | \(.conclusion // "---")"' | \
  head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Summary by status
echo "📈 Summary by Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

gh run list --limit 50 --json status,conclusion,createdAt | \
  jq -r '.[] | select(.createdAt > (now - 3600 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .status' | \
  sort | uniq -c | \
  awk '{printf "%-15s: %3d runs\n", $2, $1}'

echo ""

# Summary by conclusion
echo "📋 Summary by Conclusion (Completed Runs)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

gh run list --limit 50 --json status,conclusion,createdAt | \
  jq -r '.[] | 
    select(.createdAt > (now - 3600 | strftime("%Y-%m-%dT%H:%M:%SZ")) and .status == "completed") | 
    .conclusion' | \
  sort | uniq -c | \
  awk '{
    conclusion = $2
    count = $1
    icon = "❓"
    if (conclusion == "success") icon = "✅"
    else if (conclusion == "failure") icon = "❌"
    else if (conclusion == "cancelled") icon = "🚫"
    else if (conclusion == "skipped") icon = "⏭️"
    printf "%s %-15s: %3d runs\n", icon, conclusion, count
  }'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Key deployment workflows
echo "🚀 Key Deployment Workflows"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for workflow in "CI/CD Pipeline" "Deploy to Render" "Docker Build and Push" "Workspace CI"; do
  status=$(gh run list --workflow="$workflow" --limit 1 --json status,conclusion | \
    jq -r '.[0] | "\(.status) - \(.conclusion // "in progress")"' 2>/dev/null || echo "not found")
  
  icon="⏳"
  if echo "$status" | grep -q "success"; then icon="✅"
  elif echo "$status" | grep -q "failure"; then icon="❌"
  elif echo "$status" | grep -q "in_progress"; then icon="🔄"
  fi
  
  printf "%s %-35s: %s\n" "$icon" "$workflow" "$status"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Secrets verification
echo "🔐 Configured Secrets"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

gh secret list | awk '{printf "✓ %-30s (Updated: %s)\n", $1, $2, $3, $4}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Recommendations
echo "💡 Next Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

completed=$(gh run list --limit 30 --json status | jq '[.[] | select(.status == "completed")] | length')
in_progress=$(gh run list --limit 30 --json status | jq '[.[] | select(.status == "in_progress")] | length')
queued=$(gh run list --limit 30 --json status | jq '[.[] | select(.status == "queued")] | length')

if [ "$queued" -gt 10 ]; then
  echo "⏳ Many workflows queued ($queued) - GitHub Actions may be busy"
  echo "   Wait 5-10 minutes and run this script again"
elif [ "$in_progress" -gt 5 ]; then
  echo "🔄 Workflows running ($in_progress) - Monitor progress:"
  echo "   gh run watch"
elif [ "$completed" -gt 15 ]; then
  echo "✅ Many workflows completed ($completed) - Check results:"
  echo "   gh run list --limit 20"
fi

echo ""
echo "📖 Useful Commands:"
echo "   gh run list --limit 20          - List recent runs"
echo "   gh run view <run-id>            - View specific run details"
echo "   gh run watch                    - Watch current run in real-time"
echo "   gh run view <run-id> --log      - View full logs"
echo "   gh run rerun <run-id>           - Rerun failed workflow"
echo ""
echo "🌐 View in Browser:"
echo "   https://github.com/GrayGhostDev/ToolboxAI-Solutions/actions"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Last updated: $(date)"
echo ""
