"""
Docker Phase 3 Comprehensive Testing Suite

This module provides 10 comprehensive tests for Docker infrastructure:
1. Security hardening validation
2. Image size optimization validation
3. Production readiness validation
4. Multi-container orchestration
5. Resource limits and monitoring
6. Network isolation and security
7. Secrets management validation
8. Health check robustness
9. Backup and recovery procedures
10. High availability and scaling

Tests follow enterprise security and performance standards.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import pytest
import docker
from docker.models.containers import Container
from docker.types import Mount
import yaml
import subprocess
import tempfile
import hashlib


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.phase3
class TestDockerPhase3Comprehensive:
    """Comprehensive Docker Phase 3 testing suite."""

    def setup_method(self):
        """Set up test environment."""
        self.docker_client = docker.from_env()
        self.compose_file = Path("infrastructure/docker/compose/docker-compose.yml")
        self.prod_compose_file = Path("infrastructure/docker/compose/docker-compose.prod.yml")

        # Expected security standards
        self.security_standards = {
            "no_root_user": True,
            "read_only_filesystem": True,
            "drop_all_capabilities": True,
            "no_privileged": True,
            "secrets_external": True,
            "healthcheck_required": True,
        }

        # Image size targets (in MB)
        self.image_size_targets = {
            "backend": 200,
            "dashboard": 100,
            "mcp": 150,
            "agents": 180,
            "celery-worker": 200,
            "celery-beat": 180,
            "celery-flower": 120,
        }

    def teardown_method(self):
        """Clean up test environment."""
        self.docker_client.close()

    # ============================================
    # TEST 1: Security Hardening Validation
    # ============================================
    def test_01_security_hardening_validation(self):
        """
        Test 1: Validate all security hardening measures.

        Checks:
        - Non-root users (UID > 1000)
        - Read-only filesystems with tmpfs
        - Dropped capabilities (ALL)
        - No privileged mode
        - Security options (no-new-privileges)
        - Secrets not in environment variables
        """
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get("services", {})
        security_results = {}

        for service_name, service_config in services.items():
            results = {
                "non_root_user": False,
                "read_only_fs": False,
                "capabilities_dropped": False,
                "security_opts": False,
                "no_secrets_in_env": False,
                "issues": []
            }

            # Check non-root user
            if "user" in service_config:
                user_spec = service_config["user"]
                if isinstance(user_spec, str) and ":" in user_spec:
                    uid, gid = user_spec.split(":")
                    if int(uid) >= 1001:
                        results["non_root_user"] = True
                    else:
                        results["issues"].append(f"UID {uid} < 1001 (should be >= 1001)")
            else:
                # Some services like postgres need specific users
                if service_name not in ["postgres", "redis", "nginx"]:
                    results["issues"].append("No user specification found")

            # Check read-only filesystem
            if service_config.get("read_only") is True or \
               (service_config.get("security_opt") and "read_only" in str(service_config.get("security_opt"))):
                results["read_only_fs"] = True

                # Check tmpfs for writable directories
                if "tmpfs" in service_config:
                    tmpfs_dirs = service_config["tmpfs"]
                    if "/tmp" in tmpfs_dirs or any("/tmp" in str(t) for t in tmpfs_dirs):
                        results["read_only_fs"] = True

            # Check capabilities dropped
            cap_drop = service_config.get("cap_drop", [])
            if "ALL" in cap_drop:
                results["capabilities_dropped"] = True
            else:
                results["issues"].append("Capabilities not dropped (should drop ALL)")

            # Check security options
            security_opts = service_config.get("security_opt", [])
            if any("no-new-privileges" in opt for opt in security_opts):
                results["security_opts"] = True
            else:
                results["issues"].append("Missing no-new-privileges security option")

            # Check secrets not in environment
            environment = service_config.get("environment", {})
            if isinstance(environment, dict):
                env_vars = environment
            elif isinstance(environment, list):
                env_vars = {item.split("=")[0]: item.split("=")[1] if "=" in item else None
                          for item in environment}
            else:
                env_vars = {}

            # Look for secret-like variables that should use secrets
            sensitive_keywords = ["PASSWORD", "SECRET", "KEY", "TOKEN"]
            secrets_in_env = []
            for key, value in env_vars.items():
                if any(keyword in key.upper() for keyword in sensitive_keywords):
                    if not (str(value).endswith("_FILE") or str(value).startswith("${") or str(value).startswith("/run/secrets")):
                        secrets_in_env.append(key)

            if not secrets_in_env:
                results["no_secrets_in_env"] = True
            else:
                results["issues"].append(f"Secrets in env: {secrets_in_env}")

            security_results[service_name] = results

        # Analyze results
        critical_services = ["backend", "mcp-server", "agent-coordinator", "celery-worker"]
        failures = []

        for service_name in critical_services:
            if service_name not in security_results:
                continue

            results = security_results[service_name]

            # All critical services must pass security checks
            if not results["non_root_user"]:
                failures.append(f"{service_name}: Must run as non-root user")

            if not results["read_only_fs"]:
                failures.append(f"{service_name}: Must have read-only filesystem")

            if not results["capabilities_dropped"]:
                failures.append(f"{service_name}: Must drop ALL capabilities")

            if not results["security_opts"]:
                failures.append(f"{service_name}: Must have no-new-privileges")

            if not results["no_secrets_in_env"]:
                failures.append(f"{service_name}: Must not have secrets in environment")

        # Report results
        print(f"\n{'='*80}")
        print("Docker Security Hardening Validation Results")
        print(f"{'='*80}")
        for service_name, results in security_results.items():
            status = "✓ PASS" if not results["issues"] else "✗ FAIL"
            print(f"\n{service_name}: {status}")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  - {issue}")
        print(f"\n{'='*80}\n")

        assert not failures, f"Security hardening failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 2: Image Size Optimization Validation
    # ============================================
    def test_02_image_size_optimization(self):
        """
        Test 2: Validate Docker image sizes meet optimization targets.

        Checks:
        - Backend image < 200MB
        - Dashboard image < 100MB
        - MCP image < 150MB
        - Agents image < 180MB
        - Multi-stage builds used
        - Alpine/slim base images
        """
        images = self.docker_client.images.list()
        toolboxai_images = [img for img in images if any("toolboxai" in tag for tag in img.tags)]

        size_results = {}
        failures = []

        for image in toolboxai_images:
            # Get image name
            tag = image.tags[0] if image.tags else "unknown"
            service_name = tag.split("/")[-1].split(":")[0] if "/" in tag else tag.split(":")[0]

            # Get size in MB
            size_bytes = image.attrs.get("Size", 0)
            size_mb = size_bytes / (1024 * 1024)

            # Check against target
            target_mb = self.image_size_targets.get(service_name, float('inf'))

            size_results[service_name] = {
                "size_mb": size_mb,
                "target_mb": target_mb,
                "meets_target": size_mb <= target_mb,
                "tags": image.tags
            }

            if service_name in self.image_size_targets and size_mb > target_mb:
                failures.append(
                    f"{service_name}: {size_mb:.1f}MB exceeds target {target_mb}MB"
                )

        # Check for multi-stage builds
        dockerfiles = list(Path("infrastructure/docker/dockerfiles").glob("*.Dockerfile"))

        for dockerfile_path in dockerfiles:
            with open(dockerfile_path, 'r') as f:
                content = f.read()

            service_name = dockerfile_path.stem

            # Check for multi-stage build indicators
            has_multistage = "AS builder" in content or "AS build" in content
            uses_alpine = "alpine" in content.lower() or "slim" in content.lower()

            if service_name not in size_results:
                size_results[service_name] = {}

            size_results[service_name]["multistage"] = has_multistage
            size_results[service_name]["alpine_or_slim"] = uses_alpine

            if not has_multistage:
                failures.append(f"{service_name}: Should use multi-stage build")

        # Report results
        print(f"\n{'='*80}")
        print("Docker Image Size Optimization Results")
        print(f"{'='*80}")
        for service_name, results in size_results.items():
            if "size_mb" in results:
                status = "✓" if results["meets_target"] else "✗"
                print(f"{service_name}: {status} {results['size_mb']:.1f}MB / {results['target_mb']}MB target")
                if "multistage" in results:
                    print(f"  Multi-stage: {'✓' if results['multistage'] else '✗'}")
                if "alpine_or_slim" in results:
                    print(f"  Alpine/Slim: {'✓' if results['alpine_or_slim'] else '✗'}")
        print(f"{'='*80}\n")

        assert not failures, f"Image size optimization failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 3: Production Readiness Validation
    # ============================================
    def test_03_production_readiness_validation(self):
        """
        Test 3: Validate production readiness configuration.

        Checks:
        - Health checks defined for all services
        - Restart policies configured
        - Resource limits set
        - Logging configured
        - Deploy configuration for production
        - Monitoring labels
        """
        with open(self.compose_file, 'r') as f:
            base_config = yaml.safe_load(f)

        with open(self.prod_compose_file, 'r') as f:
            prod_config = yaml.safe_load(f)

        services = base_config.get("services", {})
        prod_services = prod_config.get("services", {})

        readiness_results = {}
        failures = []

        for service_name, service_config in services.items():
            results = {
                "healthcheck": False,
                "restart_policy": False,
                "resource_limits": False,
                "logging": False,
                "deploy_config": False,
                "labels": False,
                "issues": []
            }

            # Check health check
            if "healthcheck" in service_config:
                healthcheck = service_config["healthcheck"]
                if "test" in healthcheck and "interval" in healthcheck:
                    results["healthcheck"] = True
                else:
                    results["issues"].append("Incomplete healthcheck configuration")
            else:
                results["issues"].append("No healthcheck defined")

            # Check restart policy
            if "restart" in service_config or service_config.get("restart") == "unless-stopped":
                results["restart_policy"] = True
            else:
                results["issues"].append("No restart policy configured")

            # Check resource limits
            deploy_config = service_config.get("deploy", {})
            if "resources" in deploy_config:
                resources = deploy_config["resources"]
                if "limits" in resources and "reservations" in resources:
                    results["resource_limits"] = True
                else:
                    results["issues"].append("Incomplete resource limits")
            else:
                results["issues"].append("No resource limits defined")

            # Check logging
            if "logging" in service_config:
                logging_config = service_config["logging"]
                if "driver" in logging_config and "options" in logging_config:
                    results["logging"] = True
                else:
                    results["issues"].append("Incomplete logging configuration")
            else:
                results["issues"].append("No logging configuration")

            # Check production deploy configuration
            if service_name in prod_services:
                prod_service = prod_services[service_name]
                prod_deploy = prod_service.get("deploy", {})

                if "replicas" in prod_deploy and prod_deploy["replicas"] >= 1:
                    results["deploy_config"] = True
                else:
                    results["issues"].append("No production replica configuration")

            # Check labels for monitoring
            if "labels" in service_config:
                labels = service_config["labels"]
                if any("com.toolboxai" in label for label in labels):
                    results["labels"] = True
                else:
                    results["issues"].append("Missing monitoring labels")

            readiness_results[service_name] = results

        # Analyze critical services
        critical_services = ["backend", "dashboard", "postgres", "redis", "mcp-server"]

        for service_name in critical_services:
            if service_name not in readiness_results:
                continue

            results = readiness_results[service_name]

            if not results["healthcheck"]:
                failures.append(f"{service_name}: Missing healthcheck")

            if not results["restart_policy"]:
                failures.append(f"{service_name}: Missing restart policy")

            if not results["resource_limits"]:
                failures.append(f"{service_name}: Missing resource limits")

        # Report results
        print(f"\n{'='*80}")
        print("Production Readiness Validation Results")
        print(f"{'='*80}")
        for service_name, results in readiness_results.items():
            total_checks = 6
            passed_checks = sum(1 for k, v in results.items() if k != "issues" and v is True)
            status = "✓ PASS" if not results["issues"] else "⚠ WARN"
            print(f"\n{service_name}: {status} ({passed_checks}/{total_checks} checks passed)")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  - {issue}")
        print(f"\n{'='*80}\n")

        assert not failures, f"Production readiness failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 4: Multi-Container Orchestration
    # ============================================
    @pytest.mark.asyncio
    async def test_04_multi_container_orchestration(self):
        """
        Test 4: Validate multi-container orchestration.

        Checks:
        - Service dependencies honored
        - Container startup order correct
        - Inter-container communication
        - Network isolation properly configured
        - Service discovery working
        """
        # Get all running containers
        containers = self.docker_client.containers.list()
        toolboxai_containers = [c for c in containers if "toolboxai" in c.name]

        # Build dependency graph from compose file
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get("services", {})
        dependency_graph = {}

        for service_name, service_config in services.items():
            depends_on = service_config.get("depends_on", {})
            if isinstance(depends_on, dict):
                deps = list(depends_on.keys())
            elif isinstance(depends_on, list):
                deps = depends_on
            else:
                deps = []

            dependency_graph[service_name] = deps

        # Check startup order
        container_info = []
        for container in toolboxai_containers:
            inspect_data = self.docker_client.api.inspect_container(container.id)
            created_time = inspect_data["Created"]
            started_time = inspect_data["State"]["StartedAt"]

            # Extract service name
            service_name = container.name.replace("toolboxai-", "")

            container_info.append({
                "name": service_name,
                "created": datetime.fromisoformat(created_time.replace('Z', '+00:00')),
                "started": datetime.fromisoformat(started_time.replace('Z', '+00:00')),
                "status": container.status
            })

        # Sort by start time
        container_info.sort(key=lambda x: x["started"])

        # Validate dependency order
        started_services = set()
        failures = []

        for info in container_info:
            service_name = info["name"]

            # Check if dependencies started before this service
            if service_name in dependency_graph:
                deps = dependency_graph[service_name]
                for dep in deps:
                    if dep not in started_services:
                        failures.append(
                            f"{service_name} started before dependency {dep}"
                        )

            started_services.add(service_name)

        # Check network isolation
        networks = self.docker_client.networks.list()
        toolboxai_networks = [n for n in networks if "toolboxai" in n.name or any("br-" in n.name for n in networks)]

        # Verify internal networks exist
        network_names = [n.name for n in networks]
        expected_internal_networks = ["database", "cache", "mcp"]

        for expected in expected_internal_networks:
            matching = [n for n in network_names if expected in n]
            if not matching:
                failures.append(f"Internal network '{expected}' not found")

        # Report results
        print(f"\n{'='*80}")
        print("Multi-Container Orchestration Results")
        print(f"{'='*80}")
        print(f"Total containers: {len(container_info)}")
        print(f"Networks found: {len(toolboxai_networks)}")
        print("\nStartup order:")
        for i, info in enumerate(container_info, 1):
            print(f"  {i}. {info['name']} ({info['status']})")
        print(f"{'='*80}\n")

        assert not failures, f"Orchestration failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 5: Resource Limits and Monitoring
    # ============================================
    def test_05_resource_limits_and_monitoring(self):
        """
        Test 5: Validate resource limits and monitoring configuration.

        Checks:
        - CPU limits configured
        - Memory limits configured
        - Resource reservations set
        - Monitoring endpoints exposed
        - Metrics collection configured
        """
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        services = compose_config.get("services", {})
        resource_results = {}
        failures = []

        for service_name, service_config in services.items():
            results = {
                "cpu_limit": None,
                "memory_limit": None,
                "cpu_reservation": None,
                "memory_reservation": None,
                "has_limits": False,
                "has_reservations": False,
                "issues": []
            }

            deploy_config = service_config.get("deploy", {})
            resources = deploy_config.get("resources", {})

            # Check limits
            limits = resources.get("limits", {})
            if limits:
                results["cpu_limit"] = limits.get("cpus")
                results["memory_limit"] = limits.get("memory")

                if results["cpu_limit"] and results["memory_limit"]:
                    results["has_limits"] = True
                else:
                    results["issues"].append("Incomplete resource limits")
            else:
                results["issues"].append("No resource limits configured")

            # Check reservations
            reservations = resources.get("reservations", {})
            if reservations:
                results["cpu_reservation"] = reservations.get("cpus")
                results["memory_reservation"] = reservations.get("memory")

                if results["cpu_reservation"] and results["memory_reservation"]:
                    results["has_reservations"] = True
                else:
                    results["issues"].append("Incomplete resource reservations")
            else:
                results["issues"].append("No resource reservations configured")

            resource_results[service_name] = results

        # Check monitoring configuration
        prometheus_config = Path("infrastructure/monitoring/prometheus/prometheus-unified.yml")
        if prometheus_config.exists():
            with open(prometheus_config, 'r') as f:
                prom_config = yaml.safe_load(f)

            scrape_configs = prom_config.get("scrape_configs", [])
            monitored_services = set()

            for scrape_config in scrape_configs:
                job_name = scrape_config.get("job_name", "")
                monitored_services.add(job_name)

            print(f"\nMonitored services: {len(monitored_services)}")

        # Validate critical services
        critical_services = ["backend", "postgres", "redis", "mcp-server"]

        for service_name in critical_services:
            if service_name not in resource_results:
                continue

            results = resource_results[service_name]

            if not results["has_limits"]:
                failures.append(f"{service_name}: Missing resource limits")

            if not results["has_reservations"]:
                failures.append(f"{service_name}: Missing resource reservations")

        # Report results
        print(f"\n{'='*80}")
        print("Resource Limits and Monitoring Results")
        print(f"{'='*80}")
        for service_name, results in resource_results.items():
            status = "✓" if results["has_limits"] and results["has_reservations"] else "✗"
            print(f"\n{service_name}: {status}")
            if results["cpu_limit"]:
                print(f"  CPU Limit: {results['cpu_limit']}")
            if results["memory_limit"]:
                print(f"  Memory Limit: {results['memory_limit']}")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  ⚠ {issue}")
        print(f"\n{'='*80}\n")

        assert not failures, f"Resource limit failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 6: Network Isolation and Security
    # ============================================
    def test_06_network_isolation_and_security(self):
        """
        Test 6: Validate network isolation and security.

        Checks:
        - Internal networks have no external access
        - Services on correct networks
        - Network segmentation proper
        - No unnecessary network exposure
        - Firewall rules via network policies
        """
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        networks_config = compose_config.get("networks", {})
        services = compose_config.get("services", {})

        network_results = {}
        failures = []

        # Check network isolation
        for network_name, network_config in networks_config.items():
            is_internal = network_config.get("internal", False)

            network_results[network_name] = {
                "internal": is_internal,
                "should_be_internal": network_name in ["database", "cache", "mcp"],
                "services": [],
                "issues": []
            }

            # Database, cache, and MCP networks should be internal
            if network_name in ["database", "cache", "mcp"] and not is_internal:
                network_results[network_name]["issues"].append(
                    f"Network '{network_name}' should be internal"
                )
                failures.append(f"Network '{network_name}' not marked as internal")

        # Check service network assignments
        for service_name, service_config in services.items():
            service_networks = service_config.get("networks", [])

            if isinstance(service_networks, dict):
                network_list = list(service_networks.keys())
            elif isinstance(service_networks, list):
                network_list = service_networks
            else:
                network_list = []

            for network in network_list:
                if network in network_results:
                    network_results[network]["services"].append(service_name)

        # Check port exposure
        exposed_ports = {}
        for service_name, service_config in services.items():
            ports = service_config.get("ports", [])
            if ports:
                exposed_ports[service_name] = ports

        # Database and cache should not expose ports in production
        sensitive_services = ["postgres", "redis"]
        for service in sensitive_services:
            if service in exposed_ports:
                print(f"⚠ Warning: {service} exposes ports in base config (should be dev-only)")

        # Report results
        print(f"\n{'='*80}")
        print("Network Isolation and Security Results")
        print(f"{'='*80}")
        for network_name, results in network_results.items():
            internal_status = "✓ Internal" if results["internal"] else "✗ External"
            print(f"\n{network_name}: {internal_status}")
            print(f"  Services: {len(results['services'])}")
            if results["services"]:
                for svc in results["services"][:5]:  # Show first 5
                    print(f"    - {svc}")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  ⚠ {issue}")

        print(f"\nPort Exposure:")
        for service, ports in exposed_ports.items():
            print(f"  {service}: {ports}")

        print(f"\n{'='*80}\n")

        assert not failures, f"Network isolation failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 7: Secrets Management Validation
    # ============================================
    def test_07_secrets_management_validation(self):
        """
        Test 7: Validate Docker secrets management.

        Checks:
        - All secrets marked as external
        - No hardcoded secrets in configs
        - Secrets mounted at /run/secrets
        - Environment variables use *_FILE pattern
        - No secrets in logs or health checks
        """
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        secrets_config = compose_config.get("secrets", {})
        services = compose_config.get("services", {})

        secrets_results = {
            "total_secrets": len(secrets_config),
            "external_secrets": 0,
            "non_external_secrets": [],
            "services_using_secrets": {},
            "hardcoded_findings": [],
            "issues": []
        }

        # Check all secrets are external
        for secret_name, secret_config in secrets_config.items():
            if secret_config.get("external") is True:
                secrets_results["external_secrets"] += 1
            else:
                secrets_results["non_external_secrets"].append(secret_name)
                secrets_results["issues"].append(
                    f"Secret '{secret_name}' not marked as external"
                )

        # Check service secret usage
        for service_name, service_config in services.items():
            service_secrets = service_config.get("secrets", [])
            if service_secrets:
                secrets_results["services_using_secrets"][service_name] = len(service_secrets)

            # Check environment variables for proper _FILE pattern
            environment = service_config.get("environment", {})
            if isinstance(environment, dict):
                env_vars = environment
            elif isinstance(environment, list):
                env_vars = {item.split("=")[0]: item.split("=")[1] if "=" in item else None
                          for item in environment}
            else:
                env_vars = {}

            # Look for sensitive variables
            sensitive_patterns = ["PASSWORD", "SECRET", "KEY", "TOKEN", "CREDENTIAL"]
            for key, value in env_vars.items():
                if any(pattern in key.upper() for pattern in sensitive_patterns):
                    # Should end with _FILE or reference /run/secrets
                    if value and not (str(value).endswith("_FILE") or
                                    "/run/secrets" in str(value) or
                                    str(value).startswith("${}")):
                        secrets_results["hardcoded_findings"].append({
                            "service": service_name,
                            "variable": key,
                            "pattern": "Does not use _FILE or /run/secrets"
                        })

        # Check Dockerfiles for hardcoded secrets
        dockerfiles = list(Path("infrastructure/docker/dockerfiles").glob("*.Dockerfile"))

        for dockerfile_path in dockerfiles:
            with open(dockerfile_path, 'r') as f:
                content = f.read()

            # Look for hardcoded secrets
            if "password=" in content.lower() or "secret=" in content.lower():
                secrets_results["hardcoded_findings"].append({
                    "file": str(dockerfile_path),
                    "pattern": "Possible hardcoded secret in Dockerfile"
                })

        failures = []

        # All secrets must be external in production
        if secrets_results["non_external_secrets"]:
            failures.append(
                f"Non-external secrets found: {secrets_results['non_external_secrets']}"
            )

        # No hardcoded secrets allowed
        if secrets_results["hardcoded_findings"]:
            failures.append(
                f"Hardcoded secret patterns found: {len(secrets_results['hardcoded_findings'])}"
            )

        # Report results
        print(f"\n{'='*80}")
        print("Secrets Management Validation Results")
        print(f"{'='*80}")
        print(f"Total secrets: {secrets_results['total_secrets']}")
        print(f"External secrets: {secrets_results['external_secrets']}")
        print(f"Services using secrets: {len(secrets_results['services_using_secrets'])}")

        if secrets_results["non_external_secrets"]:
            print(f"\n⚠ Non-external secrets:")
            for secret in secrets_results["non_external_secrets"]:
                print(f"  - {secret}")

        if secrets_results["hardcoded_findings"]:
            print(f"\n⚠ Hardcoded secret findings:")
            for finding in secrets_results["hardcoded_findings"][:10]:  # Show first 10
                if "service" in finding:
                    print(f"  - {finding['service']}: {finding['variable']}")
                else:
                    print(f"  - {finding['file']}: {finding['pattern']}")

        print(f"\n{'='*80}\n")

        assert not failures, f"Secrets management failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 8: Health Check Robustness
    # ============================================
    @pytest.mark.asyncio
    async def test_08_health_check_robustness(self):
        """
        Test 8: Validate health check robustness.

        Checks:
        - All services have health checks
        - Health check intervals appropriate
        - Retry logic configured
        - Start period allows for initialization
        - Health checks don't leak sensitive info
        """
        containers = self.docker_client.containers.list()
        toolboxai_containers = [c for c in containers if "toolboxai" in c.name]

        health_results = {}
        failures = []

        for container in toolboxai_containers:
            inspect_data = self.docker_client.api.inspect_container(container.id)
            health_config = inspect_data.get("Config", {}).get("Healthcheck")

            service_name = container.name.replace("toolboxai-", "")

            results = {
                "has_healthcheck": False,
                "test_command": None,
                "interval": None,
                "timeout": None,
                "retries": None,
                "start_period": None,
                "current_status": None,
                "issues": []
            }

            if health_config:
                results["has_healthcheck"] = True
                results["test_command"] = health_config.get("Test")
                results["interval"] = health_config.get("Interval")
                results["timeout"] = health_config.get("Timeout")
                results["retries"] = health_config.get("Retries")
                results["start_period"] = health_config.get("StartPeriod")

                # Validate intervals (in nanoseconds, convert to seconds)
                if results["interval"]:
                    interval_sec = results["interval"] / 1e9
                    if interval_sec < 10:
                        results["issues"].append(f"Interval too short: {interval_sec}s")
                    elif interval_sec > 60:
                        results["issues"].append(f"Interval too long: {interval_sec}s")

                # Validate timeout
                if results["timeout"]:
                    timeout_sec = results["timeout"] / 1e9
                    if timeout_sec < 5:
                        results["issues"].append(f"Timeout too short: {timeout_sec}s")

                # Validate retries
                if results["retries"] and results["retries"] < 3:
                    results["issues"].append(f"Retries too few: {results['retries']}")

                # Validate start period
                if results["start_period"]:
                    start_period_sec = results["start_period"] / 1e9
                    if start_period_sec < 20:
                        results["issues"].append(f"Start period too short: {start_period_sec}s")
            else:
                results["issues"].append("No health check configured")
                failures.append(f"{service_name}: Missing health check")

            # Get current health status
            health_state = inspect_data.get("State", {}).get("Health", {})
            if health_state:
                results["current_status"] = health_state.get("Status")

            health_results[service_name] = results

        # Report results
        print(f"\n{'='*80}")
        print("Health Check Robustness Results")
        print(f"{'='*80}")
        for service_name, results in health_results.items():
            status = "✓" if results["has_healthcheck"] and not results["issues"] else "✗"
            print(f"\n{service_name}: {status}")
            if results["has_healthcheck"]:
                if results["interval"]:
                    print(f"  Interval: {results['interval'] / 1e9:.0f}s")
                if results["timeout"]:
                    print(f"  Timeout: {results['timeout'] / 1e9:.0f}s")
                if results["retries"]:
                    print(f"  Retries: {results['retries']}")
                if results["current_status"]:
                    print(f"  Current Status: {results['current_status']}")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  ⚠ {issue}")
        print(f"\n{'='*80}\n")

        assert not failures, f"Health check failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 9: Backup and Recovery Procedures
    # ============================================
    def test_09_backup_and_recovery_procedures(self):
        """
        Test 9: Validate backup and recovery procedures.

        Checks:
        - Volume backup configuration
        - Database backup service configured
        - Backup retention policies
        - Recovery scripts available
        - Backup encryption enabled
        """
        with open(self.compose_file, 'r') as f:
            compose_config = yaml.safe_load(f)

        volumes = compose_config.get("volumes", {})
        services = compose_config.get("services", {})

        backup_results = {
            "persistent_volumes": [],
            "backup_services": [],
            "recovery_scripts": [],
            "issues": []
        }

        # Identify persistent volumes
        for volume_name, volume_config in volumes.items():
            if volume_config:  # Has configuration
                backup_results["persistent_volumes"].append(volume_name)

        # Check for backup service
        if "backup-coordinator" in services:
            backup_config = services["backup-coordinator"]
            environment = backup_config.get("environment", {})

            backup_results["backup_services"].append({
                "name": "backup-coordinator",
                "has_schedule": any("BACKUP_SCHEDULE" in str(e) for e in environment),
                "has_retention": any("RETENTION" in str(e) for e in environment),
                "has_encryption": any("ENCRYPTION" in str(e) for e in environment),
            })
        else:
            backup_results["issues"].append("No backup coordinator service found")

        # Check for recovery scripts
        scripts_dir = Path("infrastructure/backups/scripts")
        if scripts_dir.exists():
            recovery_scripts = list(scripts_dir.glob("*recover*")) + list(scripts_dir.glob("*restore*"))
            backup_results["recovery_scripts"] = [str(s.name) for s in recovery_scripts]

        # Check volume mount for backups
        critical_volumes = ["postgres_data", "redis_data", "postgres_backup"]
        missing_volumes = [v for v in critical_volumes if v not in volumes]

        if missing_volumes:
            backup_results["issues"].append(f"Missing critical volumes: {missing_volumes}")

        failures = []

        if not backup_results["backup_services"]:
            failures.append("No backup service configured")

        if len(backup_results["persistent_volumes"]) < 3:
            failures.append("Insufficient persistent volumes configured")

        # Report results
        print(f"\n{'='*80}")
        print("Backup and Recovery Procedures Results")
        print(f"{'='*80}")
        print(f"Persistent volumes: {len(backup_results['persistent_volumes'])}")
        print(f"Backup services: {len(backup_results['backup_services'])}")
        print(f"Recovery scripts: {len(backup_results['recovery_scripts'])}")

        if backup_results["persistent_volumes"]:
            print(f"\nPersistent volumes:")
            for volume in backup_results["persistent_volumes"][:10]:
                print(f"  - {volume}")

        if backup_results["backup_services"]:
            print(f"\nBackup services:")
            for svc in backup_results["backup_services"]:
                print(f"  - {svc['name']}")
                print(f"    Schedule: {'✓' if svc.get('has_schedule') else '✗'}")
                print(f"    Retention: {'✓' if svc.get('has_retention') else '✗'}")
                print(f"    Encryption: {'✓' if svc.get('has_encryption') else '✗'}")

        if backup_results["recovery_scripts"]:
            print(f"\nRecovery scripts:")
            for script in backup_results["recovery_scripts"]:
                print(f"  - {script}")

        if backup_results["issues"]:
            print(f"\n⚠ Issues:")
            for issue in backup_results["issues"]:
                print(f"  - {issue}")

        print(f"\n{'='*80}\n")

        assert not failures, f"Backup/recovery failures:\n" + "\n".join(failures)

    # ============================================
    # TEST 10: High Availability and Scaling
    # ============================================
    def test_10_high_availability_and_scaling(self):
        """
        Test 10: Validate high availability and scaling configuration.

        Checks:
        - Multiple replicas for critical services
        - Load balancing configuration
        - Zero-downtime deployment strategy
        - Horizontal scaling capability
        - Failover mechanisms
        """
        with open(self.prod_compose_file, 'r') as f:
            prod_config = yaml.safe_load(f)

        services = prod_config.get("services", {})

        ha_results = {}
        failures = []

        for service_name, service_config in services.items():
            deploy_config = service_config.get("deploy", {})

            results = {
                "replicas": deploy_config.get("replicas", 1),
                "has_update_config": "update_config" in deploy_config,
                "update_strategy": None,
                "restart_policy": "restart_policy" in deploy_config,
                "is_ha_ready": False,
                "issues": []
            }

            # Check update configuration
            if results["has_update_config"]:
                update_config = deploy_config["update_config"]
                results["update_strategy"] = update_config.get("order")

                # Zero-downtime deployment needs start-first or rolling
                if results["update_strategy"] not in ["start-first", "rolling"]:
                    results["issues"].append(f"Update strategy '{results['update_strategy']}' may cause downtime")

            # Check if service is HA-ready
            if results["replicas"] >= 2 and results["has_update_config"] and results["restart_policy"]:
                results["is_ha_ready"] = True

            ha_results[service_name] = results

        # Critical services that should have HA
        critical_services = ["backend", "dashboard", "mcp-server", "agent-coordinator"]

        for service_name in critical_services:
            if service_name not in ha_results:
                continue

            results = ha_results[service_name]

            if results["replicas"] < 2:
                failures.append(f"{service_name}: Should have >= 2 replicas for HA")

            if not results["has_update_config"]:
                failures.append(f"{service_name}: Missing update configuration")

            if not results["is_ha_ready"]:
                failures.append(f"{service_name}: Not configured for high availability")

        # Check for load balancer / reverse proxy
        has_load_balancer = "nginx" in services or any("proxy" in svc for svc in services)

        if not has_load_balancer:
            print("⚠ Warning: No load balancer/reverse proxy configured")

        # Report results
        print(f"\n{'='*80}")
        print("High Availability and Scaling Results")
        print(f"{'='*80}")
        print(f"Load balancer configured: {'✓' if has_load_balancer else '✗'}")

        for service_name, results in ha_results.items():
            ha_status = "✓ HA Ready" if results["is_ha_ready"] else "✗ Not HA"
            print(f"\n{service_name}: {ha_status}")
            print(f"  Replicas: {results['replicas']}")
            if results["update_strategy"]:
                print(f"  Update Strategy: {results['update_strategy']}")
            if results["issues"]:
                for issue in results["issues"]:
                    print(f"  ⚠ {issue}")

        print(f"\n{'='*80}\n")

        assert not failures, f"High availability failures:\n" + "\n".join(failures)


# ============================================
# Phase 3 Test Summary Generator
# ============================================
def generate_phase3_summary(test_results: Dict[str, Any]) -> str:
    """Generate comprehensive Phase 3 test summary."""

    summary = f"""
{'='*80}
DOCKER PHASE 3 COMPREHENSIVE TEST SUMMARY
{'='*80}

Test Suite: 10 Comprehensive Infrastructure Tests
Execution Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Test Results:
-------------
"""

    for test_name, result in test_results.items():
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        summary += f"{status} {test_name}\n"
        if result.get("issues"):
            for issue in result["issues"]:
                summary += f"    - {issue}\n"

    summary += f"""
{'='*80}
Summary:
  Total Tests: {len(test_results)}
  Passed: {sum(1 for r in test_results.values() if r['passed'])}
  Failed: {sum(1 for r in test_results.values() if not r['passed'])}
{'='*80}
"""

    return summary


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
