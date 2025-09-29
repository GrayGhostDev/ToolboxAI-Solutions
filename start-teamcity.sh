#!/bin/bash
# TeamCity Startup Script with Permission Fixes
# Created: 2025-09-28

echo "🚀 Starting TeamCity Server..."

cd "/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions"

# Ensure data volume exists and has correct permissions
docker volume create teamcity_data 2>/dev/null
docker volume create teamcity_logs 2>/dev/null

# Start TeamCity server WITHOUT the user directive and read-only mount
docker run -d \
  --name teamcity-server \
  -p 8111:8111 \
  -e TEAMCITY_DATABASE_URL="jdbc:postgresql://teamcity-postgres:5432/teamcity" \
  -e TEAMCITY_DATABASE_USER="teamcity" \
  -e TEAMCITY_DATABASE_PASSWORD="teamcity_secure_2025" \
  -e TEAMCITY_SERVER_MEM_OPTS="-Xmx4g -XX:MaxPermSize=512m" \
  -e TEAMCITY_DATA_PATH="/data/teamcity_server/datadir" \
  -e TEAMCITY_LOGS_PATH="/opt/teamcity/logs" \
  -v teamcity_data:/data/teamcity_server/datadir \
  -v teamcity_logs:/opt/teamcity/logs \
  --network compose_teamcity \
  jetbrains/teamcity-server:2025.03

echo "✅ TeamCity server starting..."
echo ""
echo "📝 Notes:"
echo "  - First startup may take 2-3 minutes"
echo "  - Access TeamCity at http://localhost:8111"
echo "  - Default admin account will be created on first access"
echo ""
echo "Monitor logs with: docker logs -f teamcity-server"