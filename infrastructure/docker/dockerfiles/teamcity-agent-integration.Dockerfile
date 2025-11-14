# ============================================
# TEAMCITY AGENT - INTEGRATION TEST AGENT
# ============================================
# Custom TeamCity agent with Node.js 22 + Python 3.12
# For full-stack integration testing and E2E tests
# Updated: 2025-11-13
# ============================================

# Base image: Official TeamCity Agent with sudo support
FROM jetbrains/teamcity-agent:2025.07.3-linux-sudo AS base

# Metadata
LABEL maintainer="ToolBoxAI Solutions <dev@toolboxai.com>"
LABEL description="TeamCity Build Agent - Integration (Node.js 22 + Python 3.12 + testing tools)"
LABEL version="1.0.0"
LABEL teamcity.agent.type="integration"
LABEL teamcity.agent.capabilities="node,npm,pnpm,python,pytest,playwright,integration-tests"

# ============================================
# STAGE 1: Install Node.js 22
# ============================================
FROM base AS nodejs-stage

USER root

# Install Node.js 22 LTS
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
    # Install pnpm globally (version 9.15.0)
    npm install -g pnpm@9.15.0 && \
    pnpm --version && \
    # Configure pnpm
    pnpm config set store-dir /opt/pnpm-store && \
    pnpm config set cache-dir /opt/pnpm-cache && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ============================================
# STAGE 2: Install Python 3.12
# ============================================
FROM nodejs-stage AS python-stage

USER root

# Install Python 3.12 and development tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        python3-dev && \
    # Add deadsnakes PPA for Python 3.12
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    # Install Python 3.12
    apt-get install -y \
        python3.12 \
        python3.12-dev \
        python3.12-venv \
        python3.12-distutils && \
    # Create symlinks
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    # Install pip
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    # Verify
    python --version && \
    pip --version && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ============================================
# STAGE 3: Install Testing Tools
# ============================================
FROM python-stage AS testing-stage

USER root

# Install Python testing and development tools
RUN pip install --no-cache-dir --upgrade \
        pip \
        setuptools \
        wheel && \
    pip install --no-cache-dir \
        # Testing frameworks
        pytest==8.3.4 \
        pytest-asyncio==0.24.0 \
        pytest-cov==6.0.0 \
        pytest-xdist==3.6.1 \
        pytest-mock==3.14.0 \
        # Type checking
        basedpyright==1.23.1 \
        # Code quality
        black==24.10.0 \
        flake8==7.1.1 \
        # FastAPI for integration testing
        fastapi==0.121.1 \
        uvicorn==0.34.0 \
        pydantic==2.10.6 \
        # HTTP clients for testing
        httpx==0.28.1 \
        requests==2.32.3 \
        # Database
        asyncpg==0.30.0 \
        sqlalchemy==2.0.36 \
        # Redis
        redis==5.2.1

# Install Playwright for E2E testing (via pnpm)
RUN pnpm add -g playwright@1.51.1 && \
    playwright install --with-deps chromium firefox webkit

# ============================================
# STAGE 4: Configure Agent Environment
# ============================================
FROM testing-stage AS final

# Environment variables
ENV NODE_ENV=test \
    NODE_OPTIONS="--max-old-space-size=4096" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PNPM_HOME="/root/.local/share/pnpm" \
    PATH="${PATH}:/root/.local/share/pnpm" \
    PYTHONPATH=/opt/buildagent/work:$PYTHONPATH

# Create working directories
RUN mkdir -p \
        /opt/pnpm-store \
        /opt/pnpm-cache \
        /opt/pip-cache \
        /opt/venvs \
        /opt/test-results && \
    chmod -R 755 \
        /opt/pnpm-store \
        /opt/pnpm-cache \
        /opt/pip-cache \
        /opt/venvs \
        /opt/test-results

# Add agent-specific configuration
RUN mkdir -p /data/teamcity_agent/conf && \
    echo "teamcity.agent.name=Integration-Builder" > /data/teamcity_agent/conf/buildAgent.properties && \
    echo "teamcity.agent.description=Integration test agent with Node.js 22 and Python 3.12" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.node.version=$(node --version)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.pnpm.version=$(pnpm --version)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.python.version=$(python --version | cut -d' ' -f2)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.pytest.version=$(pytest --version | cut -d' ' -f2)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.playwright.installed=true" >> /data/teamcity_agent/conf/buildAgent.properties

# Health check to verify all tools are available
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD node --version && \
        pnpm --version && \
        python --version && \
        pytest --version && \
        playwright --version || exit 1

# Default command (inherited from base image)
CMD ["/run-services.sh"]
