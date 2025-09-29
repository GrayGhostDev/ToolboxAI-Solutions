# ToolboxAI Roblox Environment - Optimized Structure

## Overview
The Roblox scripts have been consolidated and organized into a modern, maintainable structure following Luau/Roblox best practices.

## Directory Structure

```
roblox/
├── src/                           # Modern Luau source code
│   ├── client/                    # Client-side scripts
│   │   ├── init.client.luau      # Main client entry point
│   │   ├── UI.client.lua         # UI management
│   │   ├── Input.client.lua      # Input handling
│   │   └── CameraController.client.lua # Camera controls
│   ├── server/                    # Server-side scripts
│   │   ├── init.server.luau      # Server entry point
│   │   ├── api/                  # API integration
│   │   │   ├── dashboardApi.lua  # Dashboard API
│   │   │   └── ghostApi.lua      # Ghost backend API
│   │   ├── AuthenticationHandler.lua # Player authentication
│   │   ├── DataStore.lua         # Data persistence
│   │   └── GameManager.lua       # Game session management
│   ├── shared/                    # Shared modules (client + server)
│   │   ├── HTTPClient.lua        # HTTP communication
│   │   ├── NetworkManager.lua    # Network utilities
│   │   ├── ValidationModule.lua  # Data validation
│   │   ├── SecurityValidator.lua # Security checks
│   │   └── QuizSystem.lua        # Quiz functionality
│   ├── Modules/                   # Legacy module compatibility
│   │   └── integration.lua       # Integration module
│   └── Main.server.lua           # Main server script (comprehensive)
├── plugins/                       # Roblox Studio plugins
│   ├── AIContentGenerator.lua    # Primary AI content plugin
│   ├── AIContentGeneratorTest.lua # Plugin testing
│   ├── components/               # Plugin UI components
│   ├── services/                 # Plugin services
│   └── utils/                    # Plugin utilities
├── Config/                        # Configuration files
│   ├── default.project.json      # Rojo project configuration
│   ├── plugin.project.json       # Plugin project config
│   └── settings.lua              # Environment settings
├── tests/                         # Test scripts
│   └── IntegrationTests.lua      # Integration testing
├── environments/                  # Environment configurations
├── modules/                       # Additional modules
├── legacy_scripts/               # Archived legacy structure
│   ├── scripts/                  # Old scripts directory
│   └── API/                      # Old API directory
└── plugins_archive/              # Archived plugin versions
```

## Changes Made

### 1. Consolidated Duplicate Functionality
- **Main.server.lua**: Replaced basic version with comprehensive educational platform script
- **AI Content Generators**: Kept primary version (AIContentGenerator.lua), archived older version
- **Test Scripts**: Consolidated test functionality, kept integration tests

### 2. Organized by Functionality
- **Client Scripts**: All client-side code moved to `src/client/`
- **Server Scripts**: All server-side code moved to `src/server/`
- **Shared Modules**: Common modules moved to `src/shared/`
- **API Integration**: Consolidated API files in `src/server/api/`

### 3. Updated Rojo Configuration
- Removed references to legacy `scripts/` structure
- Updated paths to use modern `src/` structure
- Consolidated module mappings
- Streamlined project tree

### 4. Removed Unused/Duplicate Files
- Legacy Hello.luau example
- Duplicate API structures
- Old script organization
- Obsolete plugin versions

### 5. Archive Structure
- **legacy_scripts/**: Contains old `scripts/` and `API/` directories
- **plugins_archive/**: Contains older plugin versions
- Files preserved for reference but not active in project

## Usage

### Development
1. Use `src/` structure for all new development
2. Follow Luau naming conventions (.luau for new files)
3. Place shared logic in `src/shared/`
4. Use proper client/server separation

### Building with Rojo
```bash
rojo build Config/default.project.json
```

### Plugin Development
- Main plugin: `plugins/AIContentGenerator.lua`
- Test plugin functionality with `plugins/AIContentGeneratorTest.lua`
- Use `plugins/components/` for UI elements

## Key Features

### Main Server Script (`src/Main.server.lua`)
- Comprehensive educational platform management
- Player session handling
- Quiz system integration
- Data persistence
- HTTP API communication
- Security validation

### Shared Modules
- **NetworkManager**: HTTP communication utilities
- **ValidationModule**: Data validation functions
- **SecurityValidator**: Security checks and filtering
- **QuizSystem**: Quiz logic and scoring

### Plugin System
- AI content generation
- Integration testing
- Real-time communication with backend
- Studio UI components

## Migration Notes

If you need to reference old code:
- Legacy scripts are in `legacy_scripts/scripts/`
- Old API files are in `legacy_scripts/API/`
- Archived plugins are in `plugins_archive/`

## Best Practices

1. **Use src/ for all new code**
2. **Follow client/server/shared organization**
3. **Use .luau extension for new Luau files**
4. **Place reusable modules in shared/**
5. **Keep plugins focused and modular**
6. **Test changes with integration tests**

## Dependencies

- Rojo for project management
- Modern Roblox Studio with Luau support
- HTTP service enabled for API communication
- Required services: HttpService, DataStoreService, Players, ReplicatedStorage