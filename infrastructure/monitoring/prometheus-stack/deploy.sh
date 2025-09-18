#!/bin/bash
# Deploy Prometheus and Grafana Monitoring Stack for ToolBoxAI

set -e

NAMESPACE="monitoring"
RELEASE_NAME="monitoring"
CHART_VERSION="51.3.0"

echo "🚀 Deploying Prometheus and Grafana Monitoring Stack"
echo "=================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "❌ helm is not installed"
    exit 1
fi

# Check cluster connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Prerequisites satisfied"

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f namespace.yaml

# Add Prometheus community Helm repository
echo "📚 Adding Helm repository..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Create secrets
echo "🔐 Creating secrets..."
kubectl create secret generic monitoring-secrets \
    --from-literal=GRAFANA_SECRET_KEY=$(openssl rand -hex 32) \
    --from-literal=PAGERDUTY_KEY="${PAGERDUTY_KEY:-your-pagerduty-key}" \
    --from-literal=SMTP_PASSWORD="${SMTP_PASSWORD:-your-smtp-password}" \
    --from-literal=SLACK_WEBHOOK="${SLACK_WEBHOOK:-your-slack-webhook}" \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Create Grafana dashboards ConfigMap
echo "📊 Creating Grafana dashboards..."
kubectl create configmap grafana-dashboards \
    --from-file=dashboards/ \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Deploy Prometheus Operator CRDs
echo "🎯 Installing Prometheus Operator CRDs..."
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagerconfigs.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_alertmanagers.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_podmonitors.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_probes.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheuses.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_prometheusrules.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_servicemonitors.yaml
kubectl apply --server-side -f https://raw.githubusercontent.com/prometheus-operator/prometheus-operator/v0.68.0/example/prometheus-operator-crd/monitoring.coreos.com_thanosrulers.yaml

# Install kube-prometheus-stack
echo "📦 Installing kube-prometheus-stack..."
helm upgrade --install ${RELEASE_NAME} \
    prometheus-community/kube-prometheus-stack \
    --namespace ${NAMESPACE} \
    --version ${CHART_VERSION} \
    --values values.yaml \
    --wait \
    --timeout 10m

# Apply custom resources
echo "🎨 Applying custom resources..."
kubectl apply -f prometheus-rules.yaml
kubectl apply -f service-monitors.yaml

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=prometheus \
    -n ${NAMESPACE} \
    --timeout=300s

kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=grafana \
    -n ${NAMESPACE} \
    --timeout=300s

kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=alertmanager \
    -n ${NAMESPACE} \
    --timeout=300s

# Get service information
echo ""
echo "✅ Deployment complete!"
echo "========================"

# Port forward for local access
echo ""
echo "📊 Access Grafana:"
echo "kubectl port-forward -n ${NAMESPACE} svc/monitoring-grafana 3000:80"
echo "URL: http://localhost:3000"
echo "Default credentials: admin / $(kubectl get secret --namespace ${NAMESPACE} monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"

echo ""
echo "🔥 Access Prometheus:"
echo "kubectl port-forward -n ${NAMESPACE} svc/monitoring-kube-prometheus-prometheus 9090:9090"
echo "URL: http://localhost:9090"

echo ""
echo "🚨 Access Alertmanager:"
echo "kubectl port-forward -n ${NAMESPACE} svc/monitoring-kube-prometheus-alertmanager 9093:9093"
echo "URL: http://localhost:9093"

# Verify deployment
echo ""
echo "🔍 Verifying deployment..."
kubectl get pods -n ${NAMESPACE}
kubectl get svc -n ${NAMESPACE}

echo ""
echo "📈 Metrics endpoints available:"
kubectl get servicemonitor -n ${NAMESPACE} -o wide

echo ""
echo "📋 Prometheus rules:"
kubectl get prometheusrule -n ${NAMESPACE}

echo ""
echo "🎉 Monitoring stack deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure ingress for external access"
echo "2. Set up PagerDuty integration with your service key"
echo "3. Configure Slack webhook for alerts"
echo "4. Import additional Grafana dashboards as needed"
echo "5. Fine-tune alert thresholds based on your SLOs"