ToolboxAI Roblox — Setup, Usage, and Integration

Overview
- Modern Luau project with Rojo mapping under `Config/default.project.json`.
- Roblox Studio plugins in `plugins/` (primary: `AIContentGenerator.lua`).
- Secure runtime configuration via `SecureConfigurationManager` (no secrets hardcoded).
- Real-time: Pusher Channels (via backend bridge) instead of direct WebSockets.

Prerequisites
- Roblox Studio (latest) and Rojo 7.4+ (via Aftman or system install).
- Optional: Selene and StyLua for lint/format.

Quick Start
- Serve to Studio: run `rojo serve roblox/Config/default.project.json` and connect via the Studio Rojo plugin.
- Build place: `rojo build roblox/Config/default.project.json -o out.rbxlx`.
- Build plugin: `rojo build roblox/Config/plugin.project.json -o AIContentGenerator.rbxmx` then install in Studio.

Rojo Project Layout
- Server: `ServerScriptService/Server` maps to `src/server/*` (init at `src/server/init.server.luau`).
- Main server script: `ServerScriptService/Main` from `src/Main.server.lua`.
- Secure config: `ServerScriptService/SecureConfigurationManager` from `src/server/SecureConfigurationManager.lua`.
- Client: `StarterPlayer/StarterPlayerScripts/Client` from `src/client/*`.
- Shared modules: `ReplicatedStorage/Shared` and `ReplicatedStorage/Modules` from `src/shared/*`.
- SDK: `ReplicatedStorage/SDK/ToolBoxAI` from `src/Modules/*`.

Secure Configuration
- Manager: `src/server/SecureConfigurationManager.lua` (auto‑provisioned on first run).
- Set ServerStorage attributes in Studio (Explorer → ServerStorage):
  - `BACKEND_URL` (e.g., `http://127.0.0.1:8009`)
  - `BRIDGE_URL` (e.g., `http://127.0.0.1:5001`)
  - `DASHBOARD_URL` (e.g., `http://127.0.0.1:5179`)
  - Optional: `API_KEY`, `SECRET_KEY`, `Environment` (`development|staging|production`)
- Non‑sensitive toggles are read from the manager; sensitive values must not be hardcoded.

Realtime (Pusher)
- Roblox does not expose a first‑class WebSocket client in all runtimes; this project uses a bridge service to subscribe to Pusher and exposes a lightweight HTTP polling endpoint to Studio/game code.
- Plugin sends events via `POST /plugin/send-message` (or `/plugin/pusher/send`) to the bridge, which relays to Pusher.
- Plugin polls `POST /plugin/messages` for Pusher channel updates when Studio lacks native sockets.
- Bridge endpoints are configurable in `plugins/AIContentGenerator.lua` under `CONFIG.ENDPOINTS` if your bridge paths differ.
- Dev tip: you can point the plugin at the backend (8009) instead of a separate bridge by setting the plugin setting `UseBackendBridge = true` (Studio → Plugin settings). When enabled, the plugin will send bridge traffic to `API_URL`.

Plugins
- Primary Studio plugin: `plugins/AIContentGenerator.lua` (UI + Pusher via bridge with HTTP polling fallback).
- Enhanced plugin: `plugins/EnhancedToolboxAI_Plugin.lua` (advanced features/components/services).
- Config module: `plugins/PluginConfig.lua` (utility for storing plugin settings).

Testing
- In‑Studio integration checks: `tests/IntegrationTests.lua` (skips optional modules gracefully).

Notes and Conventions
- New Luau files should use `.luau` where possible; keep client/server/shared separation.
- Do not commit secrets; use `.env*` for backend services and ServerStorage attributes in Studio.
- CI `roblox-sync` workflow is a placeholder; prefer local Rojo for development.

Related Documentation
- Project structure: `roblox/ROBLOX_STRUCTURE.md`
- Bridge/API details: `docs/ROBLOX_BRIDGE_IMPLEMENTATION.md`
- Dev guide: `docs/05-implementation/agent-system/roblox-development-guide.md`
