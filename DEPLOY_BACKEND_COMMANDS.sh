#!/bin/bash
# Backend Deployment Commands - Ready to Execute
# Generated: January 15, 2025

set -e  # Exit on error

echo "🚀 ToolBoxAI Backend Deployment Script"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="toolboxai-backend"
BACKEND_URL="https://toolboxai-backend.onrender.com"
VERCEL_URL="https://toolbox-production-final-i38crpr94-grayghostdevs-projects.vercel.app"

echo -e "${YELLOW}Step 1: Authenticate with Render${NC}"
echo "Running: render login"
echo ""
render login
echo ""

echo -e "${GREEN}✓ Authentication complete${NC}"
echo ""

echo -e "${YELLOW}Step 2: Verify Service Exists${NC}"
echo "Checking if $SERVICE_NAME exists..."
echo ""
render services list -o json | grep -q "$SERVICE_NAME" && echo -e "${GREEN}✓ Service found${NC}" || echo -e "${RED}✗ Service not found - create it first${NC}"
echo ""

echo -e "${YELLOW}Step 3: Configure Environment Variables${NC}"
echo "Setting up environment variables..."
echo ""

# Generated Security Keys
echo "Setting JWT_SECRET_KEY..."
render env set JWT_SECRET_KEY="d1842450fccdf9d6e0ee11c1b5b0d5d696ec7285a714ee6a783e7a0a17ee9979" --service "$SERVICE_NAME"

echo "Setting JWT_REFRESH_SECRET_KEY..."
render env set JWT_REFRESH_SECRET_KEY="94102bae4fd0e5147771c67a7725d473f50629cafb50951f6db37ee5e0b8d959" --service "$SERVICE_NAME"

echo "Setting SECRET_KEY..."
render env set SECRET_KEY="b7d5a4f43a37de6fee61786a241366c2329252696857cc049a49d9f528221242" --service "$SERVICE_NAME"

# Pusher Credentials (provided by user)
echo "Setting PUSHER_APP_ID..."
render env set PUSHER_APP_ID="2050003" --service "$SERVICE_NAME"

echo "Setting PUSHER_KEY..."
render env set PUSHER_KEY="73f059a21bb304c7d68c" --service "$SERVICE_NAME"

echo "Setting PUSHER_SECRET..."
render env set PUSHER_SECRET="fe8d15d3d7ee36652b7a" --service "$SERVICE_NAME"

echo "Setting PUSHER_CLUSTER..."
render env set PUSHER_CLUSTER="us2" --service "$SERVICE_NAME"

# CORS Configuration
echo "Setting ALLOWED_ORIGINS..."
render env set ALLOWED_ORIGINS="https://toolboxai-dashboard.onrender.com,$VERCEL_URL,https://toolboxai.vercel.app" --service "$SERVICE_NAME"

echo ""
echo -e "${GREEN}✓ Environment variables configured${NC}"
echo ""

# Check if user has OpenAI API key
echo -e "${YELLOW}Step 4: OpenAI API Key (Required)${NC}"
echo "Please enter your OpenAI API key (or press Enter to skip and set later):"
read -r OPENAI_KEY

if [ -n "$OPENAI_KEY" ]; then
  echo "Setting OPENAI_API_KEY..."
  render env set OPENAI_API_KEY="$OPENAI_KEY" --service "$SERVICE_NAME"
  echo -e "${GREEN}✓ OpenAI API key configured${NC}"
else
  echo -e "${YELLOW}⚠ Skipping OpenAI API key - you must set this later for AI features${NC}"
fi
echo ""

echo -e "${YELLOW}Step 5: Deploy Backend${NC}"
echo "Triggering deployment for $SERVICE_NAME..."
echo ""
render deploy --service "$SERVICE_NAME"

echo ""
echo -e "${GREEN}✓ Deployment triggered${NC}"
echo ""

echo -e "${YELLOW}Step 6: Monitor Deployment${NC}"
echo "Watching logs... (Press Ctrl+C to exit)"
echo ""
render logs "$SERVICE_NAME" --tail

echo ""
echo -e "${GREEN}✓ Deployment monitoring started${NC}"
echo ""

echo "======================================"
echo -e "${GREEN}🎉 Deployment commands executed!${NC}"
echo ""
echo "Next steps:"
echo "1. Wait for deployment to complete (3-5 minutes)"
echo "2. Test health endpoint: curl $BACKEND_URL/health"
echo "3. Update Vercel frontend configuration"
echo "4. Test full authentication flow"
echo ""
