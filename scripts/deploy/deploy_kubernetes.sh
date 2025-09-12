#!/bin/bash

# ToolBoxAI Kubernetes Deployment Script
# Deploys the entire ToolBoxAI platform to Kubernetes cluster

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE=${NAMESPACE:-toolboxai-production}
ENVIRONMENT=${ENVIRONMENT:-production}
VERSION=${VERSION:-latest}
KUBECONFIG_PATH=${KUBECONFIG:-~/.kube/config}
REGISTRY=${REGISTRY:-ghcr.io/toolboxai-solutions}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check helm (optional but recommended)
    if command -v helm &> /dev/null; then
        log_info "Helm is installed"
    else
        log_warning "Helm is not installed - some features may be limited"
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    kubectl apply -f config/kubernetes/namespace.yaml
    
    # Wait for namespace to be active
    kubectl wait --for=condition=Active namespace/$NAMESPACE --timeout=30s
    
    log_success "Namespace created"
}

# Create secrets
create_secrets() {
    log_info "Creating secrets..."
    
    # Database credentials
    kubectl create secret generic database-credentials \
        --from-literal=url="postgresql://toolboxai_user:${POSTGRES_PASSWORD}@postgres-service:5432/educational_platform" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Redis credentials
    kubectl create secret generic redis-credentials \
        --from-literal=url="redis://:${REDIS_PASSWORD}@redis-service:6379" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Application secrets
    kubectl create secret generic app-secrets \
        --from-literal=jwt-secret="${JWT_SECRET_KEY}" \
        --from-literal=openai-key="${OPENAI_API_KEY}" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Docker registry credentials
    kubectl create secret docker-registry ghcr-credentials \
        --docker-server=ghcr.io \
        --docker-username="${GITHUB_USERNAME}" \
        --docker-password="${GITHUB_TOKEN}" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Secrets created"
}

# Create ConfigMaps
create_configmaps() {
    log_info "Creating ConfigMaps..."
    
    kubectl create configmap app-config \
        --from-literal=environment=$ENVIRONMENT \
        --from-literal=sentry-dsn="${SENTRY_DSN:-}" \
        --from-literal=log-level="${LOG_LEVEL:-INFO}" \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "ConfigMaps created"
}

# Deploy storage
deploy_storage() {
    log_info "Deploying storage resources..."
    
    # Create PersistentVolumeClaims
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-data-pvc
  namespace: $NAMESPACE
spec:
  accessModes:
  - ReadWriteMany
  storageClassName: standard
  resources:
    requests:
      storage: 50Gi
EOF
    
    log_success "Storage resources deployed"
}

# Deploy databases
deploy_databases() {
    log_info "Deploying database services..."
    
    # Deploy PostgreSQL
    kubectl apply -f config/kubernetes/postgres-statefulset.yaml
    
    # Deploy Redis
    kubectl apply -f config/kubernetes/redis-deployment.yaml
    
    # Wait for databases to be ready
    log_info "Waiting for databases to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres --namespace=$NAMESPACE --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis --namespace=$NAMESPACE --timeout=300s
    
    log_success "Database services deployed"
}

# Deploy backend services
deploy_backend() {
    log_info "Deploying backend services..."
    
    # Update image version in deployment
    sed -i.bak "s|image: ghcr.io/toolboxai-solutions/backend:.*|image: $REGISTRY/backend:$VERSION|" \
        config/kubernetes/backend-deployment.yaml
    
    # Apply backend deployment
    kubectl apply -f config/kubernetes/backend-deployment.yaml
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/backend-deployment --namespace=$NAMESPACE --timeout=600s
    
    log_success "Backend services deployed"
}

# Deploy frontend services
deploy_frontend() {
    log_info "Deploying frontend services..."
    
    # Create frontend deployment
    cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deployment
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: $REGISTRY/frontend:$VERSION
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
EOF
    
    # Wait for deployment
    kubectl rollout status deployment/frontend-deployment --namespace=$NAMESPACE --timeout=300s
    
    log_success "Frontend services deployed"
}

# Deploy ingress
deploy_ingress() {
    log_info "Deploying ingress..."
    
    # Install nginx-ingress controller if not present
    if ! kubectl get namespace ingress-nginx &> /dev/null; then
        log_info "Installing nginx-ingress controller..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
        
        # Wait for ingress controller
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s
    fi
    
    # Apply ingress configuration
    kubectl apply -f config/kubernetes/ingress.yaml
    
    log_success "Ingress deployed"
}

# Deploy monitoring
deploy_monitoring() {
    log_info "Deploying monitoring stack..."
    
    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy Prometheus
    cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - $NAMESPACE
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
EOF
    
    log_success "Monitoring stack deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    log_info "Pod Status:"
    kubectl get pods --namespace=$NAMESPACE
    
    # Check service status
    log_info "Service Status:"
    kubectl get services --namespace=$NAMESPACE
    
    # Check ingress status
    log_info "Ingress Status:"
    kubectl get ingress --namespace=$NAMESPACE
    
    # Run health checks
    log_info "Running health checks..."
    
    # Get backend pod
    BACKEND_POD=$(kubectl get pod -l app=backend -n $NAMESPACE -o jsonpath="{.items[0].metadata.name}")
    
    if [ -n "$BACKEND_POD" ]; then
        # Check backend health
        kubectl exec $BACKEND_POD -n $NAMESPACE -- curl -s http://localhost:8008/health || true
    fi
    
    log_success "Deployment verification complete"
}

# Rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    kubectl rollout undo deployment/backend-deployment --namespace=$NAMESPACE
    kubectl rollout undo deployment/frontend-deployment --namespace=$NAMESPACE
    
    log_success "Rollback complete"
}

# Main deployment flow
main() {
    log_info "Starting ToolBoxAI Kubernetes deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Namespace: $NAMESPACE"
    log_info "Version: $VERSION"
    
    # Parse arguments
    case "${1:-deploy}" in
        deploy)
            check_prerequisites
            create_namespace
            create_secrets
            create_configmaps
            deploy_storage
            deploy_databases
            deploy_backend
            deploy_frontend
            deploy_ingress
            deploy_monitoring
            verify_deployment
            
            log_success "Deployment complete!"
            log_info "Access the application at:"
            log_info "  Dashboard: https://dashboard.toolboxai.solutions"
            log_info "  API: https://api.toolboxai.solutions"
            log_info "  Metrics: https://metrics.toolboxai.solutions"
            ;;
        
        rollback)
            rollback_deployment
            ;;
        
        verify)
            verify_deployment
            ;;
        
        delete)
            log_warning "Deleting deployment from namespace: $NAMESPACE"
            kubectl delete namespace $NAMESPACE
            log_success "Deployment deleted"
            ;;
        
        *)
            log_error "Unknown command: $1"
            echo "Usage: $0 [deploy|rollback|verify|delete]"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"