#!/bin/bash
# Create Kubernetes secrets securely

kubectl create secret generic toolboxai-db-secret \
  --from-literal=password='VRosWtMyh4RKwe6r4hGU7VLf8' \
  --namespace=default

kubectl create secret generic toolboxai-redis-secret \
  --from-literal=password='d0J5jQG66GKzWSEQh8GtonYqz' \
  --namespace=default

kubectl create secret generic toolboxai-jwt-secret \
  --from-literal=secret='52e29d55ab6435537ae476b38e2b47385f2bb30ff1a11d6794818525953c70fb' \
  --namespace=default

echo "✅ Kubernetes secrets created"
