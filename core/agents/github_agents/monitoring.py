"""
Monitoring module for the GitHub Agent System.
"""

from datetime import datetime
from typing import Any, Dict


class GitHubAgentMonitoring:
    """Monitoring and alerting for GitHub agents."""

    def __init__(self):
        """Initialize monitoring."""
        self.metrics = {}
        self.alerts = []

    async def track_agent_performance(self, agent_name: str, operation: str, duration: float):
        """Track agent performance metrics."""
        if agent_name not in self.metrics:
            self.metrics[agent_name] = []

        self.metrics[agent_name].append({
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })

    async def send_alert(self, severity: str, message: str):
        """Send an alert."""
        self.alerts.append({
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        return {
            "agents": list(self.metrics.keys()),
            "total_operations": sum(len(ops) for ops in self.metrics.values()),
            "alerts": self.alerts
        }