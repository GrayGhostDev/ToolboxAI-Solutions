# ============================================
# TEAMCITY AGENT - BACKEND BUILD AGENT
# ============================================
# Custom TeamCity agent with Python 3.12 and backend tooling
# For building FastAPI backends and running Python tests
# Updated: 2025-11-13
# ============================================

# Base image: Official TeamCity Agent with sudo support
FROM jetbrains/teamcity-agent:2025.07.3-linux-sudo AS base

# Metadata
LABEL maintainer="ToolBoxAI Solutions <dev@toolboxai.com>"
LABEL description="TeamCity Build Agent - Backend (Python 3.12 + pytest + basedpyright)"
LABEL version="1.0.0"
LABEL teamcity.agent.type="backend"
LABEL teamcity.agent.capabilities="python,pip,pytest,fastapi,basedpyright"

# ============================================
# STAGE 1: Install Python 3.12 and Build Tools
# ============================================
FROM base AS builder

# Switch to root for installation
USER root

# Install Python 3.12 and development tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        curl \
        ca-certificates \
        gnupg \
        build-essential \
        git \
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
    # Create symlinks for python and python3
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    # Install pip for Python 3.12
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    # Verify Python installation
    python --version && \
    python3 --version && \
    pip --version && \
    # Clean up apt cache
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python development and testing tools
RUN pip install --no-cache-dir --upgrade \
        pip \
        setuptools \
        wheel && \
    pip install --no-cache-dir \
        # Testing framework
        pytest==8.3.4 \
        pytest-asyncio==0.24.0 \
        pytest-cov==6.0.0 \
        pytest-xdist==3.6.1 \
        # Type checking (BasedPyright, NOT mypy)
        basedpyright==1.23.1 \
        # Code quality
        black==24.10.0 \
        flake8==7.1.1 \
        isort==5.13.2 \
        # FastAPI and dependencies (for testing)
        fastapi==0.121.1 \
        uvicorn==0.34.0 \
        pydantic==2.10.6 \
        # Database drivers
        asyncpg==0.30.0 \
        sqlalchemy==2.0.36 \
        # Redis
        redis==5.2.1 \
        # Async support
        httpx==0.28.1 \
        aiohttp==3.11.11

# ============================================
# STAGE 2: Configure Agent Environment
# ============================================
FROM builder AS final

# Environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/buildagent/work:$PYTHONPATH

# Create directories for pip cache and virtual environments
RUN mkdir -p /opt/pip-cache /opt/venvs && \
    chmod -R 755 /opt/pip-cache /opt/venvs

# Add agent-specific configuration
RUN mkdir -p /data/teamcity_agent/conf && \
    echo "teamcity.agent.name=Backend-Builder" > /data/teamcity_agent/conf/buildAgent.properties && \
    echo "teamcity.agent.description=Backend build agent with Python 3.12 and testing tools" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.python.version=$(python --version | cut -d' ' -f2)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.pip.version=$(pip --version | cut -d' ' -f2)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.pytest.version=$(pytest --version | cut -d' ' -f2)" >> /data/teamcity_agent/conf/buildAgent.properties && \
    echo "system.basedpyright.installed=true" >> /data/teamcity_agent/conf/buildAgent.properties

# Health check to verify Python and pytest are available
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD python --version && pytest --version && basedpyright --version || exit 1

# Default command (inherited from base image)
# Runs TeamCity agent process
CMD ["/run-services.sh"]
