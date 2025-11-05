#!/bin/bash

# Vercel Deployment Script for ToolBoxAI Solutions
# This script ensures proper deployment to Vercel

set -e

echo "======================================"
echo "ToolBoxAI Solutions - Vercel Deployment"
echo "======================================"
echo ""

# Navigate to project root
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Check if changes are committed
echo "🔍 Checking git status..."
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  Uncommitted changes detected. Committing..."
    git add -A
    git commit -m "chore: Auto-commit before deployment"
    git push origin main
    echo "✅ Changes committed and pushed"
else
    echo "✅ Working directory clean"
fi
echo ""

# Verify latest commit is pushed
echo "🔍 Verifying remote is up to date..."
git fetch origin
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ $LOCAL != $REMOTE ]; then
    echo "⚠️  Local and remote are out of sync. Pushing..."
    git push origin main
    echo "✅ Pushed to remote"
else
    echo "✅ Local and remote are in sync"
fi
echo ""

# Build the dashboard locally first to verify
echo "🔨 Building dashboard locally..."
cd "$PROJECT_ROOT/apps/dashboard"
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Local build successful"
else
    echo "❌ Local build failed"
    exit 1
fi
echo ""

# Check if Vercel CLI is available
echo "🔍 Checking Vercel CLI..."
if command -v vercel &> /dev/null; then
    VERCEL_CMD="vercel"
    echo "✅ Vercel CLI found: $(which vercel)"
elif command -v npx &> /dev/null; then
    VERCEL_CMD="npx vercel"
    echo "✅ Using npx vercel"
else
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel || npm install --save-dev vercel
    VERCEL_CMD="npx vercel"
fi
echo ""

# Return to project root
cd "$PROJECT_ROOT"

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
echo "Command: $VERCEL_CMD --prod --yes"
echo ""

$VERCEL_CMD --prod --yes

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo "======================================"
    echo ""
    echo "🎉 Your dashboard has been deployed to Vercel"
    echo ""
    echo "Next steps:"
    echo "1. Check your Vercel dashboard for the deployment URL"
    echo "2. Test the deployed site in your browser"
    echo "3. Verify no console errors (F12)"
    echo ""
else
    echo ""
    echo "======================================"
    echo "❌ DEPLOYMENT FAILED"
    echo "======================================"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check your Vercel authentication: vercel login"
    echo "2. Verify project is linked: vercel link"
    echo "3. Check vercel.json configuration"
    echo "4. Review build logs above"
    echo ""
    exit 1
fi

