#!/bin/bash
# Import TeamCity configuration from Kotlin DSL

TEAMCITY_URL="http://localhost:8111"
TOKEN="1564674972001227872"
PROJECT_ID="ToolboxAISolutions"

# Copy settings to TeamCity import location
echo "📁 Preparing configuration files..."
docker cp settings.kts teamcity-server:/tmp/settings.kts
docker cp pom.xml teamcity-server:/tmp/pom.xml

echo "✅ Files ready for manual import"
echo ""
echo "Next steps:"
echo "1. Open TeamCity UI: $TEAMCITY_URL"
echo "2. Go to ToolboxAI-Solutions project"
echo "3. Click 'Actions' → 'Import Kotlin DSL'"
echo "4. Select the files from /tmp/"
