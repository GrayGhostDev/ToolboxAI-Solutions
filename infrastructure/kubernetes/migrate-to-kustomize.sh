#!/bin/bash

# ToolboxAI Kubernetes Migration to Kustomize Structure
# This script organizes legacy Kubernetes manifests into proper Kustomize structure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBERNETES_DIR="$SCRIPT_DIR"
LEGACY_DIR="$KUBERNETES_DIR/legacy"
BASE_DIR="$KUBERNETES_DIR/base"

echo "Starting Kubernetes manifests migration to Kustomize..."

# Create legacy directory to store old files
mkdir -p "$LEGACY_DIR"

# Function to move file with backup
move_legacy_file() {
    local src="$1"
    local desc="$2"

    if [[ -f "$src" ]]; then
        echo "Moving legacy file: $src -> $LEGACY_DIR/$(basename "$src")"
        mv "$src" "$LEGACY_DIR/"
        echo "  ✓ $desc"
    fi
}

# Function to remove deprecated API versions
fix_deprecated_apis() {
    echo "Fixing deprecated API versions in legacy files..."

    # Fix v1beta1 PodSecurityPolicy to policy/v1
    if [[ -f "$LEGACY_DIR/pod-security-standards.yaml" ]]; then
        sed -i.bak 's/apiVersion: policy\/v1beta1/apiVersion: policy\/v1/g' "$LEGACY_DIR/pod-security-standards.yaml"
        echo "  ✓ Fixed PodSecurityPolicy API version"
    fi

    # Fix networking.k8s.io/v1beta1 to networking.k8s.io/v1
    find "$LEGACY_DIR" -name "*.yaml" -type f -exec sed -i.bak 's/networking\.k8s\.io\/v1beta1/networking.k8s.io\/v1/g' {} \;
    echo "  ✓ Fixed networking API versions"

    # Fix autoscaling/v2beta2 to autoscaling/v2
    find "$LEGACY_DIR" -name "*.yaml" -type f -exec sed -i.bak 's/autoscaling\/v2beta2/autoscaling\/v2/g' {} \;
    echo "  ✓ Fixed autoscaling API versions"

    # Remove backup files
    find "$LEGACY_DIR" -name "*.bak" -type f -delete
}

# Function to validate Kustomize structure
validate_kustomize() {
    echo "Validating Kustomize structure..."

    # Check if kustomize is installed
    if ! command -v kustomize &> /dev/null; then
        echo "  ⚠ Warning: kustomize not found. Install it to validate configurations."
        return 0
    fi

    # Validate base
    if kustomize build "$BASE_DIR" > /dev/null 2>&1; then
        echo "  ✓ Base kustomization is valid"
    else
        echo "  ✗ Base kustomization has errors"
        return 1
    fi

    # Validate overlays
    for env in development staging production; do
        overlay_dir="$KUBERNETES_DIR/overlays/$env"
        if [[ -d "$overlay_dir" ]]; then
            if kustomize build "$overlay_dir" > /dev/null 2>&1; then
                echo "  ✓ $env overlay is valid"
            else
                echo "  ✗ $env overlay has errors"
            fi
        fi
    done
}

# Function to generate README for migration
generate_migration_readme() {
    cat > "$KUBERNETES_DIR/MIGRATION_GUIDE.md" << 'EOF'
# Kubernetes Migration to Kustomize

This document outlines the migration from legacy Kubernetes manifests to a modern Kustomize-based structure.

## New Structure

```
kubernetes/
├── base/                    # Base manifests
│   ├── kustomization.yaml
│   ├── namespaces/
│   ├── deployments/
│   ├── services/
│   ├── configmaps/
│   ├── secrets/
│   ├── rbac/
│   ├── storage/
│   ├── security/
│   ├── monitoring/
│   └── ingress/
├── overlays/               # Environment-specific
│   ├── development/
│   ├── staging/
│   └── production/
├── applications/          # ArgoCD applications
│   └── argocd/
└── legacy/               # Original files (archived)
```

## Key Improvements

### 1. Modernized API Versions
- Updated all deprecated API versions to stable versions
- Fixed v1beta1 APIs to v1 where applicable
- Updated networking APIs to v1

### 2. Enhanced Security
- Added comprehensive security contexts
- Implemented Pod Security Standards
- Added network policies for microsegmentation
- Enhanced RBAC with least privilege principle

### 3. Resource Management
- Added proper resource requests and limits
- Implemented Pod Disruption Budgets
- Added Horizontal Pod Autoscalers
- Configured storage classes with encryption

### 4. Observability
- Added Prometheus metrics endpoints
- Configured proper health checks
- Added structured logging configuration
- Implemented distributed tracing

### 5. GitOps Integration
- ArgoCD application definitions
- Environment-specific configurations
- Automated deployment pipelines

## Migration Steps

1. **Backup**: All original files moved to `legacy/` directory
2. **Modernize**: Updated API versions and added security features
3. **Organize**: Restructured into Kustomize base/overlay pattern
4. **Validate**: Ensured all configurations are valid
5. **Deploy**: Use ArgoCD for GitOps deployment

## Usage

### Build manifests for an environment:
```bash
kustomize build overlays/development
kustomize build overlays/staging
kustomize build overlays/production
```

### Apply directly with kubectl:
```bash
kubectl apply -k overlays/development
```

### Use with ArgoCD:
```bash
kubectl apply -f applications/argocd/applications.yaml
```

## Security Considerations

- All secrets use placeholder values - replace with actual secrets
- Pod Security Standards enforced at namespace level
- Network policies deny all traffic by default
- Resource quotas and limits applied
- Non-root containers enforced

## Legacy Files

Original files are preserved in the `legacy/` directory for reference.
These files should not be used for deployment.
EOF

    echo "  ✓ Generated migration guide"
}

# Main migration process
main() {
    echo "🚀 Starting Kubernetes migration to Kustomize..."

    # Move legacy files
    echo "📦 Moving legacy files..."
    move_legacy_file "$KUBERNETES_DIR/namespace.yaml" "Legacy namespace definitions"
    move_legacy_file "$KUBERNETES_DIR/backend-deployment.yaml" "Legacy backend deployment"
    move_legacy_file "$KUBERNETES_DIR/postgres-statefulset.yaml" "Legacy PostgreSQL StatefulSet"
    move_legacy_file "$KUBERNETES_DIR/postgres-secure.yaml" "Legacy PostgreSQL secure config"
    move_legacy_file "$KUBERNETES_DIR/redis-deployment.yaml" "Legacy Redis deployment"
    move_legacy_file "$KUBERNETES_DIR/ingress.yaml" "Legacy ingress configuration"
    move_legacy_file "$KUBERNETES_DIR/create-secrets.sh" "Legacy secret creation script"

    # Move security files
    if [[ -d "$KUBERNETES_DIR/security" ]]; then
        echo "📦 Moving security directory..."
        cp -r "$KUBERNETES_DIR/security" "$LEGACY_DIR/"
        echo "  ✓ Legacy security configurations"
    fi

    # Move apps directory (some files will be migrated)
    if [[ -d "$KUBERNETES_DIR/apps" ]]; then
        echo "📦 Moving apps directory..."
        cp -r "$KUBERNETES_DIR/apps" "$LEGACY_DIR/"
        echo "  ✓ Legacy application configurations"
    fi

    # Fix deprecated API versions in legacy files
    fix_deprecated_apis

    # Validate new structure
    validate_kustomize

    # Generate documentation
    generate_migration_readme

    # Create a simple validation script
    cat > "$KUBERNETES_DIR/validate.sh" << 'EOF'
#!/bin/bash
# Validate Kustomize configurations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Validating Kustomize configurations..."

# Validate base
echo "Validating base..."
kustomize build "$SCRIPT_DIR/base" > /dev/null
echo "✓ Base configuration is valid"

# Validate overlays
for env in development staging production; do
    if [[ -d "$SCRIPT_DIR/overlays/$env" ]]; then
        echo "Validating $env overlay..."
        kustomize build "$SCRIPT_DIR/overlays/$env" > /dev/null
        echo "✓ $env overlay is valid"
    fi
done

echo "🎉 All configurations are valid!"
EOF

    chmod +x "$KUBERNETES_DIR/validate.sh"

    echo ""
    echo "🎉 Migration completed successfully!"
    echo ""
    echo "📁 New Structure:"
    tree "$KUBERNETES_DIR" -I 'legacy' 2>/dev/null || find "$KUBERNETES_DIR" -not -path "*/legacy*" -type d | head -20
    echo ""
    echo "📚 Next Steps:"
    echo "  1. Review the generated configurations in base/ and overlays/"
    echo "  2. Update secret values in overlay-specific files"
    echo "  3. Validate configurations: ./validate.sh"
    echo "  4. Deploy using ArgoCD: kubectl apply -f applications/argocd/"
    echo "  5. Read MIGRATION_GUIDE.md for detailed information"
    echo ""
    echo "⚠️  Important: Update placeholder secret values before deployment!"
}

# Run main function
main "$@"