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
  -e VITE_PUSHER_KEY=73f059a21bb304c7d68c \
  -e VITE_PUSHER_CLUSTER=us2 \
  -e VITE_ENABLE_PUSHER=true \
  -e VITE_ENABLE_WEBSOCKET=false \
  -e VITE_ENABLE_CLERK_AUTH=true \
  -e VITE_CLERK_PUBLISHABLE_KEY=pk_test_Y2FzdWFsLWZpcmVmbHktMzkuY2xlcmsuYWNjb3VudHMuZGV2JA \
  -v "$(pwd)/apps/dashboard:/app" \
  node:20-alpine \
  sh -c "cd /app && npm install --no-bin-links --legacy-peer-deps && npm run dev"

echo "Dashboard container starting..."
sleep 3
docker ps | grep dashboard