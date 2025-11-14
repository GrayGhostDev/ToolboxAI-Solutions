# ============================================
# TEAMCITY AGENT - FRONTEND BUILD AGENT
# ============================================
# Custom TeamCity agent with Node.js 22 LTS and pnpm 9.15.0
# For building React dashboards and frontend applications
# Updated: 2025-11-13
# ============================================

# Base image: Official TeamCity Agent with sudo support
FROM jetbrains/teamcity-agent:2025.07.3-linux-sudo AS base

# Metadata
LABEL maintainer="ToolBoxAI Solutions <dev@toolboxai.com>"
LABEL description="TeamCity Build Agent - Frontend (Node.js 22 + pnpm 9.15.0)"
LABEL version="1.0.0"
LABEL teamcity.agent.type="frontend"
LABEL teamcity.agent.capabilities="node,npm,pnpm,react,vite,typescript"

# ============================================
# STAGE 1: Install Node.js and Build Tools
# ============================================
FROM base AS builder

# Switch to root for installation
USER root

# Install dependencies and Node.js 22 LTS
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        build-essential \
        git && \
    # Add NodeSource repository for Node.js 22
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    # Install Node.js
    apt-get install -y nodejs && \
    # Verify Node.js installation
    node --version && \
    npm --version && \
    # Clean up apt cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install pnpm globally (version 9.15.0 to match project requirements)
RUN npm install -g pnpm@9.15.0 && \
    pnpm --version && \
    # Configure pnpm global settings
    pnpm config set store-dir /opt/pnpm-store && \
    pnpm config set cache-dir /opt/pnpm-cache

# ============================================
# STAGE 2: Configure Agent Environment
# ============================================
FROM builder AS final

# Environment variables for Node.js and pnpm
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=4096" \
    PNPM_HOME="/root/.local/share/pnpm" \
    PATH="${PATH}:/root/.local/share/pnpm"

# Create directories for pnpm store and cache
RUN mkdir -p /opt/pnpm-store /opt/pnpm-cache && \
    chmod -R 755 /opt/pnpm-store /opt/pnpm-cache

# Add agent-specific configuration
RUN mkdir -p /data/teamcity_agent/conf && \
    echo "teamcity.agent.name=Frontend-Builder" > /data/teamcity_agent/conf/buildAgent.properties && \
    echo "teamcity.agent.description=Frontend build agent with Node.js 22 and pnpm 9.15.0" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.node.version=$(node --version)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.npm.version=$(npm --version)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.pnpm.version=$(pnpm --version)" >> /data/teamcity_agent/conf/buildAgent.properties

# Health check to verify Node.js and pnpm are available
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD node --version && pnpm --version || exit 1

# Default command (inherited from base image)
# Runs TeamCity agent process
CMD ["/run-services.sh"]
