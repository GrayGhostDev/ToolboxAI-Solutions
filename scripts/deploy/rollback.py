#!/usr/bin/env python3
"""
Rollback Script for ToolboxAI Solutions
Emergency rollback to previous stable deployment
"""

import argparse
import json
import subprocess
import sys
import time

import requests


class RollbackManager:
    """Manages emergency rollbacks for ToolboxAI deployments."""

    def __init__(self, environment: str):
        self.environment = environment

        # Environment configurations
        self.configs = {
            "development": {
                "cluster": "toolboxai-dev-cluster",
                "namespace": "toolboxai-dev",
                "health_url": "https://dev.toolboxai.solutions/health",
                "history_limit": 5,
            },
            "staging": {
                "cluster": "toolboxai-staging-cluster",
                "namespace": "toolboxai-staging",
                "health_url": "https://staging.toolboxai.solutions/health",
                "history_limit": 5,
            },
            "production": {
                "cluster": "toolboxai-prod-cluster",
                "namespace": "toolboxai-prod",
                "health_url": "https://app.toolboxai.solutions/health",
                "history_limit": 10,
            },
        }

        self.config = self.configs.get(environment, {})
        self.rollback_history = []

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

    def get_deployment_history(self) -> list[dict]:
        """Get deployment history for rollback options."""
        print("📜 Fetching deployment history...")

        deployments = ["backend", "dashboard"]
        history = []

        for deployment_name in deployments:
            command = [
                "kubectl",
                "rollout",
                "history",
                f"deployment/{deployment_name}",
                "-n",
                self.config["namespace"],
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                # Parse the history output
                lines = stdout.strip().split("\n")
                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1 and parts[0].isdigit():
                            revision = int(parts[0])
                            history.append(
                                {
                                    "deployment": deployment_name,
                                    "revision": revision,
                                    "description": (
                                        " ".join(parts[1:]) if len(parts) > 1 else "No description"
                                    ),
                                }
                            )

        return history

    def detect_active_color(self) -> str:
        """Detect which color deployment is currently active."""
        print("🔍 Detecting active deployment color...")

        command = [
            "kubectl",
            "get",
            "service",
            f"{self.environment}-service",
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
                color = selector.get("deployment", "unknown")
                print(f"  Current active color: {color}")
                return color
            except:
                pass

        # Check for blue/green deployments
        for color in ["blue", "green"]:
            command = [
                "kubectl",
                "get",
                "deployment",
                f"backend-{color}",
                "-n",
                self.config["namespace"],
                "-o",
                "json",
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                try:
                    deployment_data = json.loads(stdout)
                    replicas = deployment_data.get("spec", {}).get("replicas", 0)
                    if replicas > 0:
                        print(f"  Active deployment detected: {color}")
                        return color
                except:
                    pass

        print("  Unable to detect active color")
        return "unknown"

    def rollback_deployment(self, deployment_name: str, revision: int | None = None) -> bool:
        """Rollback a specific deployment to a previous revision."""
        print(f"\n⏮️  Rolling back {deployment_name}...")

        if revision:
            command = [
                "kubectl",
                "rollout",
                "undo",
                f"deployment/{deployment_name}",
                f"--to-revision={revision}",
                "-n",
                self.config["namespace"],
            ]
        else:
            # Rollback to previous revision
            command = [
                "kubectl",
                "rollout",
                "undo",
                f"deployment/{deployment_name}",
                "-n",
                self.config["namespace"],
            ]

        exit_code, stdout, stderr = self._run_command(command)

        if exit_code == 0:
            print(f"  ✅ Rollback initiated for {deployment_name}")
            return True
        else:
            print(f"  ❌ Failed to rollback {deployment_name}: {stderr}")
            return False

    def rollback_blue_green(self) -> bool:
        """Rollback blue-green deployment by switching colors."""
        current_color = self.detect_active_color()

        if current_color == "unknown":
            print("❌ Cannot determine active deployment for blue-green rollback")
            return False

        target_color = "green" if current_color == "blue" else "blue"

        print(f"\n🔄 Rolling back from {current_color} to {target_color}...")

        # First, scale up the target deployment
        deployments = [f"backend-{target_color}", f"dashboard-{target_color}"]

        for deployment in deployments:
            command = [
                "kubectl",
                "scale",
                "deployment",
                deployment,
                "--replicas=3",
                "-n",
                self.config["namespace"],
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                print(f"  ✅ Scaled up {deployment}")
            else:
                print(f"  ❌ Failed to scale up {deployment}: {stderr}")
                return False

        # Wait for deployments to be ready
        print("  ⏳ Waiting for deployments to be ready...")
        time.sleep(10)

        for deployment in deployments:
            command = [
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment}",
                "-n",
                self.config["namespace"],
                "--timeout=60s",
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code != 0:
                print(f"  ❌ {deployment} not ready: {stderr}")
                return False

        # Switch service selectors
        print(f"  🔄 Switching traffic to {target_color}...")

        services = ["backend-service", "dashboard-service"]

        for service in services:
            patch = {"spec": {"selector": {"deployment": target_color}}}

            command = [
                "kubectl",
                "patch",
                "service",
                service,
                "--type",
                "merge",
                "-p",
                json.dumps(patch),
                "-n",
                self.config["namespace"],
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0:
                print(f"  ✅ Updated {service} to {target_color}")
            else:
                print(f"  ❌ Failed to update {service}: {stderr}")
                return False

        # Scale down the problematic deployment
        print(f"  📉 Scaling down {current_color} deployment...")

        problematic_deployments = [f"backend-{current_color}", f"dashboard-{current_color}"]

        for deployment in problematic_deployments:
            command = [
                "kubectl",
                "scale",
                "deployment",
                deployment,
                "--replicas=0",
                "-n",
                self.config["namespace"],
            ]

            self._run_command(command)

        print(f"  ✅ Blue-green rollback complete: {current_color} → {target_color}")
        return True

    def wait_for_rollback(self, deployment_name: str, timeout: int = 120) -> bool:
        """Wait for rollback to complete."""
        print(f"  ⏳ Waiting for {deployment_name} rollback to complete...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            command = [
                "kubectl",
                "rollout",
                "status",
                f"deployment/{deployment_name}",
                "-n",
                self.config["namespace"],
            ]

            exit_code, stdout, stderr = self._run_command(command)

            if exit_code == 0 and "successfully rolled out" in stdout:
                print(f"  ✅ {deployment_name} rollback completed")
                return True

            time.sleep(5)

        print(f"  ❌ Timeout waiting for {deployment_name} rollback")
        return False

    def verify_rollback(self) -> bool:
        """Verify the rollback was successful."""
        print("\n✅ Verifying rollback...")

        # Check health endpoint
        try:
            response = requests.get(self.config["health_url"], timeout=10)
            if response.status_code == 200:
                print("  ✅ Health check passed after rollback")
                return True
            else:
                print(f"  ❌ Health check failed with status {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Health check failed: {e}")
            return False

    def emergency_rollback(self, strategy: str = "auto", revision: int | None = None) -> bool:
        """Perform emergency rollback based on strategy."""
        print(f"\n{'='*60}")
        print(f"EMERGENCY ROLLBACK - {self.environment.upper()}")
        print(f"{'='*60}")
        print(f"Strategy: {strategy}")

        if strategy == "auto":
            # Detect deployment type and use appropriate strategy
            active_color = self.detect_active_color()
            if active_color in ["blue", "green"]:
                strategy = "blue-green"
            else:
                strategy = "kubernetes"

        success = False

        if strategy == "blue-green":
            # Blue-green rollback
            success = self.rollback_blue_green()

        elif strategy == "kubernetes":
            # Standard Kubernetes rollback
            deployments = ["backend", "dashboard"]

            all_success = True
            for deployment in deployments:
                if not self.rollback_deployment(deployment, revision):
                    all_success = False
                    continue

                if not self.wait_for_rollback(deployment):
                    all_success = False

            success = all_success

        elif strategy == "restore":
            # Restore from backup (would need implementation)
            print("❌ Restore from backup not yet implemented")
            return False

        if success:
            # Verify the rollback
            if self.verify_rollback():
                print(f"\n{'='*60}")
                print("✅ ROLLBACK SUCCESSFUL!")
                print(f"   Environment: {self.environment}")
                print(f"   Strategy: {strategy}")
                print(f"{'='*60}")
                return True
            else:
                print("\n⚠️  Rollback completed but verification failed")
                print("   Manual intervention may be required")
                return False
        else:
            print(f"\n{'='*60}")
            print("❌ ROLLBACK FAILED!")
            print("   Manual intervention required")
            print(f"{'='*60}")
            return False

    def list_rollback_options(self):
        """List available rollback options."""
        print(f"\n📋 Available Rollback Options for {self.environment}:")
        print("=" * 50)

        # Get deployment history
        history = self.get_deployment_history()

        if history:
            print("\nDeployment History:")
            for item in history[: self.config["history_limit"]]:
                print(
                    f"  • {item['deployment']} - Revision {item['revision']}: {item['description']}"
                )

        # Check for blue-green deployments
        active_color = self.detect_active_color()
        if active_color in ["blue", "green"]:
            other_color = "green" if active_color == "blue" else "blue"
            print(f"\nBlue-Green Status:")
            print(f"  • Active: {active_color}")
            print(f"  • Standby: {other_color} (available for rollback)")

        print("\nRollback Strategies:")
        print("  • auto - Automatically detect and use best strategy")
        print("  • blue-green - Switch between blue/green deployments")
        print("  • kubernetes - Standard Kubernetes rollback")
        print("  • restore - Restore from backup (if available)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Emergency Rollback")
    parser.add_argument(
        "--environment",
        required=True,
        choices=["development", "staging", "production"],
        help="Target environment",
    )
    parser.add_argument(
        "--strategy",
        choices=["auto", "blue-green", "kubernetes", "restore"],
        default="auto",
        help="Rollback strategy to use",
    )
    parser.add_argument(
        "--revision", type=int, help="Specific revision to rollback to (for kubernetes strategy)"
    )
    parser.add_argument("--list", action="store_true", help="List available rollback options")
    parser.add_argument("--force", action="store_true", help="Force rollback without confirmation")

    args = parser.parse_args()

    manager = RollbackManager(args.environment)

    try:
        if args.list:
            manager.list_rollback_options()
            sys.exit(0)

        # Confirm rollback unless forced
        if not args.force:
            print(f"\n⚠️  WARNING: This will rollback {args.environment} environment!")
            response = input("Are you sure? (yes/no): ")
            if response.lower() != "yes":
                print("Rollback cancelled")
                sys.exit(0)

        # Perform rollback
        success = manager.emergency_rollback(strategy=args.strategy, revision=args.revision)

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Rollback interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Rollback error: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
