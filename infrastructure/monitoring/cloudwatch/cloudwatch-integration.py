"""
CloudWatch and X-Ray Integration for ToolBoxAI Solutions
Comprehensive AWS observability with compliance tracking
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Patch all supported libraries for X-Ray tracing
patch_all()


class MetricNamespace(Enum):
    """CloudWatch metric namespaces"""
    APPLICATION = "ToolBoxAI/Application"
    COMPLIANCE = "ToolBoxAI/Compliance"
    SECURITY = "ToolBoxAI/Security"
    EDUCATION = "ToolBoxAI/Education"
    INFRASTRUCTURE = "ToolBoxAI/Infrastructure"
    AI_ML = "ToolBoxAI/AI-ML"


@dataclass
class ComplianceMetric:
    """Compliance metric structure"""
    regulation: str  # COPPA, FERPA, GDPR
    category: str
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


class CloudWatchIntegration:
    """CloudWatch metrics and logs integration"""

    def __init__(self, region: str = "us-east-1"):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        self.xray = boto3.client('xray', region_name=region)

        # Environment configuration
        self.environment = os.getenv('ENVIRONMENT', 'dev')
        self.project_name = 'toolboxai'

        # Create log groups if they don't exist
        self._ensure_log_groups()

    def _ensure_log_groups(self):
        """Ensure CloudWatch log groups exist"""
        log_groups = [
            f"/aws/lambda/{self.project_name}",
            f"/aws/ecs/{self.project_name}",
            f"/aws/eks/{self.project_name}",
            f"/application/{self.project_name}/backend",
            f"/application/{self.project_name}/dashboard",
            f"/compliance/{self.project_name}",
            f"/security/{self.project_name}",
            f"/audit/{self.project_name}"
        ]

        for log_group in log_groups:
            try:
                self.logs.create_log_group(
                    logGroupName=log_group,
                    kmsKeyId=os.getenv('KMS_KEY_ARN')
                )

                # Set retention policy
                self.logs.put_retention_policy(
                    logGroupName=log_group,
                    retentionInDays=90 if 'audit' in log_group else 30
                )
            except self.logs.exceptions.ResourceAlreadyExistsException:
                pass

    def put_metric(
        self,
        namespace: MetricNamespace,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Send metric to CloudWatch"""
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow()
            }

            # Add default dimensions
            default_dimensions = [
                {'Name': 'Environment', 'Value': self.environment},
                {'Name': 'Project', 'Value': self.project_name}
            ]

            if dimensions:
                for key, val in dimensions.items():
                    default_dimensions.append({'Name': key, 'Value': str(val)})

            metric_data['Dimensions'] = default_dimensions

            self.cloudwatch.put_metric_data(
                Namespace=namespace.value,
                MetricData=[metric_data]
            )

            logger.info(f"Metric sent: {namespace.value}/{metric_name} = {value}")

        except Exception as e:
            logger.error(f"Failed to send metric: {e}")

    def put_compliance_metric(self, metric: ComplianceMetric):
        """Send compliance-specific metric"""
        self.put_metric(
            namespace=MetricNamespace.COMPLIANCE,
            metric_name=f"{metric.regulation}_{metric.category}",
            value=1 if metric.status == "compliant" else 0,
            unit="None",
            dimensions={
                "Regulation": metric.regulation,
                "Category": metric.category,
                "Status": metric.status
            }
        )

        # Log compliance event
        self.log_compliance_event(metric)

    def log_compliance_event(self, metric: ComplianceMetric):
        """Log compliance event to CloudWatch Logs"""
        log_group = f"/compliance/{self.project_name}"
        log_stream = f"{metric.regulation}-{datetime.now().strftime('%Y-%m-%d')}"

        try:
            # Create log stream if needed
            self.logs.create_log_stream(
                logGroupName=log_group,
                logStreamName=log_stream
            )
        except self.logs.exceptions.ResourceAlreadyExistsException:
            pass

        # Send log event
        log_event = {
            'timestamp': int(metric.timestamp.timestamp() * 1000),
            'message': json.dumps({
                'regulation': metric.regulation,
                'category': metric.category,
                'status': metric.status,
                'details': metric.details,
                'environment': self.environment
            })
        }

        self.logs.put_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            logEvents=[log_event]
        )

    def create_dashboard(self):
        """Create CloudWatch dashboard"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["ToolBoxAI/Application", "RequestCount", {"stat": "Sum"}],
                            [".", "ErrorCount", {"stat": "Sum"}],
                            [".", "Latency", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Application Metrics"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["ToolBoxAI/Compliance", "COPPA_data_access", {"stat": "Sum"}],
                            [".", "FERPA_records_protected", {"stat": "Sum"}],
                            [".", "GDPR_consent_granted", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Compliance Status"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["ToolBoxAI/AI-ML", "ModelInferenceLatency", {"stat": "Average"}],
                            [".", "TokenUsage", {"stat": "Sum"}],
                            [".", "ContentGenerationRequests", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "AI/ML Operations"
                    }
                },
                {
                    "type": "log",
                    "properties": {
                        "query": "SOURCE '/compliance/toolboxai' | fields @timestamp, regulation, status | stats count() by status",
                        "region": "us-east-1",
                        "stacked": False,
                        "title": "Compliance Events",
                        "view": "pie"
                    }
                }
            ]
        }

        self.cloudwatch.put_dashboard(
            DashboardName=f"{self.project_name}-{self.environment}",
            DashboardBody=json.dumps(dashboard_body)
        )

    def create_alarms(self):
        """Create CloudWatch alarms"""
        alarms = [
            {
                "AlarmName": f"{self.project_name}-{self.environment}-HighErrorRate",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 2,
                "MetricName": "ErrorCount",
                "Namespace": MetricNamespace.APPLICATION.value,
                "Period": 300,
                "Statistic": "Sum",
                "Threshold": 100,
                "ActionsEnabled": True,
                "AlarmDescription": "Alert when error rate is high"
            },
            {
                "AlarmName": f"{self.project_name}-{self.environment}-ComplianceViolation",
                "ComparisonOperator": "LessThanThreshold",
                "EvaluationPeriods": 1,
                "MetricName": "COPPA_data_access",
                "Namespace": MetricNamespace.COMPLIANCE.value,
                "Period": 300,
                "Statistic": "Average",
                "Threshold": 1,
                "ActionsEnabled": True,
                "AlarmDescription": "Alert on COPPA compliance violation"
            },
            {
                "AlarmName": f"{self.project_name}-{self.environment}-HighLatency",
                "ComparisonOperator": "GreaterThanThreshold",
                "EvaluationPeriods": 3,
                "MetricName": "Latency",
                "Namespace": MetricNamespace.APPLICATION.value,
                "Period": 300,
                "Statistic": "Average",
                "Threshold": 1000,
                "ActionsEnabled": True,
                "AlarmDescription": "Alert when latency exceeds 1 second"
            }
        ]

        for alarm in alarms:
            if os.getenv('SNS_TOPIC_ARN'):
                alarm['AlarmActions'] = [os.getenv('SNS_TOPIC_ARN')]

            self.cloudwatch.put_metric_alarm(**alarm)


class XRayIntegration:
    """AWS X-Ray distributed tracing"""

    def __init__(self):
        self.xray = boto3.client('xray')

        # Configure X-Ray recorder
        xray_recorder.configure(
            service=os.getenv('SERVICE_NAME', 'toolboxai-backend'),
            context_missing='LOG_ERROR',
            daemon_address='127.0.0.1:2000'
        )

    @staticmethod
    def trace_function(subsegment_name: str = None):
        """Decorator for tracing functions"""
        def decorator(func):
            @xray_recorder.capture(subsegment_name or func.__name__)
            def wrapper(*args, **kwargs):
                # Add metadata
                subsegment = xray_recorder.current_subsegment()
                if subsegment:
                    subsegment.put_annotation('environment', os.getenv('ENVIRONMENT', 'dev'))
                    subsegment.put_annotation('function', func.__name__)

                return func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def add_user_context(user_id: str, user_role: str):
        """Add user context to current segment"""
        segment = xray_recorder.current_segment()
        if segment:
            segment.set_user(user_id)
            segment.put_annotation('user_role', user_role)
            segment.put_metadata('user', {
                'id': user_id,
                'role': user_role,
                'timestamp': datetime.utcnow().isoformat()
            })

    @staticmethod
    def add_compliance_context(regulation: str, compliant: bool):
        """Add compliance context to trace"""
        segment = xray_recorder.current_segment()
        if segment:
            segment.put_annotation(f'compliance_{regulation}', compliant)
            segment.put_metadata('compliance', {
                'regulation': regulation,
                'compliant': compliant,
                'timestamp': datetime.utcnow().isoformat()
            })

    def create_service_map_filter(self):
        """Create service map filter for visualization"""
        try:
            response = self.xray.create_group(
                GroupName=f"ToolBoxAI-{os.getenv('ENVIRONMENT', 'dev')}",
                FilterExpression=f'service("toolboxai-*") OR annotation.environment = "{os.getenv("ENVIRONMENT", "dev")}"'
            )
            return response['Group']
        except self.xray.exceptions.InvalidRequestException:
            # Group already exists
            pass


class MetricsCollector:
    """Application metrics collector"""

    def __init__(self):
        self.cloudwatch = CloudWatchIntegration()
        self.xray = XRayIntegration()

    @XRayIntegration.trace_function("collect_application_metrics")
    def collect_application_metrics(self, metrics: Dict[str, Any]):
        """Collect and send application metrics"""
        # Request metrics
        if 'request_count' in metrics:
            self.cloudwatch.put_metric(
                namespace=MetricNamespace.APPLICATION,
                metric_name="RequestCount",
                value=metrics['request_count'],
                unit="Count"
            )

        # Latency metrics
        if 'latency_ms' in metrics:
            self.cloudwatch.put_metric(
                namespace=MetricNamespace.APPLICATION,
                metric_name="Latency",
                value=metrics['latency_ms'],
                unit="Milliseconds"
            )

        # Error metrics
        if 'error_count' in metrics:
            self.cloudwatch.put_metric(
                namespace=MetricNamespace.APPLICATION,
                metric_name="ErrorCount",
                value=metrics['error_count'],
                unit="Count"
            )

    @XRayIntegration.trace_function("collect_ai_metrics")
    def collect_ai_metrics(self, metrics: Dict[str, Any]):
        """Collect AI/ML metrics"""
        # Model inference metrics
        if 'inference_time' in metrics:
            self.cloudwatch.put_metric(
                namespace=MetricNamespace.AI_ML,
                metric_name="ModelInferenceLatency",
                value=metrics['inference_time'],
                unit="Milliseconds",
                dimensions={'model': metrics.get('model_name', 'unknown')}
            )

        # Token usage
        if 'token_count' in metrics:
            self.cloudwatch.put_metric(
                namespace=MetricNamespace.AI_ML,
                metric_name="TokenUsage",
                value=metrics['token_count'],
                unit="Count",
                dimensions={'model': metrics.get('model_name', 'unknown')}
            )

    @XRayIntegration.trace_function("track_compliance")
    def track_compliance(self, regulation: str, compliant: bool, details: Dict = None):
        """Track compliance metrics"""
        metric = ComplianceMetric(
            regulation=regulation,
            category="verification",
            status="compliant" if compliant else "violation",
            timestamp=datetime.utcnow(),
            details=details
        )

        self.cloudwatch.put_compliance_metric(metric)
        XRayIntegration.add_compliance_context(regulation, compliant)


# Flask application integration
def setup_flask_monitoring(app):
    """Setup monitoring for Flask application"""
    from flask import g, request

    # Add X-Ray middleware
    XRayMiddleware(app, xray_recorder)

    # Initialize metrics collector
    collector = MetricsCollector()

    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()

        # Start X-Ray segment
        if hasattr(request, 'headers'):
            trace_header = request.headers.get('X-Amzn-Trace-Id')
            if trace_header:
                xray_recorder.begin_segment('request', traceid=trace_header)

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            # Calculate request duration
            duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000

            # Send metrics
            collector.collect_application_metrics({
                'request_count': 1,
                'latency_ms': duration,
                'error_count': 1 if response.status_code >= 500 else 0
            })

            # End X-Ray segment
            segment = xray_recorder.current_segment()
            if segment:
                segment.put_annotation('status_code', response.status_code)
                xray_recorder.end_segment()

        return response

    return app


if __name__ == "__main__":
    # Initialize integrations
    cloudwatch = CloudWatchIntegration()
    xray = XRayIntegration()
    collector = MetricsCollector()

    # Create dashboard and alarms
    cloudwatch.create_dashboard()
    cloudwatch.create_alarms()

    # Test compliance tracking
    collector.track_compliance("COPPA", True, {"user_age": 14})
    collector.track_compliance("FERPA", True, {"records_encrypted": True})
    collector.track_compliance("GDPR", True, {"consent_obtained": True})

    print("✅ CloudWatch and X-Ray integration configured")