#!/bin/bash

# ToolboxAI Roblox Environment - Rojo Integration Setup Script
# Compatible with both VS Code and Cursor

echo "🎮 Setting up Rojo integration for ToolboxAI Roblox Environment..."

# Check if we're in the right directory
if [ ! -f "default.project.json" ]; then
    echo "❌ Error: default.project.json not found. Please run this script from the ToolboxAI-Roblox-Environment directory."
    exit 1
fi

# Install Aftman if not already installed
if ! command -v aftman &> /dev/null; then
    echo "📦 Installing Aftman..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -L https://github.com/LPGhatguy/aftman/releases/latest/download/aftman-macos.zip -o aftman.zip
        unzip aftman.zip
        sudo mv aftman /usr/local/bin/
        rm aftman.zip
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -L https://github.com/LPGhatguy/aftman/releases/latest/download/aftman-linux.zip -o aftman.zip
        unzip aftman.zip
        sudo mv aftman /usr/local/bin/
        rm aftman.zip
    else
        echo "❌ Unsupported OS. Please install Aftman manually from https://github.com/LPGhatguy/aftman"
        exit 1
    fi
fi

# Install Rojo and other tools via Aftman
echo "🔧 Installing Rojo and development tools..."
aftman install

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p .vscode
mkdir -p .cursor
mkdir -p Roblox/RemoteEvents
mkdir -p Roblox/RemoteFunctions

# Set up VS Code/Cursor workspace
echo "⚙️ Setting up workspace configuration..."

# Create launch configuration for debugging
cat > .vscode/launch.json << 'EOF'
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Start Rojo Server",
            "type": "node",
            "request": "launch",
            "program": "${workspaceFolder}/node_modules/.bin/rojo",
            "args": ["serve"],
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}"
        }
    ]
}
EOF

# Create tasks for common Rojo operations
cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Rojo: Start Server",
            "type": "shell",
            "command": "rojo",
            "args": ["serve"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Rojo: Build",
            "type": "shell",
            "command": "rojo",
            "args": ["build", "default.project.json", "--output", "ToolboxAI.rbxl"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        },
        {
            "label": "Rojo: Sourcemap",
            "type": "shell",
            "command": "rojo",
            "args": ["sourcemap", "default.project.json", "--output", "sourcemap.json"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "new"
            },
            "problemMatcher": []
        }
    ]
}
EOF

# Create Cursor-specific configuration
cp .vscode/settings.json .cursor/settings.json

echo "✅ Rojo integration setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Open this folder in VS Code or Cursor"
echo "2. Install the recommended extensions when prompted"
echo "3. Open Roblox Studio"
echo "4. Install the Rojo plugin from the Toolbox"
echo "5. In VS Code/Cursor, use Ctrl+Shift+P and run 'Rojo: Start Server'"
echo "6. In Roblox Studio, click 'Connect' in the Rojo plugin"
echo ""
echo "🎯 Your Roblox files will now sync automatically between your editor and Studio!"
echo ""
echo "📚 Useful commands:"
echo "  - Ctrl+Shift+P -> 'Rojo: Start Server' - Start the sync server"
echo "  - Ctrl+Shift+P -> 'Rojo: Build' - Build a .rbxl file"
echo "  - Ctrl+Shift+P -> 'Rojo: Sourcemap' - Generate sourcemap for debugging"
echo ""
echo "🔧 Configuration files created:"
echo "  - default.project.json (Rojo project configuration)"
echo "  - aftman.toml (Tool versions)"
echo "  - .vscode/settings.json (VS Code settings)"
echo "  - .cursor/settings.json (Cursor settings)"
echo "  - .vscode/extensions.json (Recommended extensions)"
echo "  - .vscode/launch.json (Debug configuration)"
echo "  - .vscode/tasks.json (Build tasks)"
