#!/bin/bash
# ToolBoxAI Dashboard Docker Startup Script
# Optimized for external drive development

echo "🚀 Starting ToolBoxAI Dashboard..."

cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Clean up any existing containers
docker rm -f toolboxai-dashboard 2>/dev/null

# Start the dashboard container
# Note: This uses a named volume for node_modules to avoid external drive performance issues
docker run -d \
  --name toolboxai-dashboard \
  -p 5179:5173 \
  -e NODE_ENV=development \
  -e DOCKER_ENV=true \
  -e VITE_API_BASE_URL=http://localhost:8009 \
-e VITE_PUSHER_KEY=${VITE_PUSHER_KEY:?set VITE_PUSHER_KEY} \
  -e VITE_PUSHER_CLUSTER=us2 \
  -e VITE_ENABLE_PUSHER=true \
  -e VITE_ENABLE_WEBSOCKET=false \
  -e VITE_ENABLE_CLERK_AUTH=true \
-e VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY:?set VITE_CLERK_PUBLISHABLE_KEY} \
  -v "$(pwd)/apps/dashboard:/app" \
  -v "dashboard_node_modules:/app/node_modules" \
  node:20-alpine \
  sh -c "cd /app && npm install --legacy-peer-deps && npm run dev -- --host 0.0.0.0"

echo "✅ Dashboard container started"
echo ""
echo "📝 Note: The initial npm install will take 5-10 minutes on first run."
echo "    This is normal for external drive development."
echo ""
echo "Monitor logs with: docker logs -f toolboxai-dashboard"
echo "Access dashboard at: http://localhost:5179"