# ToolBoxAI Solutions API Documentation

*Generated: 2025-09-21 06:26:29*

**Total Endpoints**: 385

## Endpoint Summary

- **DELETE**: 21 endpoints
- **GET**: 192 endpoints
- **OPTIONS**: 3 endpoints
- **POST**: 159 endpoints
- **PUT**: 10 endpoints

## api/auth/rate_limiter.py

### 🔵 POST `/login`

**Function**: `unknown`

*No description available*

---

## api/health.py

### 🟢 GET `/health`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/ready`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/live`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/metrics`

**Function**: `unknown`

*No description available*

---

## api/health/health_checks.py

### 🟢 GET `/health/live`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/health/ready`

**Function**: `unknown`

*No description available*

---

## api/routes/mfa_routes.py

### 🔵 POST `/setup/init`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/setup/confirm`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/verify`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/resend`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/disable`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/backup-codes`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/admin/rollout`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/admin/enable-role`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/admin/enable-user`

**Function**: `unknown`

*No description available*

---

## api/routes/oauth_routes.py

### 🟢 GET `/authorize`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/authorize/consent`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/token`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/introspect`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/revoke`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/register`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/clients`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/clients/{client_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/.well-known/jwks.json`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/.well-known/oauth-authorization-server`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/admin.py

### 🔴 DELETE `/users/{user_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/agent_swarm.py

### 🔵 POST `/chat/stream`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/task`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/session/{session_id}`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/session/{session_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/reset`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/lesson/create`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/assessment/create`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/analyze/progress`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/ai_agent_orchestration.py

### 🔵 POST `/tasks`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/tasks`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/tasks/{task_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/agents`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/agents/{agent_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/workflows`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/workflows/{workflow_id}/start`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/sparc`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/sparc/{sparc_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/swarms`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/performance/agents/{agent_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/ai_chat.py

### 🔵 POST `/conversations`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

### 🔵 POST `/conversations/{conversation_id}/messages`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

### 🔵 POST `/generate`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

### 🟢 GET `/conversations/{conversation_id}`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

### 🟢 GET `/conversations`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

### 🔴 DELETE `/conversations/{conversation_id}`

**Function**: `initialize_assistant`

**Description**: Initialize the assistant with API key

---

## api/v1/endpoints/analytics.py

### 🟢 GET `/overview`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/student-progress`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/weekly_xp`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/subject_mastery`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/leaderboard`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{user_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/trends/engagement`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/trends/content`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/dashboard`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/realtime`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/summary`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/analytics_reporting.py

### 🔵 POST `/query`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/reports/{report_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/dashboards`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/dashboards`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/dashboards/{dashboard_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/learning-analytics`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/system-health`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/engagement`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/export/{query_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/api_keys.py

### 🔴 DELETE `/{key_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/roblox/generate-script`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/roblox/validate-script`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/roblox/content`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/usage-stats`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/assessments.py

### 🟢 GET `/{assessment_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/{assessment_id}/submit`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{assessment_id}/results`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{assessment_id}/statistics`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/auth.py

### 🔵 POST `/refresh`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/logout`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/classes.py

### 🟢 GET `/{class_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{class_id}/students`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{class_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/{class_id}/students/{student_id}`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{class_id}/students/{student_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/{class_id}/students/batch`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{class_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/compliance.py

### 🟢 GET `/reports`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/reports`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/audit-logs`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/verify/{category}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/requirements/{category}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/dashboard.py

### 🟢 GET `/overview/{role}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/notifications`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/student`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/teacher`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/admin`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/parent`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/quick-stats`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/database_swarm.py

### 🔵 POST `/workflow/execute`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/workflow/state/{thread_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/agents/status`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/events/append`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/events/replay/{aggregate_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/query/optimize`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/backup/create`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/migration/execute`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/monitoring/metrics`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/cache/invalidate`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/design_files.py

### 🔵 POST `/process-file`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/scan-folder`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/search`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/folder/{folder_path:path}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/categories`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/supported-extensions`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/educational_content.py

### 🟢 GET `/{content_id}`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{content_id}`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{content_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{content_id}/analytics`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/{content_id}/publish`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/standards/search`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/enhanced_content.py

### 🟢 GET `/status/{pipeline_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/validate`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/history`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/personalize`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/gamification.py

### 🟢 GET `/achievements`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/badges`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/xp/add`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/stats/{userId}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/integration.py

### 🔵 POST `/workflow/create`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/workflow/templates`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/schema/register`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/sync/trigger`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/event/broadcast`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/health/check`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/maintenance/cleanup`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/lessons.py

### 🟢 GET `/{lesson_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{lesson_id}/progress`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{lesson_id}/statistics`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/messages.py

### 🟢 GET `/unread-count`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{message_id}`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{message_id}/read`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{message_id}/archive`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{message_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/notifications/recent`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/mobile.py

### 🔵 POST `/register-device`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/mobile-login`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/content/mobile-list`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/progress/batch-update`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/push/send`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/content/{content_id}/download`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/network-status`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/data-usage`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/orchestrator.py

### 🔵 POST `/submit`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/status/{task_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/worktree/distribute`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/worktree/sessions`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/resources/monitor`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/resources/alerts`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/resources/optimize`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/shutdown`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/password.py

### 🔵 POST `/change`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/strength-requirements`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/sessions`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/logout-all`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/privacy.py

### 🔵 POST `/request-export`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/export/{ticket}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/request-deletion`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/export-status/{ticket}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/consents`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/consents/parent-verify`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/progress.py

### 🟢 GET `/{item_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/update`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{item_id}`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/prompt_templates.py

### 🔵 POST `/conversations/start`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversations/process`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversations/{conversation_id}/personalize`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversations/{conversation_id}/enhance-uniqueness`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/conversations/{conversation_id}/validate`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversations/{conversation_id}/generate-workflow`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/conversations/{conversation_id}/analytics`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/conversations`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/conversations/{conversation_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/system/status`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/templates`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/guidance/{stage}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/pusher_auth.py

### 🔵 POST `/auth`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/reports.py

### 🟢 GET `/stats/overview`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{report_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/analytics/engagement`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/status/{report_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/download/{report_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox.py

### 🔵 POST `/game/create`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/game/{game_id}`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟡 PUT `/game/{game_id}/settings`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔴 DELETE `/game/{game_id}`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/content/generate`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/content/templates`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/content/deploy`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/content/{content_id}/status`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/progress/update`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/progress/{student_id}`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/progress/checkpoint`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/progress/leaderboard`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/webhook`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/analytics/session/{session_id}`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/analytics/performance`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🔵 POST `/analytics/event`

**Function**: `estimate_generation_time`

**Description**: Estimate content generation time in minutes

---

### 🟢 GET `/auth/login`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/plugin/status`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox_agents.py

### 🔵 POST `/generate-content`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/optimize-script`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/validate-security`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/batch-validate`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox_ai.py

### 🔵 POST `/chat`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/conversation/{conversation_id}/status`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/conversation/{conversation_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/webhook/pusher`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox_environment.py

### 🔵 POST `/preview`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/create`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/status/{environment_name}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/rojo/info`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/rojo/check`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/list`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{environment_name}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox_integration.py

### 🔵 POST `/auth/initiate`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/oauth/callback`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/revoke`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversation/start`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversation/input`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversation/advance`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/conversation/generate`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/rojo/check`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/rojo/projects`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/rojo/project/{project_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/rojo/project/{project_id}/start`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/rojo/project/{project_id}/stop`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/rojo/project/{project_id}/build`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/rojo/project/{project_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/assets/upload`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/assets/{asset_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/datastore/set`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/datastore/get`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/messaging/publish`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/roblox_integration_enhanced.py

### 🔵 POST `/scripts/generate`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/scripts/validate`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/assets`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/environments/deploy`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/environments/{deployment_id}/status`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/studio/sync`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/environments/active`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/marketplace/browse`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/schools.py

### 🟢 GET `/`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/{school_id}`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/{school_id}`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/{school_id}`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/stripe_checkout.py

### 🔵 POST `/checkout-session`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/stripe_webhook.py

### 🔵 POST `/webhook`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/stripe_webhooks.py

### 🔵 POST `/webhooks`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/webhook-status`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/user_management_enhanced.py

### 🔵 POST `/users`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/users`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/users/{user_id}`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/users/{user_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/users/{user_id}/progress`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/users/{user_id}/achievements`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/parent-dashboard`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/link-parent`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/users/{user_id}/sessions`

**Function**: `unknown`

*No description available*

---

## api/v1/endpoints/users.py

### 🟢 GET `/stats/users`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/health`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/activity`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/revenue`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/support/queue`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/metrics`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/compliance/status`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/classes/today`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/progress`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/grades/pending`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/calendar`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/submissions`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/xp`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/assignments/due`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/achievements/recent`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/rank`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/path`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/roblox/worlds`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/children/overview`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/grades/recent`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/events`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/attendance/summary`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

### 🟢 GET `/progress/chart`

**Function**: `register_user_routers`

**Description**: Register all user-specific routers with the main app

---

## api/v1/endpoints/validation.py

### 🔵 POST `/validate`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🔵 POST `/validate/batch`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🟢 GET `/reports/{validation_id}`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🟢 GET `/statistics`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🔵 POST `/templates/secure`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🟢 GET `/checklists/security`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

### 🟢 GET `/checklists/compliance`

**Function**: `_filter_report_by_type`

**Description**: Filter comprehensive report based on validation type

---

## api/v1/roblox_environments.py

### 🟢 GET `/environments`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/environments`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/environments/{environment_id}/generate`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/environments/{environment_id}/deploy`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/environments/{environment_id}`

**Function**: `unknown`

*No description available*

---

## main.py

### 🔵 POST `/pusher/auth`

**Function**: `get_field_path`

**Description**: Extract field path from validation error

---

### 🔵 POST `/realtime/trigger`

**Function**: `get_field_path`

**Description**: Extract field path from validation error

---

### 🔵 POST `/pusher/webhook`

**Function**: `get_field_path`

**Description**: Extract field path from validation error

---

### ⚪ OPTIONS `/health`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/health`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/metrics`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/ws/status`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/pusher/status`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/pusher/trigger`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/sentry/status`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/info`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/content/generate`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/content/{content_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/endpoint/that/errors`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/sentry-debug`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/test/rate-limit`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/roblox/deploy/{content_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/api/v1/roblox/download/{content_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/ai-chat/conversations`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/ai-chat/conversations/{conversation_id}/messages`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/ai-chat/generate`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/api/v1/analytics/summary`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/reports/generate`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/api/v1/reports/download/{report_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟢 GET `/api/v1/admin/users`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔵 POST `/api/v1/admin/users`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🟡 PUT `/api/v1/admin/users/{user_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### 🔴 DELETE `/api/v1/admin/users/{user_id}`

**Function**: `generate_csv_content`

**Description**: Generate CSV content from report data

---

### ⚪ OPTIONS `/auth/login`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/login`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/refresh`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/token`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/ws/rbac`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/ws/rbac`

**Function**: `unknown`

*No description available*

---

### 🔴 DELETE `/ws/rbac`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/status`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/users/me`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/dashboard/overview`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/analytics/weekly_xp`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/analytics/subject_mastery`

**Function**: `unknown`

*No description available*

---

### ⚪ OPTIONS `/auth/verify`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/auth/verify`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/api/v1/terminal/verification`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate_content`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate_quiz`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate_terrain_original`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/lms/courses`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/lms/course/{course_id}`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/plugin/register`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/plugin/message`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/admin/status`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/admin/broadcast`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/agents/health`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/v1/user/profile`

**Function**: `unknown`

*No description available*

---

### 🟡 PUT `/api/v1/user/profile`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/sync`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/register_plugin`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/plugin/{plugin_id}/heartbeat`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/plugin/{plugin_id}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/plugins`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate_simple_content`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/generate_terrain`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/script/{script_type}`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/status`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/config`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/config`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/cache/clear`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/api/versions`

**Function**: `unknown`

*No description available*

---

## routers/error_handling_api.py

### 🔵 POST `/report-error`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/process-errors`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/workflow/{workflow_id}/status`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/patterns/analyze`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/predict-errors`

**Function**: `unknown`

*No description available*

---

### 🟢 GET `/swarm/status`

**Function**: `unknown`

*No description available*

---

### 🔵 POST `/recovery/trigger`

**Function**: `unknown`

*No description available*

---

