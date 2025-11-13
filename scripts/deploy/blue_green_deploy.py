#!/usr/bin/env python3
"""
Blue-Green Deployment Script for ToolboxAI Solutions
Implements zero-downtime deployments with automatic rollback capability
"""

import argparse
import json
import subprocess
import sys
import time

import requests


class BlueGreenDeployer:
    """Manages blue-green deployments for ToolboxAI services."""

    def __init__(self, environment: str, backend_image: str, dashboard_image: str):
        self.environment = environment
        self.backend_image = backend_image
        self.dashboard_image = dashboard_image

        # Environment configurations
        self.configs = {
            "development": {
                "cluster": "toolboxai-dev-cluster",
                "namespace": "toolboxai-dev",
                "load_balancer": "dev-lb.toolboxai.solutions",
                "health_url": "https://dev.toolboxai.solutions/health",
            },
            "staging": {
                "cluster": "toolboxai-staging-cluster",
                "namespace": "toolboxai-staging",
                "load_balancer": "staging-lb.toolboxai.solutions",
                "health_url": "https://staging.toolboxai.solutions/health",
            },
            "production": {
                "cluster": "toolboxai-prod-cluster",
                "namespace": "toolboxai-prod",
                "load_balancer": "lb.toolboxai.solutions",
                "health_url": "https://app.toolboxai.solutions/health",
            },
        }

        self.config = self.configs.get(environment, {})
        self.current_color = None
        self.target_color = None

    def _run_command(self, command: list[str], capture_output: bool = True) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, and stderr."""
        try:
            if capture_output:
                result = subprocess.run(command, capture_output=True, text=True, timeout=60)
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(command, timeout=60)
                return result.returncode, "", ""
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)

    def detect_current_deployment(self) -> str:
        """Detect which color (blue/green) is currently active."""
        print("🔍 Detecting current deployment color...")

        # In a real implementation, this would check the load balancer
        # or service configuration to determine active deployment
        # For now, we'll simulate this

        # Try to get current deployment from Kubernetes
        command = [
            "kubectl",
            "get",
            "service",
            f"{self.environment}-active",
            "-n",
            self.config["namespace"],
            "-o",
            "json",
        ]

        exit_code, stdout, stderr = self._run_command(command)

        if exit_code == 0:
            try:
                service_data = json.loads(stdout)
                selector = service_data.get("spec", {}).get("selector", {})
                current_color = selector.get("deployment", "blue")
                print(f"  Current active deployment: {current_color}")
                return current_color
            except:
                pass

        # Default to blue if we can't determine
        print("  Unable to detect current deployment, assuming blue")
        return "blue"

    def deploy_to_inactive_slot(self) -> bool:
        """Deploy new version to the inactive slot."""
        print(f"\n🚀 Deploying to {self.target_color} slot...")

        deployment_manifest = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-{self.target_color}
  namespace: {self.config['namespace']}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
      deployment: {self.target_color}
  template:
    metadata:
      labels:
        app: backend
        deployment: {self.target_color}
    spec:
      containers:
      - name: backend
        image: {self.backend_image}
        ports:
        - containerPort: 8009
        env:
        - name: ENVIRONMENT
          value: {self.environment}
        livenessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8009
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dashboard-{self.target_color}
  namespace: {self.config['namespace']}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dashboard
      deployment: {self.target_color}
  template:
    metadata:
      labels:
        app: dashboard
        deployment: {self.target_color}
    spec:
      containers:
      - name: dashboard
        image: {self.dashboard_image}
        ports:
        - containerPort: 80
        env:
        - name: ENVIRONMENT
          value: {self.environment}
        - name: API_URL
          value: http://backend-{self.target_color}:8009
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
"""

        # Write manifest to temporary file
        manifest_file = f"/tmp/deployment-{self.target_color}.yaml"
        with open(manifest_file, "w") as f:
            f.write(deployment_manifest)

        # Apply the deployment
        print(f"  Applying {self.target_color} deployment manifests...")
        command = ["kubectl", "apply", "-f", manifest_file]
        exit_code, stdout, stderr = self._run_command(command)

        if exit_code != 0:
            print(f"  ❌ Failed to apply deployment: {stderr}")
            return False

        print(f"  ✅ {self.target_color.capitalize()} deployment created")
        return True

    def wait_for_deployment_ready(self, timeout: int = 300) -> bool:
        """Wait for the new deployment to be ready."""
        print(f"\n⏳ Waiting for {self.target_color} deployment to be ready...")

        deployments = [f"backend-{self.target_color}", f"dashboard-{self.target_color}"]

        start_time = time.time()

        for deployment in deployments:
            while time.time() - start_time < timeout:
                command = [
                    "kubectl",
                    "rollout",
                    "status",
                    f"deployment/{deployment}",
                    "-n",
                    self.config["namespace"],
                    "--timeout=10s",
                ]

                exit_code, stdout, stderr = self._run_command(command)

                if exit_code == 0:
                    print(f"  ✅ {deployment} is ready")
                    break

                print(f"  Waiting for {deployment}...")
                time.sleep(5)
            else:
                print(f"  ❌ Timeout waiting for {deployment}")
                return False

        return True

    def run_smoke_tests(self) -> bool:
        """Run smoke tests against the new deployment."""
        print(f"\n🔍 Running smoke tests on {self.target_color} deployment...")

        # Create a service pointing to the new deployment for testing
        test_service = f"""
apiVersion: v1
kind: Service
metadata:
  name: test-{self.target_color}
  namespace: {self.config['namespace']}
spec:
  selector:
    deployment: {self.target_color}
  ports:
  - port: 80
    targetPort: 80
"""

        service_file = f"/tmp/test-service-{self.target_color}.yaml"
        with open(service_file, "w") as f:
            f.write(test_service)

        # Apply test service
        command = ["kubectl", "apply", "-f", service_file]
        self._run_command(command)

        # Port-forward to test the service locally
        print("  Setting up port forwarding for testing...")
        port_forward_command = [
            "kubectl",
            "port-forward",
            f"service/test-{self.target_color}",
            "8080:80",
            "-n",
            self.config["namespace"],
        ]

        # Start port forwarding in background
        import subprocess

        port_forward_process = subprocess.Popen(
            port_forward_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        time.sleep(5)  # Wait for port forward to establish

        try:
            # Run smoke tests
            test_url = "http://localhost:8080/health"
            response = requests.get(test_url, timeout=10)

            if response.status_code == 200:
                print(f"  ✅ Smoke tests passed for {self.target_color} deployment")
                return True
            else:
                print(f"  ❌ Smoke tests failed: Health check returned {response.status_code}")
                return False

        except Exception as e:
            print(f"  ❌ Smoke tests failed: {e}")
            return False
        finally:
            # Clean up port forwarding
            port_forward_process.terminate()

            # Delete test service
            command = ["kubectl", "delete", "-f", service_file, "--ignore-not-found=true"]
            self._run_command(command)

    def switch_traffic(self) -> bool:
        """Switch traffic from current deployment to new deployment."""
        print(f"\n🔄 Switching traffic from {self.current_color} to {self.target_color}...")

        # Update the main service to point to the new deployment
        service_patch = {"spec": {"selector": {"deployment": self.target_color}}}

        services = ["backend-service", "dashboard-service"]

        for service in services:
            command = [
                "kubectl",
                "patch",
                "service",
                service,
                "-n",
                self.config["namespace"],
                "--type",
                "merge",
                "-p",
                json.dumps(service_patch),
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code != 0:
                print(f"  ❌ Failed to update {service}: {stderr}")
                return False

            print(f"  ✅ Updated {service} to route to {self.target_color}")

        return True

    def verify_deployment(self) -> bool:
        """Verify the new deployment is working correctly."""
        print(f"\n✅ Verifying {self.target_color} deployment...")

        # Wait a moment for changes to propagate
        time.sleep(10)

        # Check health endpoint
        try:
            response = requests.get(self.config["health_url"], timeout=10)
            if response.status_code == 200:
                print(f"  ✅ Production health check passed")
                return True
            else:
                print(f"  ❌ Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False

    def cleanup_old_deployment(self) -> bool:
        """Remove the old deployment after successful switch."""
        print(f"\n🧹 Cleaning up old {self.current_color} deployment...")

        # Keep the old deployment for quick rollback capability
        # Just scale it down to save resources
        deployments = [f"backend-{self.current_color}", f"dashboard-{self.current_color}"]

        for deployment in deployments:
            command = [
                "kubectl",
                "scale",
                "deployment",
                deployment,
                "-n",
                self.config["namespace"],
                "--replicas=0",
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                print(f"  ✅ Scaled down {deployment}")
            else:
                print(f"  ⚠️  Failed to scale down {deployment}: {stderr}")

        return True

    def deploy(self) -> bool:
        """Execute the full blue-green deployment."""
        print(f"\n{'='*60}")
        print(f"BLUE-GREEN DEPLOYMENT - {self.environment.upper()}")
        print(f"{'='*60}")
        print(f"Backend Image: {self.backend_image}")
        print(f"Dashboard Image: {self.dashboard_image}")

        # Step 1: Detect current deployment
        self.current_color = self.detect_current_deployment()
        self.target_color = "green" if self.current_color == "blue" else "blue"

        print(f"\nDeployment Strategy:")
        print(f"  Current: {self.current_color}")
        print(f"  Target: {self.target_color}")

        # Step 2: Deploy to inactive slot
        if not self.deploy_to_inactive_slot():
            print("\n❌ Deployment failed at deploy stage")
            return False

        # Step 3: Wait for deployment to be ready
        if not self.wait_for_deployment_ready():
            print("\n❌ Deployment failed - new version not ready")
            return False

        # Step 4: Run smoke tests
        if not self.run_smoke_tests():
            print("\n❌ Deployment failed - smoke tests failed")
            print("   Rolling back...")
            self.rollback()
            return False

        # Step 5: Switch traffic
        if not self.switch_traffic():
            print("\n❌ Deployment failed - traffic switch failed")
            print("   Rolling back...")
            self.rollback()
            return False

        # Step 6: Verify deployment
        if not self.verify_deployment():
            print("\n❌ Deployment failed - verification failed")
            print("   Rolling back...")
            self.rollback()
            return False

        # Step 7: Cleanup old deployment
        self.cleanup_old_deployment()

        print(f"\n{'='*60}")
        print(f"✅ DEPLOYMENT SUCCESSFUL!")
        print(f"   Environment: {self.environment}")
        print(f"   Active Color: {self.target_color}")
        print(f"{'='*60}")

        return True

    def rollback(self) -> bool:
        """Rollback to the previous deployment."""
        print(f"\n⚠️  Rolling back to {self.current_color} deployment...")

        # Switch traffic back to original deployment
        service_patch = {"spec": {"selector": {"deployment": self.current_color}}}

        services = ["backend-service", "dashboard-service"]

        for service in services:
            command = [
                "kubectl",
                "patch",
                "service",
                service,
                "-n",
                self.config["namespace"],
                "--type",
                "merge",
                "-p",
                json.dumps(service_patch),
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                print(f"  ✅ Rolled back {service} to {self.current_color}")

        # Scale up old deployment if it was scaled down
        deployments = [f"backend-{self.current_color}", f"dashboard-{self.current_color}"]

        for deployment in deployments:
            command = [
                "kubectl",
                "scale",
                "deployment",
                deployment,
                "-n",
                self.config["namespace"],
                "--replicas=3",
            ]

            self._run_command(command)

        print(f"  ✅ Rollback completed")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Blue-Green Deployment")
    parser.add_argument("--backend-image", required=True, help="Backend Docker image to deploy")
    parser.add_argument("--dashboard-image", required=True, help="Dashboard Docker image to deploy")
    parser.add_argument(
        "--environment",
        required=True,
        choices=["development", "staging", "production"],
        help="Target environment",
    )

    args = parser.parse_args()

    deployer = BlueGreenDeployer(args.environment, args.backend_image, args.dashboard_image)

    try:
        success = deployer.deploy()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Deployment interrupted")
        deployer.rollback()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment error: {e}")
        deployer.rollback()
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
