#!/usr/bin/env python3
"""
ToolBoxAI Solutions - Slack Notifier Lambda Function
Sends CloudWatch alarm notifications to Slack
"""

import json
import os
from datetime import datetime

import urllib3


def lambda_handler(event, context):
    """
    Lambda handler for Slack notifications from SNS
    """

    # Get environment variables
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    environment = os.environ.get("ENVIRONMENT", "unknown")

    if not slack_webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL environment variable not set")
        return {
            "statusCode": 400,
            "body": json.dumps("Slack webhook URL not configured"),
        }

    try:
        # Parse SNS message
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])

        # Extract alarm details
        alarm_name = sns_message.get("AlarmName", "Unknown Alarm")
        alarm_description = sns_message.get("AlarmDescription", "No description")
        new_state = sns_message.get("NewStateValue", "UNKNOWN")
        old_state = sns_message.get("OldStateValue", "UNKNOWN")
        reason = sns_message.get("NewStateReason", "No reason provided")
        timestamp = sns_message.get("StateChangeTime", datetime.utcnow().isoformat())
        region = sns_message.get("Region", "unknown")
        account_id = sns_message.get("AWSAccountId", "unknown")

        # Determine color and emoji based on alarm state
        if new_state == "ALARM":
            color = "#FF0000"  # Red
            emoji = "🚨"
            action = "TRIGGERED"
        elif new_state == "OK":
            color = "#00FF00"  # Green
            emoji = "✅"
            action = "RESOLVED"
        else:
            color = "#FFA500"  # Orange
            emoji = "⚠️"
            action = "CHANGED"

        # Create Slack message
        slack_message = {
            "attachments": [
                {
                    "fallback": f"{emoji} {alarm_name} {action} in {environment}",
                    "color": color,
                    "pretext": f"{emoji} *CloudWatch Alarm {action}*",
                    "title": f"{alarm_name}",
                    "title_link": f"https://console.aws.amazon.com/cloudwatch/home?region={region}#alarmsV2:alarm/{alarm_name}",
                    "text": alarm_description,
                    "fields": [
                        {
                            "title": "Environment",
                            "value": environment.upper(),
                            "short": True,
                        },
                        {
                            "title": "State Change",
                            "value": f"{old_state} → {new_state}",
                            "short": True,
                        },
                        {"title": "Region", "value": region, "short": True},
                        {"title": "Account", "value": account_id, "short": True},
                        {"title": "Reason", "value": reason, "short": False},
                        {"title": "Time", "value": timestamp, "short": False},
                    ],
                    "footer": "ToolBoxAI CloudWatch",
                    "footer_icon": "https://aws.amazon.com/favicon.ico",
                    "ts": int(datetime.now().timestamp()),
                }
            ]
        }

        # Add environment-specific channel mentions
        if environment == "production" and new_state == "ALARM":
            slack_message["text"] = "<!channel> Production alert requires immediate attention!"
        elif environment == "staging" and new_state == "ALARM":
            slack_message["text"] = "<!here> Staging environment alert"

        # Send to Slack
        http = urllib3.PoolManager()
        response = http.request(
            "POST",
            slack_webhook_url,
            body=json.dumps(slack_message),
            headers={"Content-Type": "application/json"},
        )

        if response.status == 200:
            print(f"Successfully sent Slack notification for alarm: {alarm_name}")
            return {
                "statusCode": 200,
                "body": json.dumps("Notification sent successfully"),
            }
        else:
            print(f"Failed to send Slack notification. Status: {response.status}")
            return {
                "statusCode": response.status,
                "body": json.dumps(f"Failed to send notification: {response.status}"),
            }

    except Exception as e:
        print(f"Error processing notification: {str(e)}")

        # Send error notification to Slack if possible
        try:
            error_message = {
                "text": f"🔥 *Error in Slack Notifier Lambda*",
                "attachments": [
                    {
                        "color": "#FF0000",
                        "fields": [
                            {
                                "title": "Environment",
                                "value": environment,
                                "short": True,
                            },
                            {"title": "Error", "value": str(e), "short": False},
                            {
                                "title": "Event",
                                "value": (
                                    json.dumps(event, indent=2)[:1000] + "..."
                                    if len(json.dumps(event)) > 1000
                                    else json.dumps(event, indent=2)
                                ),
                                "short": False,
                            },
                        ],
                    }
                ],
            }

            http = urllib3.PoolManager()
            http.request(
                "POST",
                slack_webhook_url,
                body=json.dumps(error_message),
                headers={"Content-Type": "application/json"},
            )
        except Exception as slack_error:
            print(f"Failed to send error notification to Slack: {str(slack_error)}")

        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing notification: {str(e)}"),
        }


def format_metric_value(value, unit):
    """
    Format metric values for better readability
    """
    if unit == "Percent":
        return f"{value:.1f}%"
    elif unit == "Seconds":
        if value >= 60:
            minutes = int(value // 60)
            seconds = value % 60
            return f"{minutes}m {seconds:.0f}s"
        else:
            return f"{value:.2f}s"
    elif unit == "Bytes":
        for unit_name in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024.0:
                return f"{value:.1f} {unit_name}"
            value /= 1024.0
        return f"{value:.1f} PB"
    elif unit == "Count":
        return f"{int(value)}"
    else:
        return f"{value} {unit}"


def get_alarm_priority(alarm_name, new_state):
    """
    Determine alarm priority based on name patterns and state
    """
    high_priority_patterns = [
        "production",
        "critical",
        "database",
        "security",
        "health",
    ]

    if new_state == "ALARM":
        for pattern in high_priority_patterns:
            if pattern in alarm_name.lower():
                return "HIGH"
        return "MEDIUM"
    else:
        return "LOW"


def should_notify(alarm_name, new_state, old_state, environment):
    """
    Determine if notification should be sent based on various criteria
    """
    # Always notify for production alarms
    if environment == "production":
        return True

    # Notify for state changes from OK to ALARM
    if old_state == "OK" and new_state == "ALARM":
        return True

    # Notify for resolutions from ALARM to OK
    if old_state == "ALARM" and new_state == "OK":
        return True

    # Skip INSUFFICIENT_DATA notifications for non-production
    if new_state == "INSUFFICIENT_DATA" and environment != "production":
        return False

    return True
