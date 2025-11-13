"""
Security Admission Webhook for ToolBoxAI Kubernetes Deployments
Validates and mutates pods to enforce security standards
"""

import base64
import json
import logging
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import jsonpatch

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security requirements for COPPA/FERPA/GDPR compliance
REQUIRED_SECURITY_CONTEXT = {
    "runAsNonRoot": True,
    "runAsUser": 1000,
    "fsGroup": 1000,
    "readOnlyRootFilesystem": True,
    "allowPrivilegeEscalation": False,
    "capabilities": {
        "drop": ["ALL"]
    }
}

# Prohibited environment variable patterns
PROHIBITED_ENV_PATTERNS = [
    "PASSWORD",
    "SECRET",
    "KEY",
    "TOKEN",
    "CREDENTIAL"
]

# Required labels for compliance
REQUIRED_LABELS = {
    "compliance": ["coppa", "ferpa", "gdpr"],
    "data-classification": ["public", "internal", "confidential", "restricted"]
}

# Safe image registries
ALLOWED_REGISTRIES = [
    "registry.toolboxai.solutions",
    "public.ecr.aws/toolboxai",
    "ghcr.io/toolboxai-solutions"
]


class AdmissionReview:
    """Process Kubernetes admission reviews"""

    def __init__(self, review_request: Dict[str, Any]):
        self.request = review_request
        self.uid = review_request["uid"]
        self.object = review_request.get("object", {})
        self.namespace = review_request.get("namespace", "default")
        self.operation = review_request.get("operation", "CREATE")

    def validate_pod(self) -> tuple[bool, List[str]]:
        """Validate pod against security policies"""
        errors = []

        # Check pod security context
        pod_security_context = self.object.get("spec", {}).get("securityContext", {})
        if not self._validate_security_context(pod_security_context, "pod"):
            errors.append("Pod security context does not meet requirements")

        # Check container security contexts
        containers = self.object.get("spec", {}).get("containers", [])
        for idx, container in enumerate(containers):
            container_sc = container.get("securityContext", {})
            if not self._validate_security_context(container_sc, f"container[{idx}]"):
                errors.append(f"Container {container.get('name', idx)} security context invalid")

            # Check for exposed secrets in environment
            if self._has_exposed_secrets(container.get("env", [])):
                errors.append(f"Container {container.get('name', idx)} has exposed secrets")

            # Validate image registry
            if not self._validate_image(container.get("image", "")):
                errors.append(f"Container {container.get('name', idx)} uses untrusted image")

            # Check resource limits
            if not self._has_resource_limits(container):
                errors.append(f"Container {container.get('name', idx)} missing resource limits")

        # Check required labels
        labels = self.object.get("metadata", {}).get("labels", {})
        if not self._validate_labels(labels):
            errors.append("Missing required compliance labels")

        # Check for host network/PID/IPC
        spec = self.object.get("spec", {})
        if spec.get("hostNetwork") or spec.get("hostPID") or spec.get("hostIPC"):
            errors.append("Host namespace sharing is prohibited")

        # Check volumes
        if not self._validate_volumes(spec.get("volumes", [])):
            errors.append("Invalid volume types detected")

        return len(errors) == 0, errors

    def _validate_security_context(self, context: Dict, context_type: str) -> bool:
        """Validate security context settings"""
        if context_type == "pod":
            required_fields = ["runAsNonRoot", "fsGroup"]
        else:  # container
            required_fields = ["runAsNonRoot", "readOnlyRootFilesystem",
                             "allowPrivilegeEscalation"]

        for field in required_fields:
            if field not in context:
                logger.warning(f"Missing {field} in {context_type} security context")
                return False

            expected = REQUIRED_SECURITY_CONTEXT.get(field)
            if expected is not None and context[field] != expected:
                logger.warning(f"Invalid {field}={context[field]} in {context_type}")
                return False

        # Check capabilities are dropped
        caps = context.get("capabilities", {})
        if caps.get("add"):
            logger.warning(f"Capabilities added in {context_type}: {caps['add']}")
            return False

        return True

    def _has_exposed_secrets(self, env_vars: List[Dict]) -> bool:
        """Check for exposed secrets in environment variables"""
        for env in env_vars:
            name = env.get("name", "")
            value = env.get("value")

            # Check if directly exposed
            if value:
                for pattern in PROHIBITED_ENV_PATTERNS:
                    if pattern in name.upper():
                        logger.warning(f"Exposed secret in env var: {name}")
                        return True

            # Should use secretKeyRef or configMapKeyRef instead
            if not env.get("valueFrom"):
                for pattern in PROHIBITED_ENV_PATTERNS:
                    if pattern in name.upper():
                        logger.warning(f"Secret {name} should use valueFrom")
                        return True

        return False

    def _validate_image(self, image: str) -> bool:
        """Validate image comes from trusted registry"""
        if not image:
            return False

        for registry in ALLOWED_REGISTRIES:
            if image.startswith(registry):
                return True

        # Allow official images with specific tags
        if "/" not in image and ":" in image and image.split(":")[1] != "latest":
            return True

        logger.warning(f"Untrusted image: {image}")
        return False

    def _has_resource_limits(self, container: Dict) -> bool:
        """Check if container has resource limits"""
        resources = container.get("resources", {})
        limits = resources.get("limits", {})
        requests = resources.get("requests", {})

        return "cpu" in limits and "memory" in limits and \
               "cpu" in requests and "memory" in requests

    def _validate_labels(self, labels: Dict) -> bool:
        """Validate required compliance labels"""
        for label_key, valid_values in REQUIRED_LABELS.items():
            if label_key not in labels:
                logger.warning(f"Missing required label: {label_key}")
                return False

            if labels[label_key] not in valid_values:
                logger.warning(f"Invalid value for {label_key}: {labels[label_key]}")
                return False

        return True

    def _validate_volumes(self, volumes: List[Dict]) -> bool:
        """Validate volume types"""
        allowed_types = {
            "configMap", "secret", "emptyDir", "persistentVolumeClaim",
            "downwardAPI", "projected"
        }

        for volume in volumes:
            volume_type = None
            for key in volume.keys():
                if key != "name" and key in allowed_types:
                    volume_type = key
                    break

            if volume_type not in allowed_types:
                logger.warning(f"Prohibited volume type: {volume}")
                return False

        return True

    def mutate_pod(self) -> List[Dict]:
        """Generate mutations to make pod compliant"""
        patches = []
        spec = self.object.get("spec", {})

        # Add pod security context if missing
        if "securityContext" not in spec:
            patches.append({
                "op": "add",
                "path": "/spec/securityContext",
                "value": {
                    "runAsNonRoot": True,
                    "runAsUser": 1000,
                    "fsGroup": 1000
                }
            })

        # Add container security contexts
        containers = spec.get("containers", [])
        for idx, container in enumerate(containers):
            if "securityContext" not in container:
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{idx}/securityContext",
                    "value": REQUIRED_SECURITY_CONTEXT.copy()
                })

            # Add resource limits if missing
            if "resources" not in container:
                patches.append({
                    "op": "add",
                    "path": f"/spec/containers/{idx}/resources",
                    "value": {
                        "limits": {
                            "cpu": "1000m",
                            "memory": "1Gi"
                        },
                        "requests": {
                            "cpu": "100m",
                            "memory": "128Mi"
                        }
                    }
                })

        # Add required labels
        metadata = self.object.get("metadata", {})
        if "labels" not in metadata:
            patches.append({
                "op": "add",
                "path": "/metadata/labels",
                "value": {}
            })

        labels = metadata.get("labels", {})
        if "compliance" not in labels:
            patches.append({
                "op": "add",
                "path": "/metadata/labels/compliance",
                "value": "coppa"
            })

        if "data-classification" not in labels:
            patches.append({
                "op": "add",
                "path": "/metadata/labels/data-classification",
                "value": "internal"
            })

        # Add security annotations
        if "annotations" not in metadata:
            patches.append({
                "op": "add",
                "path": "/metadata/annotations",
                "value": {}
            })

        annotations = metadata.get("annotations", {})
        security_annotations = {
            "security.toolboxai.solutions/scan-status": "pending",
            "security.toolboxai.solutions/compliance": "enforced"
        }

        for key, value in security_annotations.items():
            if key not in annotations:
                patches.append({
                    "op": "add",
                    "path": f"/metadata/annotations/{key.replace('/', '~1')}",
                    "value": value
                })

        return patches


@app.route("/validate", methods=["POST"])
def validate():
    """Validating admission webhook endpoint"""
    admission_review = request.get_json()

    if not admission_review or "request" not in admission_review:
        return jsonify({"error": "Invalid admission review"}), 400

    review = AdmissionReview(admission_review["request"])
    allowed, errors = review.validate_pod()

    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": review.uid,
            "allowed": allowed
        }
    }

    if not allowed:
        response["response"]["status"] = {
            "code": 403,
            "message": f"Pod validation failed: {'; '.join(errors)}"
        }
        logger.warning(f"Rejected pod in namespace {review.namespace}: {errors}")
    else:
        logger.info(f"Approved pod in namespace {review.namespace}")

    return jsonify(response)


@app.route("/mutate", methods=["POST"])
def mutate():
    """Mutating admission webhook endpoint"""
    admission_review = request.get_json()

    if not admission_review or "request" not in admission_review:
        return jsonify({"error": "Invalid admission review"}), 400

    review = AdmissionReview(admission_review["request"])
    patches = review.mutate_pod()

    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": review.uid,
            "allowed": True
        }
    }

    if patches:
        patch_json = json.dumps(patches)
        patch_base64 = base64.b64encode(patch_json.encode()).decode()

        response["response"]["patchType"] = "JSONPatch"
        response["response"]["patch"] = patch_base64

        logger.info(f"Applied {len(patches)} mutations to pod in {review.namespace}")

    return jsonify(response)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    # Run with TLS in production
    app.invoke(
        host="0.0.0.0",
        port=443,
        ssl_context=("/tls/cert.pem", "/tls/key.pem")
    )