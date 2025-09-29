#!/bin/bash
# Generate TLS certificates for Admission Webhook
# This script creates self-signed certificates for the webhook service

set -e

NAMESPACE="toolboxai-system"
SERVICE="security-webhook"
SECRET_NAME="webhook-tls"

# Certificate details
CERT_DIR="./certs"
CERT_DAYS=3650
RSA_KEY_SIZE=4096

# Create certificate directory
mkdir -p ${CERT_DIR}

# Generate CA private key
openssl genrsa -out ${CERT_DIR}/ca.key ${RSA_KEY_SIZE}

# Generate CA certificate
cat <<EOF > ${CERT_DIR}/ca.conf
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_ca
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = ToolBoxAI Solutions
OU = Security
CN = ToolBoxAI Webhook CA

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical,CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
EOF

openssl req -x509 -new -nodes -key ${CERT_DIR}/ca.key \
    -sha256 -days ${CERT_DAYS} -out ${CERT_DIR}/ca.crt \
    -config ${CERT_DIR}/ca.conf

# Generate server private key
openssl genrsa -out ${CERT_DIR}/server.key ${RSA_KEY_SIZE}

# Generate server certificate request
cat <<EOF > ${CERT_DIR}/server.conf
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = California
L = San Francisco
O = ToolBoxAI Solutions
OU = Security
CN = ${SERVICE}.${NAMESPACE}.svc

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = ${SERVICE}
DNS.2 = ${SERVICE}.${NAMESPACE}
DNS.3 = ${SERVICE}.${NAMESPACE}.svc
DNS.4 = ${SERVICE}.${NAMESPACE}.svc.cluster
DNS.5 = ${SERVICE}.${NAMESPACE}.svc.cluster.local
IP.1 = 127.0.0.1
EOF

openssl req -new -key ${CERT_DIR}/server.key -out ${CERT_DIR}/server.csr \
    -config ${CERT_DIR}/server.conf

# Generate server certificate
openssl x509 -req -in ${CERT_DIR}/server.csr \
    -CA ${CERT_DIR}/ca.crt -CAkey ${CERT_DIR}/ca.key \
    -CAcreateserial -out ${CERT_DIR}/server.crt \
    -days ${CERT_DAYS} -sha256 \
    -extensions v3_req -extfile ${CERT_DIR}/server.conf

# Verify the certificate
echo "Verifying certificate..."
openssl verify -CAfile ${CERT_DIR}/ca.crt ${CERT_DIR}/server.crt

# Create combined PEM files for the application
cp ${CERT_DIR}/server.crt ${CERT_DIR}/cert.pem
cp ${CERT_DIR}/server.key ${CERT_DIR}/key.pem

# Base64 encode for Kubernetes secret
CA_BUNDLE=$(cat ${CERT_DIR}/ca.crt | base64 | tr -d '\n')
TLS_CRT=$(cat ${CERT_DIR}/server.crt | base64 | tr -d '\n')
TLS_KEY=$(cat ${CERT_DIR}/server.key | base64 | tr -d '\n')

# Generate Kubernetes secret YAML
cat <<EOF > ${CERT_DIR}/webhook-tls-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ${SECRET_NAME}
  namespace: ${NAMESPACE}
type: kubernetes.io/tls
data:
  tls.crt: ${TLS_CRT}
  tls.key: ${TLS_KEY}
EOF

# Generate webhook configuration with CA bundle
cat <<EOF > ${CERT_DIR}/webhook-config-update.yaml
# Update the webhook configurations with the CA bundle
# Apply this patch to the ValidatingWebhookConfiguration and MutatingWebhookConfiguration

apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: toolboxai-security-webhook
webhooks:
  - name: pod-security.toolboxai.solutions
    clientConfig:
      caBundle: ${CA_BUNDLE}
---
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: toolboxai-security-defaults
webhooks:
  - name: security-defaults.toolboxai.solutions
    clientConfig:
      caBundle: ${CA_BUNDLE}
EOF

echo "✅ Certificates generated successfully!"
echo ""
echo "Files created in ${CERT_DIR}:"
echo "  - ca.crt: Certificate Authority certificate"
echo "  - ca.key: Certificate Authority private key"
echo "  - server.crt: Server certificate"
echo "  - server.key: Server private key"
echo "  - cert.pem: Server certificate (PEM format)"
echo "  - key.pem: Server private key (PEM format)"
echo "  - webhook-tls-secret.yaml: Kubernetes Secret manifest"
echo "  - webhook-config-update.yaml: Webhook configuration with CA bundle"
echo ""
echo "To deploy the certificates:"
echo "  1. Create the secret: kubectl apply -f ${CERT_DIR}/webhook-tls-secret.yaml"
echo "  2. Update webhook configs: kubectl apply -f ${CERT_DIR}/webhook-config-update.yaml"
echo ""
echo "CA Bundle for webhook configuration:"
echo "${CA_BUNDLE}"