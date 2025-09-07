#!/bin/bash

# Educational Platform Backend Runner Script

echo "🚀 Starting ToolBoxAI Educational Platform Backend..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export ENV="development"
export HOST="0.0.0.0"
export PORT="8001"

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Port $PORT is already in use${NC}"
    echo -e "${YELLOW}Attempting to kill existing process...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start the backend
echo -e "${GREEN}✅ Starting FastAPI server on http://localhost:${PORT}${NC}"
echo -e "${GREEN}📚 API Documentation: http://localhost:${PORT}/api/docs${NC}"
echo -e "${GREEN}🔍 Alternative Docs: http://localhost:${PORT}/api/redoc${NC}"
echo ""

# Run the application
python3 main.py