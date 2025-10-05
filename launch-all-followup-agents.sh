#!/bin/bash

# Launch all 10 follow-up agents in parallel

echo "🚀 Launching all 10 follow-up agents..."

agents=(
    "integration-coordinator"
    "security-hardening"
    "testing-excellence"
    "documentation-update"
    "dashboard-verification"
    "infrastructure-monitoring"
    "backend-integration"
    "roblox-integration"
    "git-finalization"
    "deployment-readiness"
)

for agent in "${agents[@]}"; do
    echo "Starting $agent..."
    open -a Warp "/private/tmp/claude-warp-$agent.sh"
    sleep 2
done

echo "✅ All agents launched!"
echo ""
echo "Monitor progress:"
echo "  ps aux | grep claude | grep -E 'integration|security|testing|documentation|dashboard|infrastructure|backend|roblox|git|deployment'"
