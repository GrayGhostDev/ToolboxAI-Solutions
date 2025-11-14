"""
Pipeline Monitoring Agent for GitHub Actions CI/CD Analysis.

This agent provides comprehensive monitoring and analysis of CI/CD pipelines:
- Tracks pipeline metrics (build times, success rates, failure patterns)
- Generates performance reports and optimization suggestions
- Monitors resource usage and deployment metrics
- Analyzes pipeline bottlenecks and provides DORA metrics
"""

import asyncio
import json
import logging
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Optional

import aiohttp
import yaml

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


class PipelineMonitoringAgent(BaseGitHubAgent):
    """GitHub Actions CI/CD pipeline monitoring and analysis agent."""

    def __init__(self, config_path: Optional[str] = None, github_token: Optional[str] = None):
        """Initialize the Pipeline Monitoring Agent.

        Args:
            config_path: Path to configuration file
            github_token: GitHub API token for authentication
        """
        super().__init__(config_path)
        self.github_token = github_token or self._get_github_token()
        self.base_url = "https://api.github.com"
        self.session: Optional[aiohttp.ClientSession] = None

        # Pipeline monitoring metrics
        self.pipeline_metrics = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "cancelled_runs": 0,
            "average_duration": 0.0,
            "failure_patterns": defaultdict(int),
            "bottlenecks": [],
            "resource_usage": {},
            "deployment_frequency": 0,
            "lead_time": 0.0,
            "mttr": 0.0,
            "change_failure_rate": 0.0,
        }

    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from environment or config."""
        import os

        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        if not token:
            logger.warning("No GitHub token found. API requests will be limited.")
        return token

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.session:
            headers = {}
            if self.github_token:
                headers["Authorization"] = f"token {self.github_token}"
                headers["Accept"] = "application/vnd.github.v3+json"

            self.session = aiohttp.ClientSession(headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            self.session = None

    async def analyze(
        self,
        repository: str,
        days_back: int = 30,
        include_resource_usage: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Main pipeline analysis method.

        Args:
            repository: Repository in format 'owner/repo'
            days_back: Number of days to analyze
            include_resource_usage: Whether to analyze resource usage
            **kwargs: Additional analysis parameters

        Returns:
            Comprehensive pipeline analysis results
        """
        self.update_metrics(operations_performed=1)

        try:
            async with self:
                # Collect pipeline metrics
                metrics = await self.collect_pipeline_metrics(repository, days_back)

                # Analyze build performance
                performance = await self.analyze_build_performance(metrics)

                # Detect anomalies
                anomalies = await self.detect_anomalies(metrics)

                # Analyze failure patterns
                failure_analysis = await self.analyze_failure_patterns(metrics)

                # Calculate DORA metrics
                dora_metrics = await self.calculate_deployment_metrics(repository, days_back)

                # Generate optimization suggestions
                suggestions = await self.provide_optimization_suggestions(
                    metrics, performance, anomalies, failure_analysis
                )

                # Optional resource usage analysis
                resource_usage = {}
                if include_resource_usage:
                    resource_usage = await self._analyze_resource_usage(metrics)

                results = {
                    "repository": repository,
                    "analysis_period": f"{days_back} days",
                    "timestamp": datetime.now().isoformat(),
                    "pipeline_metrics": metrics,
                    "build_performance": performance,
                    "anomalies": anomalies,
                    "failure_analysis": failure_analysis,
                    "dora_metrics": dora_metrics,
                    "resource_usage": resource_usage,
                    "optimization_suggestions": suggestions,
                    "health_score": self._calculate_health_score(metrics, performance),
                }

                await self.log_operation(
                    "pipeline_analysis",
                    {
                        "repository": repository,
                        "metrics_collected": len(metrics.get("workflow_runs", [])),
                        "health_score": results["health_score"],
                    },
                )

                return results

        except Exception as e:
            self.update_metrics(errors_encountered=1)
            logger.error(f"Error in pipeline analysis: {e}")
            return {
                "error": str(e),
                "repository": repository,
                "timestamp": datetime.now().isoformat(),
            }

    async def collect_pipeline_metrics(
        self, repository: str, days_back: int = 30
    ) -> dict[str, Any]:
        """Gather metrics from GitHub Actions workflows.

        Args:
            repository: Repository in format 'owner/repo'
            days_back: Number of days to look back

        Returns:
            Collected pipeline metrics
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        since_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Get workflow runs
        url = f"{self.base_url}/repos/{repository}/actions/runs"
        params = {"per_page": 100, "created": f">={since_date}", "status": "completed"}

        all_runs = []
        page = 1

        while page <= 10:  # Limit to avoid rate limits
            params["page"] = page

            try:
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.warning(f"API request failed with status {response.status}")
                        break

                    data = await response.json()
                    runs = data.get("workflow_runs", [])

                    if not runs:
                        break

                    all_runs.extend(runs)

                    # Check if we have more pages
                    if len(runs) < params["per_page"]:
                        break

                    page += 1

                    # Rate limiting
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching workflow runs: {e}")
                break

        # Get workflow definitions
        workflows = await self._get_workflows(repository)

        # Process runs data
        processed_metrics = self._process_workflow_runs(all_runs, workflows)

        return {
            "repository": repository,
            "collection_date": datetime.now().isoformat(),
            "total_runs": len(all_runs),
            "workflow_runs": all_runs,
            "workflows": workflows,
            "processed_metrics": processed_metrics,
        }

    async def analyze_build_performance(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Analyze build times and performance trends.

        Args:
            metrics: Collected pipeline metrics

        Returns:
            Build performance analysis
        """
        runs = metrics.get("workflow_runs", [])

        if not runs:
            return {"error": "No workflow runs available for analysis"}

        # Extract durations and timestamps
        durations = []
        durations_by_workflow = defaultdict(list)
        durations_by_day = defaultdict(list)

        for run in runs:
            if run.get("conclusion") in ["success", "failure"]:
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated_at - created_at).total_seconds()

                durations.append(duration)
                durations_by_workflow[run["name"]].append(duration)
                durations_by_day[created_at.date().isoformat()].append(duration)

        if not durations:
            return {"error": "No completed runs with valid durations"}

        # Calculate statistics
        avg_duration = statistics.mean(durations)
        median_duration = statistics.median(durations)
        std_duration = statistics.stdev(durations) if len(durations) > 1 else 0

        # Identify slow workflows
        workflow_performance = {}
        for workflow, workflow_durations in durations_by_workflow.items():
            workflow_performance[workflow] = {
                "average_duration": statistics.mean(workflow_durations),
                "median_duration": statistics.median(workflow_durations),
                "run_count": len(workflow_durations),
                "slowest_run": max(workflow_durations),
                "fastest_run": min(workflow_durations),
            }

        # Trend analysis
        daily_trends = {}
        for day, day_durations in durations_by_day.items():
            daily_trends[day] = {
                "average_duration": statistics.mean(day_durations),
                "run_count": len(day_durations),
            }

        return {
            "overall_statistics": {
                "average_duration_seconds": avg_duration,
                "median_duration_seconds": median_duration,
                "standard_deviation": std_duration,
                "total_runs_analyzed": len(durations),
                "slowest_run_seconds": max(durations),
                "fastest_run_seconds": min(durations),
            },
            "workflow_performance": workflow_performance,
            "daily_trends": daily_trends,
            "performance_grade": self._grade_performance(avg_duration, std_duration),
        }

    async def detect_anomalies(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Identify unusual patterns in pipeline behavior.

        Args:
            metrics: Collected pipeline metrics

        Returns:
            Detected anomalies
        """
        runs = metrics.get("workflow_runs", [])
        anomalies = {
            "duration_anomalies": [],
            "failure_spikes": [],
            "unusual_patterns": [],
            "resource_anomalies": [],
        }

        if len(runs) < 10:
            return {
                "warning": "Insufficient data for anomaly detection",
                "anomalies": anomalies,
            }

        # Analyze duration anomalies
        durations = []
        for run in runs:
            if run.get("conclusion") in ["success", "failure"]:
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated_at - created_at).total_seconds()
                durations.append((created_at, duration, run))

        if durations:
            # Calculate threshold for anomalies (2 standard deviations)
            duration_values = [d[1] for d in durations]
            mean_duration = statistics.mean(duration_values)
            std_duration = statistics.stdev(duration_values) if len(duration_values) > 1 else 0
            threshold = mean_duration + (2 * std_duration)

            for timestamp, duration, run in durations:
                if duration > threshold:
                    anomalies["duration_anomalies"].append(
                        {
                            "run_id": run["id"],
                            "workflow": run["name"],
                            "duration_seconds": duration,
                            "threshold_seconds": threshold,
                            "timestamp": timestamp.isoformat(),
                            "deviation_factor": (
                                duration / mean_duration if mean_duration > 0 else 0
                            ),
                        }
                    )

        # Detect failure spikes
        failure_counts_by_hour = defaultdict(int)
        for run in runs:
            if run.get("conclusion") == "failure":
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                hour_key = created_at.replace(minute=0, second=0, microsecond=0)
                failure_counts_by_hour[hour_key] += 1

        if failure_counts_by_hour:
            failure_counts = list(failure_counts_by_hour.values())
            mean_failures = statistics.mean(failure_counts)
            std_failures = statistics.stdev(failure_counts) if len(failure_counts) > 1 else 0
            spike_threshold = mean_failures + (2 * std_failures)

            for hour, count in failure_counts_by_hour.items():
                if count > spike_threshold and count > 3:  # At least 3 failures
                    anomalies["failure_spikes"].append(
                        {
                            "hour": hour.isoformat(),
                            "failure_count": count,
                            "threshold": spike_threshold,
                            "severity": "high" if count > spike_threshold * 1.5 else "medium",
                        }
                    )

        # Pattern detection
        workflow_failure_rates = defaultdict(lambda: {"total": 0, "failures": 0})
        for run in runs:
            workflow_failure_rates[run["name"]]["total"] += 1
            if run.get("conclusion") == "failure":
                workflow_failure_rates[run["name"]]["failures"] += 1

        for workflow, stats in workflow_failure_rates.items():
            if stats["total"] >= 5:  # Only analyze workflows with sufficient data
                failure_rate = stats["failures"] / stats["total"]
                if failure_rate > 0.3:  # More than 30% failure rate
                    anomalies["unusual_patterns"].append(
                        {
                            "type": "high_failure_rate",
                            "workflow": workflow,
                            "failure_rate": failure_rate,
                            "total_runs": stats["total"],
                            "failed_runs": stats["failures"],
                        }
                    )

        return anomalies

    async def analyze_failure_patterns(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Find common failure causes and patterns.

        Args:
            metrics: Collected pipeline metrics

        Returns:
            Failure pattern analysis
        """
        runs = metrics.get("workflow_runs", [])
        failed_runs = [run for run in runs if run.get("conclusion") == "failure"]

        if not failed_runs:
            return {"message": "No failed runs found in the analysis period"}

        # Analyze failure patterns
        failure_by_workflow = defaultdict(int)
        failure_by_branch = defaultdict(int)
        failure_by_actor = defaultdict(int)
        failure_by_event = defaultdict(int)
        failure_by_hour = defaultdict(int)

        for run in failed_runs:
            failure_by_workflow[run["name"]] += 1
            failure_by_branch[run.get("head_branch", "unknown")] += 1
            failure_by_actor[run.get("actor", {}).get("login", "unknown")] += 1
            failure_by_event[run.get("event", "unknown")] += 1

            created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
            failure_by_hour[created_at.hour] += 1

        # Get detailed failure information for recent failures
        recent_failures = sorted(failed_runs, key=lambda x: x["created_at"], reverse=True)[:10]
        detailed_failures = []

        for run in recent_failures:
            # Try to get job details for more context
            job_details = await self._get_job_details(run["jobs_url"])
            detailed_failures.append(
                {
                    "run_id": run["id"],
                    "workflow": run["name"],
                    "branch": run.get("head_branch"),
                    "actor": run.get("actor", {}).get("login"),
                    "event": run.get("event"),
                    "created_at": run["created_at"],
                    "html_url": run["html_url"],
                    "job_details": job_details,
                }
            )

        # Calculate failure rates
        total_runs = len(runs)
        overall_failure_rate = len(failed_runs) / total_runs if total_runs > 0 else 0

        return {
            "overall_statistics": {
                "total_failures": len(failed_runs),
                "total_runs": total_runs,
                "failure_rate": overall_failure_rate,
                "analysis_period": metrics.get("collection_date"),
            },
            "failure_distribution": {
                "by_workflow": dict(failure_by_workflow),
                "by_branch": dict(failure_by_branch),
                "by_actor": dict(failure_by_actor),
                "by_event": dict(failure_by_event),
                "by_hour": dict(failure_by_hour),
            },
            "top_failing_workflows": sorted(
                failure_by_workflow.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "recent_detailed_failures": detailed_failures,
            "recommendations": self._generate_failure_recommendations(
                failure_by_workflow, failure_by_branch, overall_failure_rate
            ),
        }

    async def generate_performance_report(
        self, repository: str, days_back: int = 30, format_type: str = "markdown"
    ) -> str:
        """Create detailed performance reports.

        Args:
            repository: Repository in format 'owner/repo'
            days_back: Number of days to analyze
            format_type: Report format ('markdown', 'json', 'yaml')

        Returns:
            Formatted performance report
        """
        analysis = await self.analyze(repository, days_back)

        if format_type == "json":
            return json.dumps(analysis, indent=2, default=str)
        elif format_type == "yaml":
            return yaml.dump(analysis, default_flow_style=False)
        else:  # markdown
            return self._generate_markdown_report(analysis)

    async def calculate_deployment_metrics(
        self, repository: str, days_back: int = 30
    ) -> dict[str, Any]:
        """Calculate DORA metrics (deployment frequency, lead time, MTTR, change failure rate).

        Args:
            repository: Repository in format 'owner/repo'
            days_back: Number of days to analyze

        Returns:
            DORA metrics
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        # Get deployment-related workflow runs
        deployment_runs = await self._get_deployment_runs(repository, days_back)

        # Calculate deployment frequency
        deployment_frequency = len(deployment_runs) / days_back if days_back > 0 else 0

        # Calculate lead time (time from commit to deployment)
        lead_times = []
        for run in deployment_runs:
            if run.get("conclusion") == "success":
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                lead_time = (updated_at - created_at).total_seconds() / 3600  # Convert to hours
                lead_times.append(lead_time)

        avg_lead_time = statistics.mean(lead_times) if lead_times else 0

        # Calculate change failure rate
        total_deployments = len(deployment_runs)
        failed_deployments = len(
            [run for run in deployment_runs if run.get("conclusion") == "failure"]
        )
        change_failure_rate = failed_deployments / total_deployments if total_deployments > 0 else 0

        # Calculate MTTR (Mean Time To Recovery)
        mttr = await self._calculate_mttr(repository, days_back)

        return {
            "deployment_frequency_per_day": deployment_frequency,
            "lead_time_hours": avg_lead_time,
            "change_failure_rate": change_failure_rate,
            "mean_time_to_recovery_hours": mttr,
            "total_deployments": total_deployments,
            "successful_deployments": total_deployments - failed_deployments,
            "failed_deployments": failed_deployments,
            "dora_score": self._calculate_dora_score(
                deployment_frequency, avg_lead_time, change_failure_rate, mttr
            ),
        }

    async def provide_optimization_suggestions(
        self,
        metrics: dict[str, Any],
        performance: dict[str, Any],
        anomalies: dict[str, Any],
        failure_analysis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate actionable optimization recommendations.

        Args:
            metrics: Pipeline metrics
            performance: Performance analysis
            anomalies: Detected anomalies
            failure_analysis: Failure pattern analysis

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Performance-based suggestions
        overall_stats = performance.get("overall_statistics", {})
        avg_duration = overall_stats.get("average_duration_seconds", 0)

        if avg_duration > 1800:  # 30 minutes
            suggestions.append(
                {
                    "type": "performance",
                    "priority": "high",
                    "title": "Reduce Build Time",
                    "description": f"Average build time is {avg_duration/60:.1f} minutes, which is quite long",
                    "recommendations": [
                        "Enable build caching for dependencies",
                        "Parallelize test execution",
                        "Use matrix builds for different environments",
                        "Consider using faster runners (GitHub-hosted vs self-hosted)",
                        "Optimize Docker layer caching",
                    ],
                }
            )

        # Failure rate suggestions
        failure_stats = failure_analysis.get("overall_statistics", {})
        failure_rate = failure_stats.get("failure_rate", 0)

        if failure_rate > 0.2:  # More than 20% failure rate
            suggestions.append(
                {
                    "type": "reliability",
                    "priority": "critical",
                    "title": "High Failure Rate Detected",
                    "description": f"Failure rate is {failure_rate:.1%}, indicating reliability issues",
                    "recommendations": [
                        "Review and improve test suite reliability",
                        "Add retry mechanisms for flaky tests",
                        "Implement better error handling",
                        "Consider splitting large workflows into smaller ones",
                        "Add health checks before deployment",
                    ],
                }
            )

        # Workflow-specific suggestions
        workflow_performance = performance.get("workflow_performance", {})
        for workflow, stats in workflow_performance.items():
            if stats.get("average_duration", 0) > 2400:  # 40 minutes
                suggestions.append(
                    {
                        "type": "workflow_optimization",
                        "priority": "medium",
                        "title": f"Optimize {workflow} Workflow",
                        "description": f"Workflow '{workflow}' takes {stats['average_duration']/60:.1f} minutes on average",
                        "recommendations": [
                            f"Break down '{workflow}' into smaller, parallel jobs",
                            "Use conditional execution to skip unnecessary steps",
                            "Implement incremental builds",
                            "Cache build artifacts between jobs",
                        ],
                    }
                )

        # Anomaly-based suggestions
        duration_anomalies = anomalies.get("anomalies", {}).get("duration_anomalies", [])
        if len(duration_anomalies) > 5:
            suggestions.append(
                {
                    "type": "stability",
                    "priority": "medium",
                    "title": "Inconsistent Build Times",
                    "description": f"Detected {len(duration_anomalies)} builds with unusually long durations",
                    "recommendations": [
                        "Investigate resource contention issues",
                        "Add monitoring for external dependency availability",
                        "Implement timeout mechanisms",
                        "Consider using dedicated build agents",
                    ],
                }
            )

        # Resource optimization suggestions
        suggestions.append(
            {
                "type": "resource_optimization",
                "priority": "low",
                "title": "Resource Usage Optimization",
                "description": "General recommendations for better resource utilization",
                "recommendations": [
                    "Use appropriate runner sizes for different job types",
                    "Implement artifact cleanup after successful builds",
                    "Consider using spot instances for non-critical builds",
                    "Monitor and optimize memory usage in builds",
                ],
            }
        )

        return suggestions

    async def execute_action(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute a specific monitoring action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action results
        """
        self.update_metrics(operations_performed=1)

        actions = {
            "analyze_pipeline": self._action_analyze_pipeline,
            "generate_report": self._action_generate_report,
            "check_health": self._action_check_health,
            "get_metrics": self._action_get_metrics,
            "detect_issues": self._action_detect_issues,
            "optimize_workflows": self._action_optimize_workflows,
        }

        if action not in actions:
            return {
                "error": f"Unknown action: {action}",
                "available_actions": list(actions.keys()),
            }

        try:
            result = await actions[action](**kwargs)
            await self.log_operation(f"execute_action_{action}", kwargs)
            return result
        except Exception as e:
            self.update_metrics(errors_encountered=1)
            logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e), "action": action}

    # Action implementations
    async def _action_analyze_pipeline(
        self, repository: str, days_back: int = 30, **kwargs
    ) -> dict[str, Any]:
        """Analyze pipeline action."""
        return await self.analyze(repository, days_back, **kwargs)

    async def _action_generate_report(
        self,
        repository: str,
        days_back: int = 30,
        format_type: str = "markdown",
        **kwargs,
    ) -> dict[str, Any]:
        """Generate report action."""
        report = await self.generate_performance_report(repository, days_back, format_type)
        return {"report": report, "format": format_type}

    async def _action_check_health(self, repository: str, **kwargs) -> dict[str, Any]:
        """Check pipeline health action."""
        metrics = await self.collect_pipeline_metrics(repository, 7)  # Last 7 days
        performance = await self.analyze_build_performance(metrics)
        health_score = self._calculate_health_score(metrics, performance)

        return {
            "repository": repository,
            "health_score": health_score,
            "status": (
                "healthy"
                if health_score > 0.7
                else "needs_attention" if health_score > 0.4 else "critical"
            ),
            "last_check": datetime.now().isoformat(),
        }

    async def _action_get_metrics(
        self, repository: str, days_back: int = 30, **kwargs
    ) -> dict[str, Any]:
        """Get metrics action."""
        return await self.collect_pipeline_metrics(repository, days_back)

    async def _action_detect_issues(
        self, repository: str, days_back: int = 30, **kwargs
    ) -> dict[str, Any]:
        """Detect issues action."""
        metrics = await self.collect_pipeline_metrics(repository, days_back)
        anomalies = await self.detect_anomalies(metrics)
        failure_analysis = await self.analyze_failure_patterns(metrics)

        return {
            "anomalies": anomalies,
            "failure_analysis": failure_analysis,
            "issues_found": len(anomalies.get("anomalies", {}).get("duration_anomalies", [])) > 0
            or len(anomalies.get("anomalies", {}).get("failure_spikes", [])) > 0,
        }

    async def _action_optimize_workflows(
        self, repository: str, days_back: int = 30, **kwargs
    ) -> dict[str, Any]:
        """Optimize workflows action."""
        analysis = await self.analyze(repository, days_back)
        suggestions = analysis.get("optimization_suggestions", [])

        # Filter by priority if specified
        priority_filter = kwargs.get("priority")
        if priority_filter:
            suggestions = [s for s in suggestions if s.get("priority") == priority_filter]

        return {
            "repository": repository,
            "optimization_suggestions": suggestions,
            "total_suggestions": len(suggestions),
        }

    # Helper methods
    def _process_workflow_runs(self, runs: list[dict], workflows: list[dict]) -> dict[str, Any]:
        """Process raw workflow run data into metrics."""
        processed = {
            "success_rate": 0,
            "average_duration": 0,
            "workflow_stats": {},
            "status_distribution": Counter(),
            "conclusion_distribution": Counter(),
        }

        if not runs:
            return processed

        durations = []
        successes = 0

        workflow_stats = defaultdict(
            lambda: {"runs": 0, "successes": 0, "failures": 0, "durations": []}
        )

        for run in runs:
            # Status and conclusion tracking
            processed["status_distribution"][run.get("status", "unknown")] += 1
            processed["conclusion_distribution"][run.get("conclusion", "unknown")] += 1

            # Duration calculation
            if run.get("status") == "completed":
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated_at - created_at).total_seconds()
                durations.append(duration)

                # Workflow-specific stats
                workflow_name = run["name"]
                workflow_stats[workflow_name]["runs"] += 1
                workflow_stats[workflow_name]["durations"].append(duration)

                if run.get("conclusion") == "success":
                    successes += 1
                    workflow_stats[workflow_name]["successes"] += 1
                elif run.get("conclusion") == "failure":
                    workflow_stats[workflow_name]["failures"] += 1

        # Calculate averages
        processed["success_rate"] = successes / len(runs) if runs else 0
        processed["average_duration"] = statistics.mean(durations) if durations else 0

        # Process workflow stats
        for workflow, stats in workflow_stats.items():
            if stats["durations"]:
                processed["workflow_stats"][workflow] = {
                    "total_runs": stats["runs"],
                    "success_rate": stats["successes"] / stats["runs"] if stats["runs"] > 0 else 0,
                    "average_duration": statistics.mean(stats["durations"]),
                    "total_successes": stats["successes"],
                    "total_failures": stats["failures"],
                }

        return processed

    async def _get_workflows(self, repository: str) -> list[dict]:
        """Get workflow definitions for the repository."""
        if not self.session:
            return []

        try:
            url = f"{self.base_url}/repos/{repository}/actions/workflows"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("workflows", [])
        except Exception as e:
            logger.error(f"Error fetching workflows: {e}")

        return []

    async def _get_job_details(self, jobs_url: str) -> list[dict]:
        """Get detailed job information."""
        if not self.session or not jobs_url:
            return []

        try:
            async with self.session.get(jobs_url) as response:
                if response.status == 200:
                    data = await response.json()
                    jobs = data.get("jobs", [])
                    return [
                        {
                            "name": job.get("name"),
                            "conclusion": job.get("conclusion"),
                            "status": job.get("status"),
                            "steps": len(job.get("steps", [])),
                            "failed_steps": len(
                                [
                                    s
                                    for s in job.get("steps", [])
                                    if s.get("conclusion") == "failure"
                                ]
                            ),
                        }
                        for job in jobs
                    ]
        except Exception as e:
            logger.error(f"Error fetching job details: {e}")

        return []

    async def _get_deployment_runs(self, repository: str, days_back: int) -> list[dict]:
        """Get workflow runs related to deployments."""
        metrics = await self.collect_pipeline_metrics(repository, days_back)
        runs = metrics.get("workflow_runs", [])

        # Filter for deployment-related workflows
        deployment_keywords = ["deploy", "release", "production", "staging", "publish"]
        deployment_runs = []

        for run in runs:
            workflow_name = run.get("name", "").lower()
            if any(keyword in workflow_name for keyword in deployment_keywords):
                deployment_runs.append(run)

        return deployment_runs

    async def _calculate_mttr(self, repository: str, days_back: int) -> float:
        """Calculate Mean Time To Recovery."""
        # This is a simplified implementation
        # In practice, you'd track from when an issue is detected to when it's resolved
        deployment_runs = await self._get_deployment_runs(repository, days_back)

        recovery_times = []
        for i, run in enumerate(deployment_runs):
            if run.get("conclusion") == "failure" and i < len(deployment_runs) - 1:
                # Find next successful deployment
                for next_run in deployment_runs[i + 1 :]:
                    if next_run.get("conclusion") == "success":
                        failure_time = datetime.fromisoformat(
                            run["created_at"].replace("Z", "+00:00")
                        )
                        recovery_time = datetime.fromisoformat(
                            next_run["created_at"].replace("Z", "+00:00")
                        )
                        mttr_hours = (recovery_time - failure_time).total_seconds() / 3600
                        recovery_times.append(mttr_hours)
                        break

        return statistics.mean(recovery_times) if recovery_times else 0

    def _calculate_health_score(
        self, metrics: dict[str, Any], performance: dict[str, Any]
    ) -> float:
        """Calculate overall pipeline health score (0-1)."""
        processed = metrics.get("processed_metrics", {})
        success_rate = processed.get("success_rate", 0)

        # Base score from success rate
        health_score = success_rate

        # Adjust for performance
        avg_duration = performance.get("overall_statistics", {}).get("average_duration_seconds", 0)
        if avg_duration > 3600:  # More than 1 hour
            health_score *= 0.8
        elif avg_duration > 1800:  # More than 30 minutes
            health_score *= 0.9

        # Adjust for consistency (lower std dev = better)
        std_duration = performance.get("overall_statistics", {}).get("standard_deviation", 0)
        avg_duration = performance.get("overall_statistics", {}).get("average_duration_seconds", 1)
        if avg_duration > 0:
            cv = std_duration / avg_duration  # Coefficient of variation
            if cv > 0.5:  # High variability
                health_score *= 0.9

        return min(max(health_score, 0), 1)  # Clamp between 0 and 1

    def _grade_performance(self, avg_duration: float, std_duration: float) -> str:
        """Grade performance based on duration metrics."""
        if avg_duration < 300:  # Less than 5 minutes
            return "A"
        elif avg_duration < 900:  # Less than 15 minutes
            return "B"
        elif avg_duration < 1800:  # Less than 30 minutes
            return "C"
        elif avg_duration < 3600:  # Less than 1 hour
            return "D"
        else:
            return "F"

    def _calculate_dora_score(
        self,
        deployment_freq: float,
        lead_time: float,
        change_failure_rate: float,
        mttr: float,
    ) -> str:
        """Calculate DORA maturity score."""
        # Elite performers: Daily deployments, <1hr lead time, <15% failure rate, <1hr MTTR
        # High performers: Weekly-monthly deployments, <1 day lead time, <15% failure rate, <1 day MTTR
        # Medium/Low performers: Monthly-yearly deployments, longer lead times, higher failure rates

        score = 0

        # Deployment frequency scoring
        if deployment_freq >= 1:  # Daily
            score += 25
        elif deployment_freq >= 0.14:  # Weekly
            score += 20
        elif deployment_freq >= 0.03:  # Monthly
            score += 15
        else:
            score += 5

        # Lead time scoring
        if lead_time <= 1:  # 1 hour
            score += 25
        elif lead_time <= 24:  # 1 day
            score += 20
        elif lead_time <= 168:  # 1 week
            score += 15
        else:
            score += 5

        # Change failure rate scoring
        if change_failure_rate <= 0.15:
            score += 25
        elif change_failure_rate <= 0.3:
            score += 20
        elif change_failure_rate <= 0.45:
            score += 15
        else:
            score += 5

        # MTTR scoring
        if mttr <= 1:  # 1 hour
            score += 25
        elif mttr <= 24:  # 1 day
            score += 20
        elif mttr <= 168:  # 1 week
            score += 15
        else:
            score += 5

        if score >= 90:
            return "Elite"
        elif score >= 70:
            return "High"
        elif score >= 50:
            return "Medium"
        else:
            return "Low"

    def _generate_failure_recommendations(
        self,
        failure_by_workflow: dict,
        failure_by_branch: dict,
        overall_failure_rate: float,
    ) -> list[str]:
        """Generate recommendations based on failure patterns."""
        recommendations = []

        if overall_failure_rate > 0.3:
            recommendations.append(
                "Overall failure rate is high. Consider improving test reliability and adding retry mechanisms."
            )

        # Top failing workflows
        if failure_by_workflow:
            top_failing = max(failure_by_workflow.items(), key=lambda x: x[1])
            if top_failing[1] > 5:
                recommendations.append(
                    f"Workflow '{top_failing[0]}' has {top_failing[1]} failures. Focus optimization efforts here."
                )

        # Branch-specific issues
        if failure_by_branch:
            problematic_branches = [
                branch for branch, count in failure_by_branch.items() if count > 3
            ]
            if problematic_branches:
                recommendations.append(
                    f"Branches {problematic_branches} have multiple failures. Consider branch protection rules."
                )

        return recommendations

    def _generate_markdown_report(self, analysis: dict[str, Any]) -> str:
        """Generate a markdown-formatted report."""
        repo = analysis.get("repository", "Unknown")
        period = analysis.get("analysis_period", "Unknown")
        timestamp = analysis.get("timestamp", "Unknown")

        report = f"""# Pipeline Monitoring Report

**Repository:** {repo}
**Analysis Period:** {period}
**Generated:** {timestamp}

## Executive Summary

"""

        health_score = analysis.get("health_score", 0)
        health_status = (
            "🟢 Healthy"
            if health_score > 0.7
            else "🟡 Needs Attention" if health_score > 0.4 else "🔴 Critical"
        )

        report += f"**Pipeline Health:** {health_status} (Score: {health_score:.2f}/1.00)\n\n"

        # Performance metrics
        performance = analysis.get("build_performance", {})
        overall_stats = performance.get("overall_statistics", {})

        if overall_stats:
            avg_duration = overall_stats.get("average_duration_seconds", 0)
            total_runs = overall_stats.get("total_runs_analyzed", 0)

            report += f"""## Performance Metrics

- **Average Build Time:** {avg_duration/60:.1f} minutes
- **Total Runs Analyzed:** {total_runs}
- **Performance Grade:** {performance.get("performance_grade", "N/A")}

"""

        # DORA metrics
        dora = analysis.get("dora_metrics", {})
        if dora:
            report += f"""## DORA Metrics

- **Deployment Frequency:** {dora.get("deployment_frequency_per_day", 0):.2f} per day
- **Lead Time:** {dora.get("lead_time_hours", 0):.1f} hours
- **Change Failure Rate:** {dora.get("change_failure_rate", 0):.1%}
- **MTTR:** {dora.get("mean_time_to_recovery_hours", 0):.1f} hours
- **DORA Score:** {dora.get("dora_score", "Unknown")}

"""

        # Optimization suggestions
        suggestions = analysis.get("optimization_suggestions", [])
        if suggestions:
            report += "## Optimization Recommendations\n\n"
            for i, suggestion in enumerate(suggestions[:5], 1):  # Top 5 suggestions
                priority_emoji = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }.get(suggestion.get("priority", "low"), "🔵")
                report += f"### {i}. {suggestion.get('title', 'Optimization')} {priority_emoji}\n\n"
                report += f"{suggestion.get('description', '')}\n\n"

                recommendations = suggestion.get("recommendations", [])
                if recommendations:
                    for rec in recommendations:
                        report += f"- {rec}\n"
                    report += "\n"

        # Anomalies
        anomalies = analysis.get("anomalies", {})
        if anomalies and anomalies.get("anomalies"):
            report += "## Detected Anomalies\n\n"

            duration_anomalies = anomalies.get("anomalies", {}).get("duration_anomalies", [])
            if duration_anomalies:
                report += f"- **Duration Anomalies:** {len(duration_anomalies)} detected\n"

            failure_spikes = anomalies.get("anomalies", {}).get("failure_spikes", [])
            if failure_spikes:
                report += f"- **Failure Spikes:** {len(failure_spikes)} detected\n"

            report += "\n"

        report += "---\n*Report generated by PipelineMonitoringAgent*"

        return report

    async def _analyze_resource_usage(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Analyze resource usage patterns (simplified implementation)."""
        # This would typically integrate with monitoring systems
        # For now, we'll analyze based on duration patterns as a proxy

        runs = metrics.get("workflow_runs", [])
        workflow_resource_patterns = {}

        for run in runs:
            workflow_name = run["name"]
            if workflow_name not in workflow_resource_patterns:
                workflow_resource_patterns[workflow_name] = {
                    "run_count": 0,
                    "total_duration": 0,
                    "avg_duration": 0,
                    "resource_efficiency": "unknown",
                }

            if run.get("status") == "completed":
                created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
                updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
                duration = (updated_at - created_at).total_seconds()

                workflow_resource_patterns[workflow_name]["run_count"] += 1
                workflow_resource_patterns[workflow_name]["total_duration"] += duration

        # Calculate averages and efficiency ratings
        for workflow, data in workflow_resource_patterns.items():
            if data["run_count"] > 0:
                data["avg_duration"] = data["total_duration"] / data["run_count"]

                # Simple efficiency rating based on duration
                if data["avg_duration"] < 600:  # 10 minutes
                    data["resource_efficiency"] = "excellent"
                elif data["avg_duration"] < 1800:  # 30 minutes
                    data["resource_efficiency"] = "good"
                elif data["avg_duration"] < 3600:  # 1 hour
                    data["resource_efficiency"] = "fair"
                else:
                    data["resource_efficiency"] = "poor"

        return {
            "workflow_patterns": workflow_resource_patterns,
            "analysis_note": "Resource usage analysis is simplified. For detailed resource metrics, integrate with monitoring systems.",
        }
