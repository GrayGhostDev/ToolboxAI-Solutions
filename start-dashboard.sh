#!/bin/bash
# Dashboard startup script

cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Remove any existing container
docker rm -f toolboxai-dashboard 2>/dev/null

# Start dashboard container
docker run -d \
  --name toolboxai-dashboard \
  -p 5179:5179 \
  -e DOCKER_ENV=true \
  -e NODE_ENV=development \
  -e VITE_API_BASE_URL=http://localhost:8009 \
-e VITE_PUSHER_KEY=${VITE_PUSHER_KEY:?set VITE_PUSHER_KEY} \
  -e VITE_PUSHER_CLUSTER=us2 \
  -e VITE_ENABLE_PUSHER=true \
  -e VITE_ENABLE_WEBSOCKET=false \
  -e VITE_ENABLE_CLERK_AUTH=true \
-e VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY:?set VITE_CLERK_PUBLISHABLE_KEY} \
  -v "$(pwd)/apps/dashboard:/app" \
  node:20-alpine \
  sh -c "cd /app && npm install --no-bin-links --legacy-peer-deps && npm run dev"

echo "Dashboard container starting..."
sleep 3
docker ps | grep dashboard