#!/bin/bash
# Docker Entrypoint Script for ToolBoxAI Dashboard Frontend
# This script handles dependency checking, initialization, and startup

set -e

# Colors for better logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] [DASHBOARD]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] [DASHBOARD]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] [DASHBOARD]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] [DASHBOARD]${NC} $1"
}

# Configuration
BACKEND_URL="${VITE_API_BASE_URL:-http://fastapi-main:8009}"
BACKEND_HEALTH_URL="${BACKEND_URL%/api/v1}/health"
MAX_WAIT_TIME=${BACKEND_WAIT_TIMEOUT:-300}
CHECK_INTERVAL=${BACKEND_CHECK_INTERVAL:-5}
RETRY_COUNT=${STARTUP_RETRY_COUNT:-3}

# Function to check if backend is healthy
check_backend_health() {
    local url="$1"
    local timeout="${2:-10}"

    if command -v curl >/dev/null 2>&1; then
        curl -f -s -m "$timeout" "$url" >/dev/null 2>&1
    elif command -v wget >/dev/null 2>&1; then
        wget --quiet --timeout="$timeout" --tries=1 --spider "$url" >/dev/null 2>&1
    else
        # Fallback to nc if available
        if command -v nc >/dev/null 2>&1; then
            local host port
            host=$(echo "$url" | sed -e 's|^[^/]*//||' -e 's|/.*||' -e 's|:.*||')
            port=$(echo "$url" | sed -e 's|^[^/]*//||' -e 's|/.*||' -e 's|.*:||')
            port=${port:-80}
            nc -z "$host" "$port" >/dev/null 2>&1
        else
            log_error "No HTTP client available (curl, wget, or nc)"
            return 1
        fi
    fi
}

# Function to wait for backend service
wait_for_backend() {
    local start_time=$(date +%s)
    local end_time=$((start_time + MAX_WAIT_TIME))

    log "Waiting for backend service at $BACKEND_HEALTH_URL (timeout: ${MAX_WAIT_TIME}s)"

    while [ $(date +%s) -lt $end_time ]; do
        if check_backend_health "$BACKEND_HEALTH_URL"; then
            log_success "Backend service is healthy and ready"
            return 0
        fi

        local elapsed=$(($(date +%s) - start_time))
        log "Backend not ready yet (${elapsed}s elapsed). Retrying in ${CHECK_INTERVAL}s..."
        sleep "$CHECK_INTERVAL"
    done

    log_error "Backend service failed to become ready within ${MAX_WAIT_TIME}s"
    return 1
}

# Function to validate environment variables
validate_environment() {
    local required_vars=(
        "VITE_API_BASE_URL"
        "VITE_PUSHER_KEY"
        "VITE_PUSHER_CLUSTER"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done

        # For development, provide warnings instead of failures
        if [ "$NODE_ENV" = "development" ]; then
            log_warn "Development mode: continuing with missing variables"
            return 0
        else
            return 1
        fi
    fi

    log_success "Environment variables validated successfully"
    return 0
}

# Function to setup application directories
setup_directories() {
    local dirs=(
        "/app/logs"
        "/app/tmp"
        "/app/cache"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
}

# Function to clear caches if needed
clear_caches() {
    if [ "$CLEAR_CACHE_ON_START" = "true" ]; then
        log "Clearing application caches..."

        # Clear Vite cache
        if [ -d "node_modules/.vite" ]; then
            rm -rf "node_modules/.vite"
            log "Cleared Vite cache"
        fi

        # Clear application cache directory
        if [ -d "/app/cache" ]; then
            rm -rf "/app/cache"/*
            log "Cleared application cache"
        fi
    fi
}

# Function to check database connectivity through backend
check_database_connectivity() {
    local db_check_url="${BACKEND_URL%/api/v1}/health/database"

    log "Checking database connectivity through backend..."

    if check_backend_health "$db_check_url"; then
        log_success "Database connectivity confirmed"
        return 0
    else
        log_warn "Database connectivity check failed (this may be normal if backend doesn't expose /health/database)"
        return 0  # Don't fail startup for this
    fi
}

# Function to verify authentication setup
verify_auth_setup() {
    if [ -n "$VITE_CLERK_PUBLISHABLE_KEY" ]; then
        log "Clerk authentication configured"
    else
        log_warn "Clerk authentication not configured"
    fi

    # Check if Pusher is configured for realtime features
    if [ -n "$VITE_PUSHER_KEY" ] && [ -n "$VITE_PUSHER_CLUSTER" ]; then
        log_success "Pusher realtime configuration found"
    else
        log_warn "Pusher realtime configuration incomplete"
    fi
}

# Function to run pre-startup checks
run_startup_checks() {
    log "Running pre-startup checks..."

    # Check Node.js version
    local node_version=$(node --version)
    log "Node.js version: $node_version"

    # Check if package.json exists
    if [ ! -f "package.json" ]; then
        log_error "package.json not found in /app"
        return 1
    fi

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_error "node_modules not found. Dependencies may not be installed."
        return 1
    fi

    # Check if Vite is available
    if [ ! -f "node_modules/.bin/vite" ]; then
        log_error "Vite executable not found in node_modules/.bin/"
        return 1
    fi

    log_success "Pre-startup checks completed"
    return 0
}

# Function to start the application with retry logic
start_application() {
    local attempt=1

    while [ $attempt -le $RETRY_COUNT ]; do
        log "Starting application (attempt $attempt/$RETRY_COUNT)..."

        # Determine which Vite config to use
        local vite_config=""
        if [ "$VITE_USE_DOCKER_CONFIG" = "true" ]; then
            vite_config="--config vite.config.docker.ts"
            log "Using Docker-specific Vite configuration"
        fi

        # Start the Vite dev server
        if npm run dev -- --host 0.0.0.0 --port 5179 $vite_config; then
            log_success "Application started successfully"
            return 0
        else
            log_error "Application failed to start (attempt $attempt/$RETRY_COUNT)"

            if [ $attempt -lt $RETRY_COUNT ]; then
                log "Retrying in 10 seconds..."
                sleep 10
            fi

            attempt=$((attempt + 1))
        fi
    done

    log_error "Application failed to start after $RETRY_COUNT attempts"
    return 1
}

# Function to handle graceful shutdown
cleanup() {
    log "Received shutdown signal, cleaning up..."

    # Kill any background processes
    if [ -n "$VITE_PID" ]; then
        kill "$VITE_PID" 2>/dev/null || true
    fi

    log "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup TERM INT

# Main execution
main() {
    log "============================================"
    log "ToolBoxAI Dashboard Frontend Starting..."
    log "============================================"

    log "Environment: ${NODE_ENV:-development}"
    log "Backend URL: $BACKEND_URL"
    log "Pusher Cluster: ${VITE_PUSHER_CLUSTER:-not set}"
    log "Docker Mode: ${DOCKER_ENV:-false}"

    # Run all initialization steps
    local steps=(
        "validate_environment"
        "setup_directories"
        "clear_caches"
        "run_startup_checks"
        "wait_for_backend"
        "check_database_connectivity"
        "verify_auth_setup"
    )

    for step in "${steps[@]}"; do
        if ! $step; then
            log_error "Initialization step failed: $step"
            exit 1
        fi
    done

    log_success "All initialization checks passed"
    log "============================================"

    # Start the application
    if start_application; then
        log_success "Dashboard frontend is running successfully"

        # Keep the script running and handle signals
        wait
    else
        log_error "Failed to start dashboard frontend"
        exit 1
    fi
}

# Execute main function if script is run directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi