# Documentation Worktree Tasks
**Branch**: docs/cleanup-2025-09-11
**Ports**: Backend(8013), Dashboard(5184), MCP(9881), Coordinator(8892)

## 🚨 CRITICAL: 2025 Implementation Standards

**MANDATORY**: Document ONLY 2025 current implementations!

**Requirements**:
- ✅ Reference official 2025 documentation
- ✅ Update examples to React 19, Python 3.12
- ✅ Remove outdated tutorials
- ✅ Auto-accept enabled for corrections
- ❌ NO documentation of deprecated patterns

## Primary Objectives
1. **Documentation Cleanup**
   - Remove outdated documentation
   - Update README files
   - Consolidate duplicate docs

2. **API Documentation**
   - Generate OpenAPI/Swagger specs
   - Create endpoint examples
   - Add authentication guides

3. **Developer Guides**
   - Write setup instructions
   - Create contribution guidelines
   - Add troubleshooting guides

## Current Tasks
- [ ] Audit all documentation in `docs/` directory
- [ ] Identify outdated or duplicate content
- [ ] Update main README.md
- [ ] Create developer onboarding guide
- [ ] Write API usage examples
- [ ] Add architecture diagrams
- [ ] Create deployment documentation
- [ ] Setup documentation website (Docusaurus/MkDocs)

## Documentation Structure
```
docs/
├── README.md                 # Main documentation index
├── getting-started/          # Setup and installation
├── api/                      # API documentation
│   ├── rest-api.md
│   ├── graphql-api.md
│   └── websocket-api.md
├── guides/                   # Developer guides
│   ├── development.md
│   ├── testing.md
│   └── deployment.md
├── architecture/             # System design
│   ├── overview.md
│   ├── database-schema.md
│   └── microservices.md
└── troubleshooting/          # Common issues
```

## File Locations
- Documentation: `ToolboxAI-Solutions/docs/`
- README: `ToolboxAI-Solutions/README.md`
- API Specs: `ToolboxAI-Solutions/docs/api/openapi.yaml`
- Diagrams: `ToolboxAI-Solutions/docs/diagrams/`

## Tools
- Markdown linter
- Docusaurus or MkDocs
- Mermaid for diagrams
- OpenAPI/Swagger editor

## Commands
```bash
cd ToolboxAI-Solutions
npm run docs:build        # Build documentation site
npm run docs:serve        # Serve docs locally
npm run docs:lint         # Lint markdown files
npm run docs:api          # Generate API documentation
```
