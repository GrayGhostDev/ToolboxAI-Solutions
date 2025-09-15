# Phase 2 – Task 2.5: TypeScript WebSocketMessageType Fixes

Last updated: 2025-09-15 06:12 local
Related source: TODO.md § “2.5 TypeScript WebSocketMessageType Fixes”

## Objective
Resolve TypeScript compilation errors by centralizing and completing the WebSocket message type definitions used by the Dashboard app. Ensure components compile and are type-safe when handling realtime events.

## Acceptance Criteria
- A single source of truth for WebSocket message types exists at `apps/dashboard/src/types/websocket.ts`.
- The union includes all required message types listed in TODO.md:
  - 'connect' | 'disconnect' | 'content_update' | 'quiz_update' | 'progress_update' |
    'class_online' | 'achievement_unlocked' | 'assignment_reminder' |
    'request_leaderboard' | 'leaderboard_update' | 'xp_gained' | 'badge_earned' | 'error'
- Components compile without TS errors, specifically:
  - `apps/dashboard/src/components/notifications/RealtimeToast.tsx`
  - `apps/dashboard/src/components/pages/Leaderboard.tsx`
- Type-check passes for the dashboard package:
  - `npm -w apps/dashboard run typecheck` (or `cd apps/dashboard && npx tsc --noEmit`)
- Relevant unit tests pass (Vitest), no new lint errors.

// ... existing code ...

## Out of Scope
- Backend message schema changes.
- Runtime WebSocket wiring or server event emission changes.

## Implementation Plan

1. Branch and environment
   - From repo root:
     - git checkout -b fix/dashboard-websocket-message-types
     - npm ci
     - npm -w apps/dashboard ci

2. Create/Update centralized type definition
   - File: `apps/dashboard/src/types/websocket.ts`
   - Export a literal union for message types, plus a `const` map for safer reuse.
   - Also export a type-guard and a canonical array to assist with exhaustive checks.
   - Example content skeleton:
     - export type WebSocketMessageType =
       'connect' | 'disconnect' | 'content_update' | 'quiz_update' | 'progress_update' |
       'class_online' | 'achievement_unlocked' | 'assignment_reminder' |
       'request_leaderboard' | 'leaderboard_update' | 'xp_gained' | 'badge_earned' | 'error';
     - export const WebSocketMessageTypes = [... as const]
     - export function isWebSocketMessageType(x: string): x is WebSocketMessageType { ... }

3. Update component imports and usages
   - RealtimeToast.tsx
     - Ensure it imports { WebSocketMessageType } (and optionally the constants) from `src/types/websocket`.
     - Replace string literal comparisons with the union type and constants where appropriate.
     - Add exhaustive switch/if handling with a `never` check to make future additions safer.
   - Leaderboard.tsx
     - Import the same type/constant and update guards and event handlers that reference:
       - 'request_leaderboard', 'leaderboard_update', 'xp_gained', 'badge_earned'

4. Optional improvement (low-risk, can defer if time-constrained)
   - Create a discriminated union shape for incoming messages:
     - type WebSocketMessage = { type: WebSocketMessageType; payload?: unknown }
   - Update narrow handlers where already compatible; otherwise leave as-is.

5. Type-check and tests
   - Type-check:
     - npm -w apps/dashboard run typecheck
     - Or: cd apps/dashboard && npx tsc --noEmit
   - Unit tests (Vitest):
     - npm -w apps/dashboard test -- --run
   - If Playwright E2E exists and is active, run quickly to ensure no regressions:
     - npx playwright test

6. Lint and format
   - npm -w apps/dashboard run lint
   - npm -w apps/dashboard run format  # if available in package scripts

7. Commit and PR
   - git add -A
   - git commit -m "fix(dashboard): complete WebSocketMessageType union and update component handlers

- Centralize message types in src/types/websocket
- Update RealtimeToast and Leaderboard to use typed constants
- Ensure exhaustive handling and type guards

Tests: Unit (✓), Build (✓)"
   - git push -u origin fix/dashboard-websocket-message-types
   - Open PR → target `develop` (per branch strategy), request review.

8. Verification and closure
   - Confirm CI passes (type-check, unit tests).
   - Check off TODO.md § 2.5 criteria.
   - Merge PR following approvals.

// ... existing code ...

## Risks and Mitigations
- Missed literal usage: Components may still use string literals elsewhere.
  - Mitigation: Grep for message type strings and replace with constants; rely on union type for compiler help.
- Future message additions break exhaustiveness.
  - Mitigation: Keep `never` checks in switches and rely on tsc to surface missing cases.
- Inconsistent import paths.
  - Mitigation: Use absolute alias (if configured) or consistent relative paths; update tsconfig paths if needed.

## Rollback Plan
- Revert PR or `git revert` the commit hash.
- Re-run dashboard typecheck to confirm return to previous state:
  - `npm -w apps/dashboard run typecheck`

## Time Estimate
- Implementation: 30–60 minutes
- Testing and polish: 15–30 minutes

## Verification Checklist (maps to TODO.md § 2.5)
- [ ] apps/dashboard/src/types/websocket.ts defines the complete union and exports supporting helpers/consts.
- [ ] RealtimeToast.tsx compiles and uses the centralized types.
- [ ] Leaderboard.tsx compiles and uses the centralized types.
- [ ] Dashboard typecheck passes: `npm -w apps/dashboard run typecheck`.
- [ ] Vitest suite passes (no new failures introduced).
- [ ] PR merged into develop with agreed commit message format.
