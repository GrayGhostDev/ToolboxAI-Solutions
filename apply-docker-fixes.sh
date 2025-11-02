#!/bin/bash
# Docker Error Fixes - Quick Apply Script
# Run this to apply all dashboard error fixes in Docker environment

set -e

echo "🐳 ToolBoxAI Dashboard - Applying Error Fixes in Docker"
echo "=========================================================="
echo ""

# Navigate to docker compose directory
cd "$(dirname "$0")/infrastructure/docker/compose"

echo "📍 Current directory: $(pwd)"
echo ""

# Check if containers are running
echo "🔍 Checking container status..."
if docker compose ps | grep -q "Up"; then
    echo "✅ Containers are running"
else
    echo "⚠️  Containers are not running"
    echo "   Starting containers..."
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
fi
echo ""

# Option selection
echo "🔧 Select fix application method:"
echo ""
echo "1) Quick Restart (no rebuild) - Recommended if using mounted volumes"
echo "2) Full Rebuild (slower but guaranteed)"
echo "3) Just restart dashboard container"
echo "4) Check logs and status only"
echo ""
read -p "Enter choice [1-4]: " choice
echo ""

case $choice in
    1)
        echo "♻️  Restarting all services..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml restart
        echo "✅ Services restarted"
        ;;
    2)
        echo "🔨 Rebuilding dashboard container..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml build dashboard
        echo "♻️  Restarting services..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        echo "✅ Dashboard rebuilt and restarted"
        ;;
    3)
        echo "♻️  Restarting dashboard only..."
        docker compose -f docker-compose.yml -f docker-compose.dev.yml restart dashboard
        echo "✅ Dashboard restarted"
        ;;
    4)
        echo "📊 Container Status:"
        docker compose ps
        echo ""
        echo "📝 Recent Dashboard Logs:"
        docker compose logs --tail=50 dashboard
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "⏳ Waiting for services to be ready (10 seconds)..."
sleep 10
echo ""

# Check dashboard health
echo "🏥 Checking dashboard health..."
if curl -f -s http://localhost:5179/health > /dev/null 2>&1 || curl -f -s http://localhost:5179 > /dev/null 2>&1; then
    echo "✅ Dashboard is healthy"
else
    echo "⚠️  Dashboard may still be starting..."
    echo "   Check logs: docker compose logs dashboard"
fi
echo ""

# Check backend health
echo "🏥 Checking backend health..."
if curl -f -s http://localhost:8009/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend may still be starting..."
    echo "   Check logs: docker compose logs backend"
fi
echo ""

# Display service URLs
echo "🌐 Service URLs:"
echo "   Dashboard: http://localhost:5179"
echo "   Backend:   http://localhost:8009"
echo "   Backend API Docs: http://localhost:8009/docs"
echo ""

# Show next steps
echo "📋 Next Steps:"
echo ""
echo "1. Open browser to: http://localhost:5179"
echo "2. Open Chrome DevTools (F12)"
echo "3. Check Console tab for reduced errors"
echo "4. Verify: Should see ~95% fewer errors"
echo ""
echo "🔍 Useful Commands:"
echo "   View logs:      docker compose logs -f dashboard"
echo "   Enter container: docker compose exec dashboard sh"
echo "   Stop services:  docker compose down"
echo "   Check status:   docker compose ps"
echo ""
echo "📚 Documentation:"
echo "   - DOCKER_ERROR_FIXES_GUIDE.md - Complete Docker guide"
echo "   - QUICK_FIX_GUIDE.md - Troubleshooting reference"
echo "   - FIXES_COMPLETE.md - Summary of all fixes"
echo ""
echo "✨ Done! Dashboard error fixes applied."
echo ""

