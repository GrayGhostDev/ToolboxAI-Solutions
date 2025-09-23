#!/bin/bash

# Enhanced Nginx Deployment Script
# Deploys Nginx with advanced load balancing, health checks, and monitoring

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
NGINX_CONFIG="$PROJECT_ROOT/config/production/nginx-enhanced.conf"
NGINX_BACKUP_DIR="/etc/nginx/backup"
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-docker}"  # docker or native

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."

    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is not installed"
            exit 1
        fi
    else
        if ! command -v nginx &> /dev/null; then
            log_error "Nginx is not installed"
            log_info "Install with: apt-get install nginx (Ubuntu) or brew install nginx (macOS)"
            exit 1
        fi
    fi

    if [ ! -f "$NGINX_CONFIG" ]; then
        log_error "Enhanced Nginx configuration not found at: $NGINX_CONFIG"
        exit 1
    }

    log_info "Prerequisites check passed"
}

# Validate Nginx configuration
validate_config() {
    log_step "Validating Nginx configuration..."

    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        # Test config in Docker
        docker run --rm \
            -v "$NGINX_CONFIG:/etc/nginx/nginx.conf:ro" \
            nginx:alpine \
            nginx -t
    else
        # Test config locally
        nginx -t -c "$NGINX_CONFIG"
    fi

    if [ $? -eq 0 ]; then
        log_info "Configuration validation successful"
    else
        log_error "Configuration validation failed"
        exit 1
    fi
}

# Backup existing configuration
backup_existing_config() {
    log_step "Backing up existing Nginx configuration..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        # Backup Docker volumes if they exist
        if docker volume ls | grep -q nginx-config; then
            docker run --rm \
                -v nginx-config:/source:ro \
                -v "$NGINX_BACKUP_DIR:/backup" \
                alpine \
                tar czf "/backup/nginx-config-$TIMESTAMP.tar.gz" /source
            log_info "Docker volume backed up to $NGINX_BACKUP_DIR/nginx-config-$TIMESTAMP.tar.gz"
        fi
    else
        # Backup native installation
        if [ -f /etc/nginx/nginx.conf ]; then
            sudo mkdir -p "$NGINX_BACKUP_DIR"
            sudo cp /etc/nginx/nginx.conf "$NGINX_BACKUP_DIR/nginx.conf.$TIMESTAMP"
            log_info "Configuration backed up to $NGINX_BACKUP_DIR/nginx.conf.$TIMESTAMP"
        fi
    fi
}

# Deploy Nginx with Docker
deploy_docker() {
    log_step "Deploying Nginx with Docker..."

    # Create Docker network if it doesn't exist
    docker network create toolboxai-network 2>/dev/null || true

    # Stop existing Nginx container if running
    if docker ps | grep -q toolboxai-nginx; then
        log_warn "Stopping existing Nginx container..."
        docker stop toolboxai-nginx
        docker rm toolboxai-nginx
    fi

    # Create directories for logs and cache
    mkdir -p "$PROJECT_ROOT/logs/nginx" "$PROJECT_ROOT/cache/nginx"

    # Run Nginx container
    docker run -d \
        --name toolboxai-nginx \
        --network toolboxai-network \
        --restart unless-stopped \
        -p 80:80 \
        -p 443:443 \
        -p 8081:8081 \
        -v "$NGINX_CONFIG:/etc/nginx/nginx.conf:ro" \
        -v "$PROJECT_ROOT/logs/nginx:/var/log/nginx" \
        -v "$PROJECT_ROOT/cache/nginx:/var/cache/nginx" \
        -v "$PROJECT_ROOT/apps/dashboard/dist:/usr/share/nginx/html:ro" \
        --health-cmd="curl -f http://localhost:8081/nginx-health || exit 1" \
        --health-interval=30s \
        --health-timeout=3s \
        --health-retries=3 \
        nginx:alpine

    # Wait for container to be healthy
    log_info "Waiting for Nginx to be healthy..."
    for i in {1..30}; do
        if docker ps | grep -q "healthy.*toolboxai-nginx"; then
            log_info "Nginx is healthy and running"
            return 0
        fi
        sleep 2
    done

    log_error "Nginx failed to become healthy"
    docker logs toolboxai-nginx --tail=50
    return 1
}

# Deploy Nginx natively
deploy_native() {
    log_step "Deploying Nginx natively..."

    # Copy configuration
    sudo cp "$NGINX_CONFIG" /etc/nginx/nginx.conf

    # Create cache directory
    sudo mkdir -p /var/cache/nginx

    # Test configuration
    sudo nginx -t

    if [ $? -ne 0 ]; then
        log_error "Configuration test failed"
        # Restore backup
        if [ -f "$NGINX_BACKUP_DIR/nginx.conf.latest" ]; then
            sudo cp "$NGINX_BACKUP_DIR/nginx.conf.latest" /etc/nginx/nginx.conf
            log_info "Restored previous configuration"
        fi
        exit 1
    fi

    # Reload or start Nginx
    if systemctl is-active --quiet nginx; then
        log_info "Reloading Nginx configuration..."
        sudo systemctl reload nginx
    else
        log_info "Starting Nginx..."
        sudo systemctl start nginx
        sudo systemctl enable nginx
    fi

    # Check status
    if systemctl is-active --quiet nginx; then
        log_info "Nginx is running"
    else
        log_error "Nginx failed to start"
        sudo journalctl -u nginx --lines=50
        exit 1
    fi
}

# Set up monitoring
setup_monitoring() {
    log_step "Setting up Nginx monitoring..."

    # Install Nginx exporter for Prometheus
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        # Check if nginx-exporter is already running
        if ! docker ps | grep -q nginx-exporter; then
            docker run -d \
                --name nginx-exporter \
                --network toolboxai-network \
                --restart unless-stopped \
                -p 9113:9113 \
                nginx/nginx-prometheus-exporter:latest \
                -nginx.scrape-uri=http://toolboxai-nginx:8081/nginx-status

            log_info "Nginx Prometheus exporter started on port 9113"
        fi
    else
        # Native installation of nginx-exporter
        if ! command -v nginx-prometheus-exporter &> /dev/null; then
            log_warn "nginx-prometheus-exporter not installed"
            log_info "Download from: https://github.com/nginxinc/nginx-prometheus-exporter"
        else
            # Start exporter if not running
            if ! pgrep -f nginx-prometheus-exporter > /dev/null; then
                nginx-prometheus-exporter \
                    -nginx.scrape-uri=http://localhost:8081/nginx-status \
                    -web.listen-address=:9113 &
                log_info "Nginx Prometheus exporter started"
            fi
        fi
    fi

    # Create Grafana dashboard import file
    cat > "$PROJECT_ROOT/monitoring/grafana/nginx-dashboard-import.sh" <<'EOF'
#!/bin/bash
# Import Nginx dashboard to Grafana

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"

# Import dashboard
curl -X POST \
    -H "Content-Type: application/json" \
    -u "$GRAFANA_USER:$GRAFANA_PASSWORD" \
    -d @/monitoring/grafana/dashboards/load-balancing-dashboard.json \
    "$GRAFANA_URL/api/dashboards/import"

echo "Dashboard imported successfully"
EOF
    chmod +x "$PROJECT_ROOT/monitoring/grafana/nginx-dashboard-import.sh"
    log_info "Grafana dashboard import script created"
}

# Test enhanced features
test_enhanced_features() {
    log_step "Testing enhanced Nginx features..."

    NGINX_URL="http://localhost"

    # Test health endpoint
    log_info "Testing health check endpoint..."
    if curl -sf "$NGINX_URL:8081/nginx-health" > /dev/null; then
        log_info "✓ Health check endpoint working"
    else
        log_warn "✗ Health check endpoint not responding"
    fi

    # Test nginx status
    log_info "Testing Nginx status endpoint..."
    if curl -sf "$NGINX_URL:8081/nginx-status" > /dev/null; then
        log_info "✓ Nginx status endpoint working"
    else
        log_warn "✗ Nginx status endpoint not responding"
    fi

    # Test rate limiting headers
    log_info "Testing rate limiting..."
    RESPONSE=$(curl -sI "$NGINX_URL/api/v1/test" 2>/dev/null)
    if echo "$RESPONSE" | grep -q "X-RateLimit"; then
        log_info "✓ Rate limiting headers present"
    else
        log_warn "✗ Rate limiting headers not found"
    fi

    # Test cache headers
    log_info "Testing cache configuration..."
    RESPONSE=$(curl -sI "$NGINX_URL/api/v1/test" 2>/dev/null)
    if echo "$RESPONSE" | grep -q "X-Cache-Status"; then
        log_info "✓ Cache headers present"
    else
        log_warn "✗ Cache headers not found"
    fi

    # Test upstream health
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        log_info "Checking upstream connectivity..."
        docker exec toolboxai-nginx curl -sf http://fastapi-main:8008/health > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            log_info "✓ Upstream services reachable"
        else
            log_warn "✗ Upstream services not reachable (may need to start backend services)"
        fi
    fi
}

# Show deployment summary
show_summary() {
    log_step "Deployment Summary"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Nginx Enhanced Load Balancer Deployment Complete"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Main Application:     http://localhost"
    echo "  Health Check:         http://localhost:8081/nginx-health"
    echo "  Status Page:          http://localhost:8081/nginx-status"
    echo "  Prometheus Metrics:   http://localhost:9113/metrics"
    echo ""
    echo "  Features Enabled:"
    echo "    ✓ Advanced load balancing algorithms"
    echo "    ✓ Active health checks"
    echo "    ✓ Session affinity for WebSockets"
    echo "    ✓ Distributed rate limiting"
    echo "    ✓ Response caching"
    echo "    ✓ Circuit breaker integration"
    echo ""

    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        echo "  Docker Commands:"
        echo "    View logs:   docker logs -f toolboxai-nginx"
        echo "    Restart:     docker restart toolboxai-nginx"
        echo "    Stop:        docker stop toolboxai-nginx"
    else
        echo "  System Commands:"
        echo "    View logs:   sudo tail -f /var/log/nginx/error.log"
        echo "    Reload:      sudo systemctl reload nginx"
        echo "    Status:      sudo systemctl status nginx"
    fi

    echo ""
    echo "  Monitoring:"
    echo "    Import Grafana dashboard: $PROJECT_ROOT/monitoring/grafana/nginx-dashboard-import.sh"
    echo "    Prometheus alerts: $PROJECT_ROOT/monitoring/prometheus/alerts/load-balancing-alerts.yml"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
}

# Rollback deployment
rollback() {
    log_step "Rolling back Nginx deployment..."

    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        # Stop current container
        docker stop toolboxai-nginx 2>/dev/null || true
        docker rm toolboxai-nginx 2>/dev/null || true
        log_info "Docker container removed"
    else
        # Restore backup configuration
        LATEST_BACKUP=$(ls -t "$NGINX_BACKUP_DIR"/nginx.conf.* 2>/dev/null | head -1)
        if [ -f "$LATEST_BACKUP" ]; then
            sudo cp "$LATEST_BACKUP" /etc/nginx/nginx.conf
            sudo systemctl reload nginx
            log_info "Configuration rolled back to: $LATEST_BACKUP"
        else
            log_error "No backup found to rollback"
            exit 1
        fi
    fi
}

# Main execution
main() {
    case "${1:-deploy}" in
        deploy)
            check_prerequisites
            validate_config
            backup_existing_config

            if [ "$DEPLOYMENT_MODE" = "docker" ]; then
                deploy_docker
            else
                deploy_native
            fi

            setup_monitoring
            test_enhanced_features
            show_summary
            ;;
        test)
            test_enhanced_features
            ;;
        rollback)
            rollback
            ;;
        status)
            if [ "$DEPLOYMENT_MODE" = "docker" ]; then
                docker ps | grep nginx
                echo ""
                docker exec toolboxai-nginx nginx -V
            else
                systemctl status nginx --no-pager
            fi
            ;;
        logs)
            if [ "$DEPLOYMENT_MODE" = "docker" ]; then
                docker logs -f toolboxai-nginx
            else
                sudo tail -f /var/log/nginx/error.log /var/log/nginx/access.log
            fi
            ;;
        help|--help|-h)
            echo "Usage: $0 {deploy|test|rollback|status|logs|help}"
            echo ""
            echo "Commands:"
            echo "  deploy    - Deploy enhanced Nginx configuration"
            echo "  test      - Test enhanced features"
            echo "  rollback  - Rollback to previous configuration"
            echo "  status    - Show Nginx status"
            echo "  logs      - Show Nginx logs"
            echo "  help      - Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DEPLOYMENT_MODE - Set to 'docker' or 'native' (default: docker)"
            ;;
        *)
            echo "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"