#!/bin/bash

# Tailscale VPN Setup for ToolBoxAI Collaboration
# This script configures Tailscale for secure multi-machine access

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Tailscale VPN Setup for ToolBoxAI ===${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check if Tailscale is installed
echo -e "${YELLOW}Checking Tailscale installation...${NC}"

if ! command_exists tailscale; then
    echo -e "${YELLOW}Tailscale not found. Installing...${NC}"

    # macOS installation
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            echo "Installing Tailscale via Homebrew..."
            brew install --cask tailscale
        else
            echo -e "${RED}Homebrew not found. Please install Tailscale manually from:${NC}"
            echo "https://tailscale.com/download/mac"
            exit 1
        fi
    else
        echo -e "${RED}Please install Tailscale for your OS from:${NC}"
        echo "https://tailscale.com/download"
        exit 1
    fi
fi

echo -e "${GREEN}✓ Tailscale is installed${NC}"

# Step 2: Start Tailscale
echo -e "${YELLOW}Starting Tailscale...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # Open Tailscale app on macOS
    if ! pgrep -x "Tailscale" > /dev/null; then
        open -a Tailscale
        echo "Waiting for Tailscale to start..."
        sleep 3
    fi
fi

# Step 3: Check Tailscale status
echo -e "${YELLOW}Checking Tailscale status...${NC}"

if tailscale status >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Tailscale is running${NC}"

    # Get Tailscale IP
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "not connected")

    if [ "$TAILSCALE_IP" != "not connected" ]; then
        echo -e "${GREEN}✓ Connected to Tailscale network${NC}"
        echo -e "  Your Tailscale IP: ${GREEN}${TAILSCALE_IP}${NC}"
    else
        echo -e "${YELLOW}Not connected to Tailscale network${NC}"
        echo ""
        echo "Please log in to Tailscale:"
        echo "1. Click on the Tailscale icon in the menu bar"
        echo "2. Select 'Log in...'"
        echo "3. Follow the authentication process"
        echo ""
        read -p "Press Enter after you've logged in to continue..."

        # Check again
        TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "not connected")
        if [ "$TAILSCALE_IP" != "not connected" ]; then
            echo -e "${GREEN}✓ Successfully connected! IP: ${TAILSCALE_IP}${NC}"
        else
            echo -e "${RED}Failed to connect. Please try again.${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}Tailscale is not running properly${NC}"
    exit 1
fi

# Step 4: Configure Tailscale ACLs for collaboration
echo -e "${YELLOW}Configuring Tailscale for collaboration...${NC}"

# Create ACL configuration file
ACL_CONFIG="${HOME}/.toolboxai-tailscale-acl.json"
cat > "$ACL_CONFIG" << 'EOF'
{
  "acls": [
    {
      "action": "accept",
      "src": ["*"],
      "dst": [
        "*:5432",     // PostgreSQL
        "*:6379",     // Redis
        "*:8009",     // Backend API
        "*:5179",     // Frontend Dashboard
        "*:8384",     // Syncthing Web UI
        "*:22000",    // Syncthing transfers
        "*:9000",     // Collaboration Hub
        "*:3000",     // Grafana
        "*:5555"      // Celery Flower
      ]
    }
  ],
  "tagOwners": {
    "tag:toolboxai": ["autogroup:admin"]
  },
  "hosts": {
    "toolboxai-primary": "100.64.0.1",
    "toolboxai-dev1": "100.64.0.2",
    "toolboxai-dev2": "100.64.0.3"
  }
}
EOF

echo -e "${GREEN}✓ ACL configuration created${NC}"

# Step 5: Set up MagicDNS
echo -e "${YELLOW}Enabling MagicDNS for easy hostname access...${NC}"

# This needs to be done in the Tailscale admin console
echo ""
echo -e "${YELLOW}To enable MagicDNS:${NC}"
echo "1. Go to https://login.tailscale.com/admin/dns"
echo "2. Click 'Enable MagicDNS'"
echo "3. Add 'toolboxai.ts.net' as a search domain"
echo ""

# Step 6: Share services configuration
echo -e "${YELLOW}Creating service sharing configuration...${NC}"

SHARE_CONFIG="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/collaboration/tailscale-services.json"
cat > "$SHARE_CONFIG" << EOF
{
  "services": {
    "postgres": {
      "host": "${TAILSCALE_IP}",
      "port": 5432,
      "description": "PostgreSQL Database"
    },
    "redis": {
      "host": "${TAILSCALE_IP}",
      "port": 6379,
      "description": "Redis Cache"
    },
    "backend": {
      "host": "${TAILSCALE_IP}",
      "port": 8009,
      "description": "FastAPI Backend"
    },
    "frontend": {
      "host": "${TAILSCALE_IP}",
      "port": 5179,
      "description": "React Dashboard"
    },
    "syncthing": {
      "host": "${TAILSCALE_IP}",
      "port": 8384,
      "description": "Syncthing Web UI"
    }
  },
  "machine": {
    "hostname": "$(hostname)",
    "tailscale_ip": "${TAILSCALE_IP}",
    "role": "development"
  }
}
EOF

echo -e "${GREEN}✓ Service configuration created${NC}"

# Step 7: Update environment files
echo -e "${YELLOW}Updating environment configuration...${NC}"

# Update .env.local with Tailscale IP
ENV_LOCAL="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env.local"
if [ -f "$ENV_LOCAL" ]; then
    # Update existing TAILSCALE_IP
    if grep -q "TAILSCALE_IP=" "$ENV_LOCAL"; then
        sed -i '' "s/TAILSCALE_IP=.*/TAILSCALE_IP=${TAILSCALE_IP}/" "$ENV_LOCAL"
    else
        echo "TAILSCALE_IP=${TAILSCALE_IP}" >> "$ENV_LOCAL"
    fi
else
    # Create new .env.local
    cat > "$ENV_LOCAL" << EOF
# Local machine configuration
MACHINE_ID=$(uuidgen | cut -c1-8)
COLLABORATION_MODE=enabled
TAILSCALE_IP=${TAILSCALE_IP}
PRIMARY_HOST=${TAILSCALE_IP}
EOF
fi

echo -e "${GREEN}✓ Environment updated with Tailscale IP${NC}"

# Step 8: Test connectivity
echo -e "${YELLOW}Testing Tailscale connectivity...${NC}"

# Get other machines on the network
echo "Other machines on your Tailscale network:"
tailscale status | grep -v "$(hostname)" | grep -E "100\." || echo "No other machines found"

# Step 9: Create helper script for connecting to services
CONNECT_SCRIPT="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/scripts/collaboration/tailscale-connect.sh"
cat > "$CONNECT_SCRIPT" << 'EOF'
#!/bin/bash

# Connect to ToolBoxAI services via Tailscale

SERVICE=$1
MACHINE=$2

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service> [machine]"
    echo ""
    echo "Available services:"
    echo "  postgres  - PostgreSQL database"
    echo "  redis     - Redis cache"
    echo "  backend   - FastAPI backend"
    echo "  frontend  - React dashboard"
    echo "  syncthing - File synchronization"
    echo ""
    echo "Example: $0 postgres toolboxai-primary"
    exit 1
fi

# Get service configuration
CONFIG_FILE="/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/collaboration/tailscale-services.json"

if [ -z "$MACHINE" ]; then
    # Use local configuration
    HOST=$(jq -r ".services.${SERVICE}.host" "$CONFIG_FILE")
    PORT=$(jq -r ".services.${SERVICE}.port" "$CONFIG_FILE")
else
    # Use remote machine (would need to fetch config from that machine)
    HOST="${MACHINE}"
    case $SERVICE in
        postgres) PORT=5432 ;;
        redis) PORT=6379 ;;
        backend) PORT=8009 ;;
        frontend) PORT=5179 ;;
        syncthing) PORT=8384 ;;
        *) echo "Unknown service: $SERVICE"; exit 1 ;;
    esac
fi

echo "Connecting to $SERVICE at $HOST:$PORT..."

case $SERVICE in
    postgres)
        psql "postgresql://eduplatform:eduplatform2024@${HOST}:${PORT}/educational_platform_dev"
        ;;
    redis)
        redis-cli -h "$HOST" -p "$PORT" -a redis2024
        ;;
    backend|frontend|syncthing)
        open "http://${HOST}:${PORT}"
        ;;
    *)
        echo "Unknown service: $SERVICE"
        exit 1
        ;;
esac
EOF

chmod +x "$CONNECT_SCRIPT"
echo -e "${GREEN}✓ Connection helper script created${NC}"

# Final summary
echo ""
echo -e "${BLUE}=== Tailscale Setup Complete ===${NC}"
echo ""
echo -e "${GREEN}Your Tailscale configuration:${NC}"
echo "  Tailscale IP: ${TAILSCALE_IP}"
echo "  Hostname: $(hostname)"
echo "  Network: $(tailscale status | grep "Tailnet:" | awk '{print $2}' 2>/dev/null || echo "default")"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Share your Tailscale IP with collaborators: ${TAILSCALE_IP}"
echo "2. Have collaborators run this setup script on their machines"
echo "3. Update PRIMARY_HOST in .env.shared with the primary machine's Tailscale IP"
echo ""
echo -e "${BLUE}To connect to services on another machine:${NC}"
echo "  ${CONNECT_SCRIPT} <service> <machine-hostname>"
echo ""
echo -e "${BLUE}To check Tailscale status:${NC}"
echo "  tailscale status"
echo ""
echo -e "${GREEN}Tailscale is ready for collaboration!${NC}"