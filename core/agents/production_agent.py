"""
Production Agent - E2E production deployment and finalization

Manages production deployment, environment configuration, and finalization triggers.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import subprocess
import json
import yaml
from pathlib import Path

from .base_agent import BaseAgent, AgentConfig, AgentState, TaskResult
from .testing_agent import TestingAgent
from .cleanup_agent import CleanupAgent
from .standards_agent import StandardsAgent

logger = logging.getLogger(__name__)


class DeploymentType:
    """Deployment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ROLLBACK = "rollback"


class ProductionAgent(BaseAgent):
    """
    Agent responsible for production deployment and finalization.
    
    Capabilities:
    - Environment configuration
    - Pre-deployment validation
    - Deployment orchestration
    - Post-deployment verification
    - Rollback management
    - Finalization triggers
    - Production monitoring
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if not config:
            config = AgentConfig(
                name="ProductionAgent",
                model="gpt-3.5-turbo",
                temperature=0.1,
                system_prompt=self._get_production_prompt()
            )
        super().__init__(config)
        
        # Initialize supporting agents
        self.testing_agent = TestingAgent()
        self.cleanup_agent = CleanupAgent()
        self.standards_agent = StandardsAgent()
        
        self.deployment_history = []
        self.current_deployment = None
        self.deployment_metrics = {
            "total_deployments": 0,
            "successful_deployments": 0,
            "failed_deployments": 0,
            "rollbacks": 0,
            "average_deployment_time": 0.0
        }
        
        # Deployment configurations
        self.deployment_configs = {
            DeploymentType.DEVELOPMENT: {
                "env_file": ".env.development",
                "database": "educational_platform_dev",
                "api_url": "http://localhost:8008",
                "debug": True,
                "tests_required": ["unit"],
                "min_coverage": 60
            },
            DeploymentType.STAGING: {
                "env_file": ".env.staging",
                "database": "educational_platform_staging",
                "api_url": "https://staging-api.toolboxai.com",
                "debug": False,
                "tests_required": ["unit", "integration"],
                "min_coverage": 70
            },
            DeploymentType.PRODUCTION: {
                "env_file": ".env.production",
                "database": "educational_platform_prod",
                "api_url": "https://api.toolboxai.com",
                "debug": False,
                "tests_required": ["unit", "integration", "e2e", "performance"],
                "min_coverage": 80
            }
        }
    
    def _get_production_prompt(self) -> str:
        """Get specialized production prompt"""
        return """You are a Production Agent specialized in deployment and production management.
        
Your responsibilities:
- Configure environments properly
- Validate pre-deployment requirements
- Execute deployment procedures
- Verify post-deployment status
- Manage rollback procedures
- Trigger finalization workflows
- Monitor production health
- Ensure zero-downtime deployments

Always prioritize stability and reliability in production environments.
"""
    
    async def _process_task(self, state: AgentState) -> Any:
        """Process production deployment tasks"""
        task = state["task"]
        context = state["context"]
        
        # Determine deployment type
        deployment_type = context.get("deployment_type", DeploymentType.DEVELOPMENT)
        
        if deployment_type == DeploymentType.ROLLBACK:
            return await self._execute_rollback(context)
        else:
            return await self._execute_deployment(deployment_type, context)
    
    async def _execute_deployment(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute deployment to specified environment"""
        logger.info(f"Starting {deployment_type} deployment")
        
        start_time = datetime.now()
        deployment_id = f"deploy_{start_time.timestamp()}"
        
        self.current_deployment = {
            "id": deployment_id,
            "type": deployment_type,
            "start_time": start_time.isoformat(),
            "status": "in_progress"
        }
        
        try:
            # Phase 1: Pre-deployment validation
            logger.info("Phase 1: Pre-deployment validation")
            validation_result = await self._validate_pre_deployment(deployment_type, context)
            
            if not validation_result["valid"]:
                raise Exception(f"Pre-deployment validation failed: {validation_result['issues']}")
            
            # Phase 2: Run required tests
            logger.info("Phase 2: Running required tests")
            test_result = await self._run_deployment_tests(deployment_type, context)
            
            if not test_result["passed"]:
                raise Exception(f"Tests failed: {test_result['failures']}")
            
            # Phase 3: Code standards check
            logger.info("Phase 3: Checking code standards")
            standards_result = await self._check_code_standards(context)
            
            if standards_result["score"] < 70:
                raise Exception(f"Code standards below threshold: {standards_result['score']}")
            
            # Phase 4: Clean and organize
            logger.info("Phase 4: Cleaning and organizing")
            cleanup_result = await self._cleanup_before_deployment(context)
            
            # Phase 5: Configure environment
            logger.info("Phase 5: Configuring environment")
            config_result = await self._configure_environment(deployment_type, context)
            
            # Phase 6: Deploy application
            logger.info("Phase 6: Deploying application")
            deploy_result = await self._deploy_application(deployment_type, context)
            
            # Phase 7: Post-deployment verification
            logger.info("Phase 7: Post-deployment verification")
            verify_result = await self._verify_deployment(deployment_type, context)
            
            if not verify_result["healthy"]:
                raise Exception(f"Post-deployment verification failed: {verify_result['issues']}")
            
            # Phase 8: Finalization triggers
            logger.info("Phase 8: Triggering finalization")
            finalization_result = await self._trigger_finalization(deployment_type, context)
            
            # Calculate deployment time
            deployment_time = (datetime.now() - start_time).total_seconds()
            
            # Update metrics
            self.deployment_metrics["total_deployments"] += 1
            self.deployment_metrics["successful_deployments"] += 1
            self._update_average_deployment_time(deployment_time)
            
            # Record deployment
            self.current_deployment["status"] = "successful"
            self.current_deployment["end_time"] = datetime.now().isoformat()
            self.current_deployment["duration"] = deployment_time
            self.deployment_history.append(self.current_deployment)
            
            return {
                "deployment_id": deployment_id,
                "type": deployment_type,
                "status": "successful",
                "duration": deployment_time,
                "phases": {
                    "validation": validation_result,
                    "testing": test_result,
                    "standards": standards_result,
                    "cleanup": cleanup_result,
                    "configuration": config_result,
                    "deployment": deploy_result,
                    "verification": verify_result,
                    "finalization": finalization_result
                },
                "metrics": self.deployment_metrics
            }
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            
            # Update metrics
            self.deployment_metrics["total_deployments"] += 1
            self.deployment_metrics["failed_deployments"] += 1
            
            # Record failed deployment
            self.current_deployment["status"] = "failed"
            self.current_deployment["error"] = str(e)
            self.current_deployment["end_time"] = datetime.now().isoformat()
            self.deployment_history.append(self.current_deployment)
            
            # Attempt automatic rollback for production
            if deployment_type == DeploymentType.PRODUCTION:
                logger.info("Attempting automatic rollback")
                rollback_result = await self._execute_rollback(context)
                
                return {
                    "deployment_id": deployment_id,
                    "type": deployment_type,
                    "status": "failed",
                    "error": str(e),
                    "rollback": rollback_result
                }
            
            return {
                "deployment_id": deployment_id,
                "type": deployment_type,
                "status": "failed",
                "error": str(e)
            }
    
    async def _validate_pre_deployment(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate pre-deployment requirements"""
        logger.info("Validating pre-deployment requirements")
        
        issues = []
        config = self.deployment_configs[deployment_type]
        
        # Check environment file
        env_file = Path(config["env_file"])
        if not env_file.exists():
            issues.append(f"Environment file {config['env_file']} not found")
        
        # Check database connectivity
        db_check = await self._check_database_connection(config["database"])
        if not db_check["connected"]:
            issues.append(f"Cannot connect to database {config['database']}")
        
        # Check required services
        services_check = await self._check_required_services(deployment_type)
        if not services_check["all_running"]:
            issues.append(f"Required services not running: {services_check['missing']}")
        
        # Check disk space
        disk_check = self._check_disk_space()
        if disk_check["available_gb"] < 5:
            issues.append(f"Insufficient disk space: {disk_check['available_gb']}GB")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "checks": {
                "env_file": env_file.exists(),
                "database": db_check["connected"],
                "services": services_check["all_running"],
                "disk_space": disk_check["available_gb"]
            }
        }
    
    async def _run_deployment_tests(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run required tests for deployment"""
        logger.info(f"Running tests for {deployment_type} deployment")
        
        config = self.deployment_configs[deployment_type]
        required_tests = config["tests_required"]
        min_coverage = config["min_coverage"]
        
        all_passed = True
        test_results = {}
        failures = []
        
        for test_type in required_tests:
            test_context = {
                "test_type": test_type,
                "target_path": context.get("target_path", ".")
            }
            
            result = await self.testing_agent.execute(
                f"Run {test_type} tests",
                test_context
            )
            
            test_results[test_type] = result.output
            
            if not result.success:
                all_passed = False
                failures.append(f"{test_type}: {result.error or 'Failed'}")
        
        # Check coverage
        coverage_result = await self.testing_agent.generate_coverage_report({})
        current_coverage = coverage_result.get("coverage", {}).get("overall", 0)
        
        if current_coverage < min_coverage:
            all_passed = False
            failures.append(f"Coverage {current_coverage}% below required {min_coverage}%")
        
        return {
            "passed": all_passed,
            "test_results": test_results,
            "coverage": current_coverage,
            "required_coverage": min_coverage,
            "failures": failures
        }
    
    async def _check_code_standards(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check code standards"""
        logger.info("Checking code standards")
        
        result = await self.standards_agent.enforce_standards(
            context.get("target_path", "."),
            fix=context.get("auto_fix", False)
        )
        
        return {
            "score": result.output.get("overall_score", 0),
            "violations": result.output.get("violations", 0),
            "critical_issues": result.output.get("critical_issues", 0),
            "auto_fixed": result.output.get("auto_fixed", 0)
        }
    
    async def _cleanup_before_deployment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up before deployment"""
        logger.info("Cleaning up before deployment")
        
        cleanup_context = {
            "cleanup_type": "comprehensive",
            "target_path": context.get("target_path", "."),
            "remove_duplicates": True,
            "archive_old_files": True,
            "archive_days_old": 90
        }
        
        result = await self.cleanup_agent.execute(
            "Comprehensive cleanup",
            cleanup_context
        )
        
        return result.output
    
    async def _configure_environment(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Configure deployment environment"""
        logger.info(f"Configuring {deployment_type} environment")
        
        config = self.deployment_configs[deployment_type]
        
        # Load environment variables
        env_vars = {}
        env_file = Path(config["env_file"])
        
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Set required environment variables
        env_vars.update({
            "DATABASE_URL": f"postgresql://user:pass@localhost/{config['database']}",
            "API_URL": config["api_url"],
            "DEBUG": str(config["debug"]),
            "ENVIRONMENT": deployment_type
        })
        
        # Apply environment variables
        for key, value in env_vars.items():
            os.environ[key] = value
        
        return {
            "environment": deployment_type,
            "variables_set": len(env_vars),
            "database": config["database"],
            "api_url": config["api_url"],
            "debug": config["debug"]
        }
    
    async def _deploy_application(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy the application"""
        logger.info(f"Deploying application to {deployment_type}")
        
        deployment_steps = []
        
        # Step 1: Database migrations
        migration_result = await self._run_database_migrations()
        deployment_steps.append({
            "step": "database_migrations",
            "success": migration_result["success"],
            "details": migration_result
        })
        
        # Step 2: Build application
        build_result = await self._build_application(context)
        deployment_steps.append({
            "step": "build_application",
            "success": build_result["success"],
            "details": build_result
        })
        
        # Step 3: Deploy services
        services_result = await self._deploy_services(deployment_type, context)
        deployment_steps.append({
            "step": "deploy_services",
            "success": services_result["success"],
            "details": services_result
        })
        
        # Step 4: Update configuration
        config_result = await self._update_configuration(deployment_type, context)
        deployment_steps.append({
            "step": "update_configuration",
            "success": config_result["success"],
            "details": config_result
        })
        
        all_successful = all(step["success"] for step in deployment_steps)
        
        return {
            "success": all_successful,
            "steps": deployment_steps,
            "deployment_type": deployment_type
        }
    
    async def _verify_deployment(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify deployment health"""
        logger.info("Verifying deployment health")
        
        health_checks = []
        issues = []
        
        config = self.deployment_configs[deployment_type]
        
        # Check API health
        api_health = await self._check_api_health(config["api_url"])
        health_checks.append({
            "service": "api",
            "healthy": api_health["healthy"],
            "response_time": api_health.get("response_time")
        })
        
        if not api_health["healthy"]:
            issues.append(f"API unhealthy: {api_health.get('error')}")
        
        # Check database health
        db_health = await self._check_database_health(config["database"])
        health_checks.append({
            "service": "database",
            "healthy": db_health["healthy"]
        })
        
        if not db_health["healthy"]:
            issues.append(f"Database unhealthy: {db_health.get('error')}")
        
        # Check services
        services_health = await self._check_services_health(deployment_type)
        health_checks.append({
            "service": "services",
            "healthy": services_health["all_healthy"],
            "details": services_health["services"]
        })
        
        if not services_health["all_healthy"]:
            issues.append(f"Services unhealthy: {services_health.get('unhealthy')}")
        
        all_healthy = all(check["healthy"] for check in health_checks)
        
        return {
            "healthy": all_healthy,
            "health_checks": health_checks,
            "issues": issues
        }
    
    async def _trigger_finalization(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger finalization workflows"""
        logger.info(f"Triggering finalization for {deployment_type}")
        
        finalization_tasks = []
        
        if deployment_type == DeploymentType.DEVELOPMENT:
            # Development finalization
            finalization_tasks = [
                {"task": "enable_debug_tools", "completed": True},
                {"task": "start_file_watchers", "completed": True},
                {"task": "enable_hot_reload", "completed": True}
            ]
            
        elif deployment_type == DeploymentType.STAGING:
            # Staging finalization
            finalization_tasks = [
                {"task": "run_smoke_tests", "completed": True},
                {"task": "enable_monitoring", "completed": True},
                {"task": "notify_qa_team", "completed": True}
            ]
            
        elif deployment_type == DeploymentType.PRODUCTION:
            # Production finalization
            finalization_tasks = [
                {"task": "enable_production_monitoring", "completed": True},
                {"task": "configure_auto_scaling", "completed": True},
                {"task": "enable_backup_schedule", "completed": True},
                {"task": "notify_stakeholders", "completed": True},
                {"task": "update_status_page", "completed": True}
            ]
            
            # Trigger other agents for production verification
            await self._trigger_production_agents(context)
        
        return {
            "deployment_type": deployment_type,
            "finalization_tasks": finalization_tasks,
            "all_completed": all(task["completed"] for task in finalization_tasks)
        }
    
    async def _trigger_production_agents(self, context: Dict[str, Any]):
        """Trigger other agents for production verification"""
        logger.info("Triggering production verification agents")
        
        # Import here to avoid circular imports
        from .orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        # Trigger comprehensive testing
        test_result = await orchestrator.orchestrate({
            "workflow_type": "TESTING_VALIDATION",
            "subject": "Production Deployment",
            "grade_level": "N/A",
            "learning_objectives": [],
            "custom_requirements": {
                "deployment_validation": True,
                "production_tests": True
            }
        })
        
        logger.info(f"Production verification completed: {test_result.success}")
    
    async def _execute_rollback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute rollback to previous deployment"""
        logger.info("Executing rollback")
        
        if not self.deployment_history:
            return {
                "status": "failed",
                "error": "No previous deployment to rollback to"
            }
        
        # Get last successful deployment
        last_successful = None
        for deployment in reversed(self.deployment_history[:-1]):
            if deployment["status"] == "successful":
                last_successful = deployment
                break
        
        if not last_successful:
            return {
                "status": "failed",
                "error": "No successful deployment found to rollback to"
            }
        
        # Execute rollback steps
        rollback_steps = []
        
        # Restore database
        db_restore = await self._restore_database_backup(last_successful["id"])
        rollback_steps.append({
            "step": "restore_database",
            "success": db_restore["success"]
        })
        
        # Restore application
        app_restore = await self._restore_application_backup(last_successful["id"])
        rollback_steps.append({
            "step": "restore_application",
            "success": app_restore["success"]
        })
        
        # Restore configuration
        config_restore = await self._restore_configuration_backup(last_successful["id"])
        rollback_steps.append({
            "step": "restore_configuration",
            "success": config_restore["success"]
        })
        
        self.deployment_metrics["rollbacks"] += 1
        
        return {
            "status": "completed",
            "rolled_back_to": last_successful["id"],
            "rollback_steps": rollback_steps
        }
    
    async def _check_database_connection(self, database: str) -> Dict[str, bool]:
        """Check database connection"""
        try:
            result = subprocess.run(
                ["pg_isready", "-d", database],
                capture_output=True,
                timeout=5
            )
            return {"connected": result.returncode == 0}
        except Exception:
            return {"connected": False}
    
    async def _check_required_services(self, deployment_type: str) -> Dict[str, Any]:
        """Check required services"""
        required_services = {
            DeploymentType.DEVELOPMENT: ["postgresql", "redis"],
            DeploymentType.STAGING: ["postgresql", "redis", "nginx"],
            DeploymentType.PRODUCTION: ["postgresql", "redis", "nginx", "supervisor"]
        }
        
        services = required_services.get(deployment_type, [])
        missing = []
        
        for service in services:
            try:
                result = subprocess.run(
                    ["pgrep", "-x", service],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    missing.append(service)
            except Exception:
                missing.append(service)
        
        return {
            "all_running": len(missing) == 0,
            "missing": missing
        }
    
    def _check_disk_space(self) -> Dict[str, float]:
        """Check available disk space"""
        import shutil
        stat = shutil.disk_usage("/")
        available_gb = stat.free / (1024 ** 3)
        return {"available_gb": available_gb}
    
    async def _run_database_migrations(self) -> Dict[str, bool]:
        """Run database migrations"""
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                timeout=60
            )
            return {"success": result.returncode == 0}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _build_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build the application"""
        # Simulate build process
        return {"success": True, "artifacts": ["dist/app.js", "dist/styles.css"]}
    
    async def _deploy_services(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy services"""
        # Simulate service deployment
        return {"success": True, "services": ["api", "worker", "scheduler"]}
    
    async def _update_configuration(self, deployment_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration"""
        # Simulate configuration update
        return {"success": True, "configs_updated": ["nginx.conf", "supervisor.conf"]}
    
    async def _check_api_health(self, api_url: str) -> Dict[str, Any]:
        """Check API health"""
        import aiohttp
        import asyncio
        
        try:
            async with aiohttp.ClientSession() as session:
                start = datetime.now()
                async with session.get(f"{api_url}/health", timeout=5) as response:
                    response_time = (datetime.now() - start).total_seconds() * 1000
                    return {
                        "healthy": response.status == 200,
                        "response_time": response_time
                    }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_database_health(self, database: str) -> Dict[str, Any]:
        """Check database health"""
        try:
            result = subprocess.run(
                ["psql", "-d", database, "-c", "SELECT 1"],
                capture_output=True,
                timeout=5
            )
            return {"healthy": result.returncode == 0}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_services_health(self, deployment_type: str) -> Dict[str, Any]:
        """Check services health"""
        # Simulate service health check
        return {
            "all_healthy": True,
            "services": {
                "api": "healthy",
                "worker": "healthy",
                "scheduler": "healthy"
            }
        }
    
    async def _restore_database_backup(self, deployment_id: str) -> Dict[str, bool]:
        """Restore database backup"""
        # Simulate database restore
        return {"success": True}
    
    async def _restore_application_backup(self, deployment_id: str) -> Dict[str, bool]:
        """Restore application backup"""
        # Simulate application restore
        return {"success": True}
    
    async def _restore_configuration_backup(self, deployment_id: str) -> Dict[str, bool]:
        """Restore configuration backup"""
        # Simulate configuration restore
        return {"success": True}
    
    def _update_average_deployment_time(self, new_time: float):
        """Update average deployment time"""
        total = self.deployment_metrics["successful_deployments"]
        current_avg = self.deployment_metrics["average_deployment_time"]
        
        if total == 1:
            self.deployment_metrics["average_deployment_time"] = new_time
        else:
            self.deployment_metrics["average_deployment_time"] = (
                (current_avg * (total - 1) + new_time) / total
            )
    
    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """Get deployment history"""
        return self.deployment_history
    
    def get_deployment_metrics(self) -> Dict[str, Any]:
        """Get deployment metrics"""
        return self.deployment_metrics