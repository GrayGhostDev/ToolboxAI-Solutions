# Main Development Worktree Tasks
**Branch**: development-infrastructure-dashboard
**Ports**: Backend(8009), Dashboard(5180), MCP(9877), Coordinator(8888)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Read and follow `2025-IMPLEMENTATION-STANDARDS.md` before writing ANY code!

**Requirements**:
- ✅ Use ONLY official 2025 documentation
- ✅ React 19.1.0, TypeScript 5.9.2, Vite 6.0.1
- ✅ Python 3.12, FastAPI latest, Pydantic v2
- ✅ Auto-accept enabled for corrections
- ❌ NO deprecated patterns or legacy code

## Primary Objectives
1. **Infrastructure Dashboard Development**
   - Build comprehensive monitoring dashboard
   - Integrate system health metrics
   - Add real-time performance tracking

2. **System Integration**
   - Connect all microservices to central dashboard
   - Implement unified logging system
   - Setup cross-service communication

3. **Database Schema Updates**
   - Design infrastructure monitoring tables
   - Add metrics collection endpoints
   - Implement data aggregation pipelines

## Current Tasks
- [ ] Review existing dashboard components in `ToolboxAI-Solutions/apps/`
- [ ] Analyze current infrastructure metrics collection
- [ ] Design new dashboard layout with Roblox theme compatibility
- [ ] Implement backend API endpoints for metrics
- [ ] Add real-time WebSocket support for live updates
- [ ] Create comprehensive test suite
- [ ] Update documentation

## File Locations
- Frontend: `ToolboxAI-Solutions/apps/dashboard/`
- Backend: `ToolboxAI-Solutions/core/`
- Database: `ToolboxAI-Solutions/database/`
- Config: `ToolboxAI-Solutions/config/`

## Commands
```bash
cd ToolboxAI-Solutions
npm install
npm run dev        # Start development server on port 5180
npm run test       # Run tests
npm run lint       # Check code quality
```
