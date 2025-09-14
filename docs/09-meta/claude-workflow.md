# Claude Swarm Workflow (Warp + MCP + Redis)

## Overview
- Multiple Claude Code terminals coordinate via Redis-backed queue and locks.
- 14-step loop with strict gates: Objective → Tasking → Research → Plan → Tooling → Implement → Test → Fix → Retest → Cleanup → Final Test → Commit/Push → Update Docs → Next Task.
- Monitor alerts to terminal (low-noise). You can wire Slack/Pusher later.

## Quickstart
1) Ensure Redis is running locally (brew services start redis)
2) Start services in Warp workflows:
   - start:orchestrator
   - start:workers
   - start:monitor
3) Check health: check:health
4) Seed tasks:
   - python3 core/coordinators/cli/taskctl enqueue --capability implementation "Implement feature X"

## Workers
- Open multiple Claude terminals (Desktop/VS Code/Cursor) in Warp.
- Assign a capability per terminal (planning, implementation, research, fix, docs).
- Workers claim tasks matching their capability. Locks + heartbeats prevent overlap.

## Gates
- Review Gate enforces: tests ≥ 95%, coverage ≥ COVERAGE_MIN, lint/typecheck 0, and no stubs/simplifications.
- Releaser should push only when gates pass.

## Privacy & Performance
- Resource limits applied via cpulimit and ulimit in scripts/agents/run_supervisor.sh.
- No secrets are stored in repo; prefer Keychain/env.

---

**Last Updated**: 2025-09-14
