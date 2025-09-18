#!/bin/bash
# Deploy ArgoCD for GitOps - ToolBoxAI Solutions

set -e

NAMESPACE="argocd"
RELEASE_NAME="argocd"
CHART_VERSION="5.51.6"

echo "🚀 Deploying ArgoCD for GitOps"
echo "=============================="

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

# Add ArgoCD Helm repository
echo "📚 Adding Helm repository..."
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Create secrets
echo "🔐 Creating secrets..."

# Generate admin password
ARGOCD_ADMIN_PASSWORD=$(openssl rand -base64 32)
BCRYPT_HASH=$(htpasswd -bnBC 10 "" ${ARGOCD_ADMIN_PASSWORD} | tr -d ':\n')

# Create secret for admin password
kubectl create secret generic argocd-initial-admin-secret \
    --from-literal=password=${BCRYPT_HASH} \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Create repository credentials
kubectl create secret generic repo-creds \
    --from-literal=username="${GITHUB_USERNAME:-github-user}" \
    --from-literal=password="${GITHUB_TOKEN:-your-github-token}" \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Create notification secrets
kubectl create secret generic argocd-notifications-secret \
    --from-literal=slack-token="${SLACK_TOKEN:-your-slack-token}" \
    --from-literal=email-username="${EMAIL_USERNAME:-argocd@toolboxai.solutions}" \
    --from-literal=email-password="${EMAIL_PASSWORD:-your-email-password}" \
    --namespace=${NAMESPACE} \
    --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
echo "📦 Installing ArgoCD..."
helm upgrade --install ${RELEASE_NAME} argo/argo-cd \
    --namespace ${NAMESPACE} \
    --version ${CHART_VERSION} \
    --values values.yaml \
    --wait \
    --timeout 10m

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=argocd-server \
    -n ${NAMESPACE} \
    --timeout=300s

kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=argocd-repo-server \
    -n ${NAMESPACE} \
    --timeout=300s

kubectl wait --for=condition=ready pod \
    -l app.kubernetes.io/name=argocd-application-controller \
    -n ${NAMESPACE} \
    --timeout=300s

# Install ArgoCD CLI
echo "🔧 Installing ArgoCD CLI..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    brew install argocd || true
else
    curl -sSL -o /tmp/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    sudo install -m 755 /tmp/argocd /usr/local/bin/argocd
    rm /tmp/argocd
fi

# Apply App of Apps
echo "📱 Applying App of Apps pattern..."
kubectl apply -f ../apps/app-of-apps.yaml

# Apply ApplicationSets
echo "🎯 Applying ApplicationSets..."
kubectl apply -f ../apps/applicationset.yaml

# Configure RBAC
echo "🔐 Configuring RBAC..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:admin, applications, *, */*, allow
    p, role:admin, clusters, *, *, allow
    p, role:admin, repositories, *, *, allow
    p, role:developer, applications, *, dev/*, allow
    p, role:developer, applications, *, staging/*, allow
    p, role:developer, applications, get, prod/*, allow
    p, role:readonly, applications, get, */*, allow
    g, toolboxai:admins, role:admin
    g, toolboxai:developers, role:developer
    g, authenticated, role:readonly
  policy.default: role:readonly
EOF

# Create ingress
echo "🌐 Creating ingress..."
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/backend-protocol: HTTPS
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - argocd.toolboxai.solutions
      secretName: argocd-server-tls
  rules:
    - host: argocd.toolboxai.solutions
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
EOF

# Get service information
echo ""
echo "✅ ArgoCD deployment complete!"
echo "==============================="

# Port forward for local access
echo ""
echo "🌐 Access ArgoCD UI:"
echo "kubectl port-forward -n ${NAMESPACE} svc/argocd-server 8080:443"
echo "URL: https://localhost:8080"
echo ""
echo "Username: admin"
echo "Password: ${ARGOCD_ADMIN_PASSWORD}"
echo ""
echo "⚠️  Save this password securely! It won't be shown again."

# Save credentials to file
echo "admin:${ARGOCD_ADMIN_PASSWORD}" > argocd-credentials.txt
chmod 600 argocd-credentials.txt
echo ""
echo "Credentials saved to: argocd-credentials.txt"

# ArgoCD CLI login
echo ""
echo "🔑 Login with ArgoCD CLI:"
echo "argocd login localhost:8080 --username admin --password '${ARGOCD_ADMIN_PASSWORD}' --insecure"

# Verify deployment
echo ""
echo "🔍 Verifying deployment..."
kubectl get pods -n ${NAMESPACE}
kubectl get svc -n ${NAMESPACE}

echo ""
echo "📊 Applications:"
kubectl get applications -n ${NAMESPACE}

echo ""
echo "📋 Application Sets:"
kubectl get applicationsets -n ${NAMESPACE}

echo ""
echo "🎉 ArgoCD GitOps platform deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Access the ArgoCD UI at https://argocd.toolboxai.solutions"
echo "2. Configure GitHub webhook for automatic syncing"
echo "3. Add your applications to the App of Apps"
echo "4. Configure SSO with your identity provider"
echo "5. Set up notifications for Slack/Email"
echo ""
echo "GitHub Webhook URL: https://argocd.toolboxai.solutions/api/webhook"
echo "GitHub Webhook Secret: Use the value from GITHUB_TOKEN environment variable"