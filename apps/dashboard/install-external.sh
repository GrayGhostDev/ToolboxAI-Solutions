#!/bin/bash

# Dashboard Installation Script for External Drive
# Handles npm installation with --no-bin-links flag for external drive compatibility

echo "🚀 Installing dashboard dependencies on external drive..."
echo "📍 Location: $(pwd)"
echo "💻 Node: $(node --version) | npm: $(npm --version)"
echo ""

# Clean existing installation
if [ -d "node_modules" ]; then
    echo "🧹 Cleaning existing node_modules..."
    rm -rf node_modules
fi

if [ -f "package-lock.json" ]; then
    echo "🗑️  Removing package-lock.json..."
    rm -f package-lock.json
fi

# Install with no-bin-links flag for external drive
echo "📦 Installing packages with --no-bin-links..."
npm install --no-bin-links --verbose

# Check if esbuild needs rebuilding
if ! npm ls esbuild >/dev/null 2>&1; then
    echo "🔨 Rebuilding esbuild for ARM64..."
    npm rebuild esbuild
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "📊 Installation summary:"
npm ls --depth=0

echo ""
echo "🎯 Next steps:"
echo "  1. Run 'npm run dev' to start development server"
echo "  2. Run 'npm run build' to create production build"
echo "  3. Run 'npm run test' to run tests"