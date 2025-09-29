"""
Lambda Function Monitoring with CloudWatch and X-Ray
Enhanced observability for serverless functions
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize AWS Lambda Powertools
logger = Logger(service="toolboxai-lambda")
metrics = Metrics(namespace="ToolBoxAI/Lambda")
tracer = Tracer(service="toolboxai-lambda")

# CloudWatch client
cloudwatch = boto3.client('cloudwatch')


class LambdaMonitor:
    """Enhanced monitoring for Lambda functions"""

    def __init__(self, function_name: str):
        self.function_name = function_name
        self.environment = os.getenv('ENVIRONMENT', 'dev')

    def log_metric(
        self,
        metric_name: str,
        value: float,
        unit: MetricUnit = MetricUnit.None,
        **dimensions
    ):
        """Log custom metric"""
        metrics.add_metric(
            name=metric_name,
            unit=unit,
            value=value
        )

        # Add dimensions
        for key, val in dimensions.items():
            metrics.add_dimension(key, str(val))

    def log_compliance_check(
        self,
        regulation: str,
        check_type: str,
        passed: bool,
        details: Optional[Dict] = None
    ):
        """Log compliance check result"""
        logger.info(
            "Compliance check performed",
            extra={
                "regulation": regulation,
                "check_type": check_type,
                "passed": passed,
                "details": details or {}
            }
        )

        # Send metric
        self.log_metric(
            metric_name=f"ComplianceCheck_{regulation}",
            value=1 if passed else 0,
            unit=MetricUnit.None,
            regulation=regulation,
            check_type=check_type
        )

    @tracer.capture_method
    def track_cold_start(self, context: LambdaContext):
        """Track Lambda cold starts"""
        is_cold_start = not hasattr(self, '_warm')
        self._warm = True

        if is_cold_start:
            logger.info("Cold start detected")
            self.log_metric(
                metric_name="ColdStart",
                value=1,
                unit=MetricUnit.Count,
                function_name=self.function_name
            )

            # Log initialization duration
            remaining_time = context.get_remaining_time_in_millis()
            init_duration = context.memory_limit_in_mb - remaining_time
            self.log_metric(
                metric_name="InitializationDuration",
                value=init_duration,
                unit=MetricUnit.Milliseconds
            )

    def track_execution(self, context: LambdaContext):
        """Track Lambda execution metrics"""
        # Memory usage
        memory_used = int(context.memory_limit_in_mb)
        self.log_metric(
            metric_name="MemoryUsed",
            value=memory_used,
            unit=MetricUnit.Megabytes,
            function_name=self.function_name
        )

        # Remaining time
        remaining_time = context.get_remaining_time_in_millis()
        execution_time = 30000 - remaining_time  # Assuming 30s timeout
        self.log_metric(
            metric_name="ExecutionDuration",
            value=execution_time,
            unit=MetricUnit.Milliseconds,
            function_name=self.function_name
        )

    def create_custom_dashboard(self):
        """Create Lambda-specific CloudWatch dashboard"""
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Invocations", {"stat": "Sum"}],
                            [".", "Errors", {"stat": "Sum"}],
                            [".", "Duration", {"stat": "Average"}],
                            [".", "Throttles", {"stat": "Sum"}]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": os.getenv('AWS_REGION', 'us-east-1'),
                        "title": f"{self.function_name} Metrics"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["ToolBoxAI/Lambda", "ColdStart", {"stat": "Sum"}],
                            [".", "MemoryUsed", {"stat": "Average"}],
                            [".", "ExecutionDuration", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "region": os.getenv('AWS_REGION', 'us-east-1'),
                        "title": "Custom Lambda Metrics"
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["ToolBoxAI/Lambda", "ComplianceCheck_COPPA", {"stat": "Average"}],
                            [".", "ComplianceCheck_FERPA", {"stat": "Average"}],
                            [".", "ComplianceCheck_GDPR", {"stat": "Average"}]
                        ],
                        "period": 300,
                        "region": os.getenv('AWS_REGION', 'us-east-1'),
                        "title": "Compliance Checks"
                    }
                }
            ]
        }

        cloudwatch.put_dashboard(
            DashboardName=f"Lambda-{self.function_name}",
            DashboardBody=json.dumps(dashboard_body)
        )


def monitored_handler(function_name: str):
    """Decorator for Lambda handler monitoring"""
    def decorator(handler):
        monitor = LambdaMonitor(function_name)

        @wraps(handler)
        @logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
        @tracer.capture_lambda_handler
        @metrics.log_metrics(capture_cold_start_metric=True)
        def wrapper(event: Dict[str, Any], context: LambdaContext):
            # Track cold start
            monitor.track_cold_start(context)

            # Log event
            logger.info("Lambda invoked", extra={"event": event})

            try:
                # Execute handler
                result = handler(event, context)

                # Track execution metrics
                monitor.track_execution(context)

                # Log success
                logger.info("Lambda execution successful")
                monitor.log_metric(
                    metric_name="SuccessfulInvocation",
                    value=1,
                    unit=MetricUnit.Count
                )

                return result

            except Exception as e:
                # Log error
                logger.exception(f"Lambda execution failed: {e}")
                monitor.log_metric(
                    metric_name="FailedInvocation",
                    value=1,
                    unit=MetricUnit.Count,
                    error_type=type(e).__name__
                )

                # Add error to trace
                tracer.put_annotation(key="error", value=str(e))
                tracer.put_metadata(key="error_details", value={
                    "type": type(e).__name__,
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

                raise

        return wrapper
    return decorator


# Example Lambda handlers with monitoring

@monitored_handler("content-generator")
def content_generator_handler(event: Dict[str, Any], context: LambdaContext):
    """Content generation Lambda function"""
    monitor = LambdaMonitor("content-generator")

    # Validate user age for COPPA
    user_age = event.get('user_age', 0)
    if user_age < 13:
        monitor.log_compliance_check(
            regulation="COPPA",
            check_type="age_verification",
            passed=False,
            details={"user_age": user_age}
        )
        raise ValueError("User does not meet age requirements")

    monitor.log_compliance_check(
        regulation="COPPA",
        check_type="age_verification",
        passed=True,
        details={"user_age": user_age}
    )

    # Process content generation
    content_type = event.get('content_type', 'lesson')

    # Simulate content generation
    import time
    generation_start = time.time()
    time.sleep(0.5)  # Simulate processing
    generation_time = (time.time() - generation_start) * 1000

    # Log generation metrics
    monitor.log_metric(
        metric_name="ContentGenerationTime",
        value=generation_time,
        unit=MetricUnit.Milliseconds,
        content_type=content_type
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'content_id': 'generated_123',
            'content_type': content_type,
            'generation_time_ms': generation_time
        })
    }


@monitored_handler("compliance-validator")
def compliance_validator_handler(event: Dict[str, Any], context: LambdaContext):
    """Compliance validation Lambda function"""
    monitor = LambdaMonitor("compliance-validator")

    validations = []

    # COPPA validation
    coppa_compliant = event.get('user_age', 0) >= 13
    monitor.log_compliance_check(
        regulation="COPPA",
        check_type="full_validation",
        passed=coppa_compliant
    )
    validations.append({"regulation": "COPPA", "compliant": coppa_compliant})

    # FERPA validation
    ferpa_compliant = event.get('records_encrypted', False)
    monitor.log_compliance_check(
        regulation="FERPA",
        check_type="encryption_check",
        passed=ferpa_compliant
    )
    validations.append({"regulation": "FERPA", "compliant": ferpa_compliant})

    # GDPR validation
    gdpr_compliant = event.get('consent_obtained', False)
    monitor.log_compliance_check(
        regulation="GDPR",
        check_type="consent_verification",
        passed=gdpr_compliant
    )
    validations.append({"regulation": "GDPR", "compliant": gdpr_compliant})

    all_compliant = all(v['compliant'] for v in validations)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'compliant': all_compliant,
            'validations': validations,
            'timestamp': datetime.utcnow().isoformat()
        })
    }


@monitored_handler("data-processor")
def data_processor_handler(event: Dict[str, Any], context: LambdaContext):
    """Data processing Lambda with enhanced monitoring"""
    monitor = LambdaMonitor("data-processor")

    # Parse S3 event
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size']

        logger.info(f"Processing S3 object", extra={
            "bucket": bucket,
            "key": key,
            "size": size
        })

        # Track data processing
        monitor.log_metric(
            metric_name="DataProcessed",
            value=size,
            unit=MetricUnit.Bytes,
            bucket=bucket
        )

        # Check data classification
        if 'educational_records' in key:
            # FERPA protected data
            monitor.log_compliance_check(
                regulation="FERPA",
                check_type="data_access",
                passed=True,
                details={"data_type": "educational_records"}
            )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': len(event.get('Records', [])),
            'timestamp': datetime.utcnow().isoformat()
        })
    }


# CloudFormation template for Lambda monitoring
def generate_cloudformation_template():
    """Generate CloudFormation template for Lambda monitoring setup"""
    template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Lambda monitoring setup for ToolBoxAI",
        "Resources": {
            "LambdaLogGroup": {
                "Type": "AWS::Logs::LogGroup",
                "Properties": {
                    "LogGroupName": "/aws/lambda/toolboxai",
                    "RetentionInDays": 30,
                    "KmsKeyId": {"Ref": "KMSKey"}
                }
            },
            "LambdaMetricFilter": {
                "Type": "AWS::Logs::MetricFilter",
                "Properties": {
                    "FilterPattern": "[time, request_id, level = ERROR, ...]",
                    "LogGroupName": {"Ref": "LambdaLogGroup"},
                    "MetricTransformations": [{
                        "MetricName": "LambdaErrors",
                        "MetricNamespace": "ToolBoxAI/Lambda",
                        "MetricValue": "1"
                    }]
                }
            },
            "LambdaErrorAlarm": {
                "Type": "AWS::CloudWatch::Alarm",
                "Properties": {
                    "AlarmName": "LambdaHighErrorRate",
                    "ComparisonOperator": "GreaterThanThreshold",
                    "EvaluationPeriods": 2,
                    "MetricName": "Errors",
                    "Namespace": "AWS/Lambda",
                    "Period": 300,
                    "Statistic": "Sum",
                    "Threshold": 10,
                    "AlarmActions": [{"Ref": "SNSTopic"}]
                }
            }
        }
    }

    return json.dumps(template, indent=2)


if __name__ == "__main__":
    # Test monitoring setup
    monitor = LambdaMonitor("test-function")
    monitor.create_custom_dashboard()

    print("✅ Lambda monitoring configured")
    print("\nCloudFormation template:")
    print(generate_cloudformation_template())