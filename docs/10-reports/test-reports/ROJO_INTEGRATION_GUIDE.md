# 🎮 Rojo Integration Guide for ToolboxAI Roblox Environment

This guide provides comprehensive instructions for setting up and using Rojo with the ToolboxAI Roblox Environment in both VS Code and Cursor.

## 📋 Prerequisites

- **VS Code** or **Cursor** editor
- **Roblox Studio** (latest version)
- **Node.js** (for Rojo CLI)
- **Git** (for version control)

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
# Navigate to the ToolboxAI-Roblox-Environment directory
cd ToolboxAI-Roblox-Environment

# Run the setup script
./setup_rojo_integration.sh
```

### Option 2: Manual Setup

1. **Install Aftman** (if not already installed):
   ```bash
   # macOS
   curl -L https://github.com/LPGhatguy/aftman/releases/latest/download/aftman-macos.zip -o aftman.zip
   unzip aftman.zip && sudo mv aftman /usr/local/bin/ && rm aftman.zip
   
   # Linux
   curl -L https://github.com/LPGhatguy/aftman/releases/latest/download/aftman-linux.zip -o aftman.zip
   unzip aftman.zip && sudo mv aftman /usr/local/bin/ && rm aftman.zip
   ```

2. **Install Rojo and tools**:
   ```bash
   aftman install
   ```

3. **Install VS Code/Cursor extensions**:
   - Open VS Code/Cursor
   - Install recommended extensions when prompted
   - Or manually install: `rojo-rbx.rojo`, `sumneko.lua`, `johnnymorganz.luau-lsp`

## 🔧 Configuration Files

### `default.project.json`
The main Rojo project configuration that maps your local files to Roblox Studio instances:

```json
{
  "name": "ToolboxAI-Roblox-Environment",
  "servePort": 34872,
  "tree": {
    "$className": "DataModel",
    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "ToolboxAI": { "$path": "src" },
      "API": { "$path": "API" },
      "Config": { "$path": "Config" }
    },
    "ServerScriptService": {
      "$className": "ServerScriptService",
      "ServerScripts": { "$path": "Scripts/ServerScripts" }
    }
  }
}
```

### `aftman.toml`
Tool version management:

```toml
[tools]
rojo = "7.4.0"
selene = "0.25.0"
stylua = "0.19.0"
```

### VS Code/Cursor Settings
- `.vscode/settings.json` - VS Code specific settings
- `.cursor/settings.json` - Cursor specific settings
- Both include Rojo configuration and Lua language support

## 🎯 Usage Instructions

### 1. Start Rojo Server

**In VS Code/Cursor:**
- Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
- Type "Rojo: Start Server"
- Press Enter

**Or via Command Palette:**
- Click the Rojo icon in the bottom status bar
- Click "Start Server"

### 2. Connect Roblox Studio

1. Open Roblox Studio
2. Go to the **Plugins** tab
3. Click **Rojo** (if not installed, install from Toolbox)
4. Click **Connect** in the Rojo plugin window
5. Your files will now sync automatically!

### 3. Development Workflow

1. **Edit files** in VS Code/Cursor
2. **Save changes** (Ctrl+S)
3. **See updates** instantly in Roblox Studio
4. **Test in Studio** by running the game

## 📁 File Structure

```
ToolboxAI-Roblox-Environment/
├── default.project.json          # Rojo project configuration
├── aftman.toml                   # Tool versions
├── .vscode/                      # VS Code configuration
│   ├── settings.json
│   ├── extensions.json
│   ├── launch.json
│   └── tasks.json
├── .cursor/                      # Cursor configuration
│   └── settings.json
├── Roblox/                       # Roblox source files
│   ├── API/                      # → ReplicatedStorage.API
│   ├── Config/                   # → ReplicatedStorage.Config
│   ├── Scripts/                  # → ServerScriptService/StarterPlayerScripts
│   │   ├── ServerScripts/        # → ServerScriptService.ServerScripts
│   │   ├── ClientScripts/        # → StarterPlayerScripts.ClientScripts
│   │   └── ModuleScripts/        # → ReplicatedStorage.Modules
│   ├── RemoteEvents/             # → ReplicatedStorage.RemoteEvents
│   ├── RemoteFunctions/          # → ReplicatedStorage.RemoteFunctions
│   └── src/                      # → ReplicatedStorage.ToolboxAI
└── setup_rojo_integration.sh     # Setup script
```

## 🛠️ Available Commands

### Rojo Commands (via Command Palette)

- **Rojo: Start Server** - Start the sync server
- **Rojo: Stop Server** - Stop the sync server
- **Rojo: Build** - Build a .rbxl file
- **Rojo: Sourcemap** - Generate sourcemap for debugging
- **Rojo: Install Roblox Studio plugin** - Install/update the Studio plugin

### Build Tasks (Ctrl+Shift+P → "Tasks: Run Task")

- **Rojo: Start Server** - Start the sync server
- **Rojo: Build** - Build project to .rbxl file
- **Rojo: Sourcemap** - Generate sourcemap

## 🔍 Troubleshooting

### Common Issues

1. **"Rojo server not found"**
   - Run `aftman install` to install Rojo
   - Restart VS Code/Cursor

2. **"Connection failed"**
   - Check that Roblox Studio is open
   - Verify the Rojo plugin is installed in Studio
   - Try restarting both Studio and the editor

3. **"Files not syncing"**
   - Check the Rojo server is running (status bar should show "Rojo: Connected")
   - Verify the project file path is correct
   - Check for syntax errors in `default.project.json`

4. **"Lua errors in editor"**
   - Install the Lua language server extension
   - Check that Roblox types are loaded (should be automatic)

### Debug Mode

Enable debug logging:
1. Open Command Palette
2. Run "Rojo: Open Menu"
3. Enable "Debug Mode"

### Reset Configuration

If you need to reset the configuration:
```bash
# Remove generated files
rm -rf .vscode/launch.json .vscode/tasks.json
rm -f ToolboxAI.rbxl sourcemap.json

# Re-run setup
./setup_rojo_integration.sh
```

## 📚 Advanced Features

### Custom Build Scripts

You can create custom build scripts in `.vscode/tasks.json`:

```json
{
  "label": "Build for Production",
  "type": "shell",
  "command": "rojo",
  "args": ["build", "default.project.json", "--output", "ToolboxAI-Production.rbxl"],
  "group": "build"
}
```

### Multiple Project Files

For different environments, create multiple project files:
- `default.project.json` - Development
- `production.project.json` - Production
- `testing.project.json` - Testing

### Sourcemap Integration

Generate sourcemaps for debugging:
```bash
rojo sourcemap default.project.json --output sourcemap.json
```

## 🎯 Best Practices

1. **File Naming**
   - Use `.server.lua` for server scripts
   - Use `.client.lua` for client scripts
   - Use `.lua` for module scripts

2. **Project Structure**
   - Keep related files in the same directory
   - Use descriptive folder names
   - Follow Roblox naming conventions

3. **Version Control**
   - Commit `default.project.json` and `aftman.toml`
   - Ignore generated files (`.rbxl`, `sourcemap.json`)
   - Use `.gitignore` to exclude build artifacts

4. **Development Workflow**
   - Always start Rojo server before development
   - Test changes in Roblox Studio frequently
   - Use the build command for sharing builds

## 🔗 Useful Links

- [Rojo Documentation](https://rojo.space/docs/)
- [VS Code Rojo Extension](https://marketplace.visualstudio.com/items?itemName=rojo-rbx.rojo)
- [Aftman Documentation](https://github.com/LPGhatguy/aftman)
- [Roblox Studio Plugin](https://www.roblox.com/library/1391591109/Rojo)

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the Rojo documentation
3. Check the VS Code/Cursor output panel for error messages
4. Ensure all prerequisites are installed correctly

---

**Happy coding with Rojo! 🎮✨**
