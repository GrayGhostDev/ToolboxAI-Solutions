"""Documentation validation for Pusher migration"""
import re
from pathlib import Path
import yaml
import json

class DocumentationValidator:
    """Validate documentation correctly reflects Pusher migration"""

    def __init__(self):
        self.doc_path = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/docs")
        self.issues = []

    def validate_no_active_websocket_refs(self):
        """Ensure WebSocket references are marked as deprecated"""
        patterns = [
            r'ws://',
            r'wss://',
            r'new WebSocket',
            r'/ws/',
            r'socket\.io'
        ]

        for doc_file in self.doc_path.rglob("*.md"):
            with open(doc_file, 'r') as f:
                content = f.read()

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    context = content[match.start()-50:match.end()+50]

                    # Check if marked as deprecated
                    if not any(word in context.lower() for word in ['deprecated', 'legacy', 'old']):
                        self.issues.append({
                            'file': str(doc_file),
                            'line': line_num,
                            'pattern': pattern,
                            'issue': 'WebSocket reference not marked as deprecated'
                        })

        return self.issues

    def validate_pusher_documentation(self):
        """Ensure Pusher channels are properly documented"""
        required_channels = [
            'roblox-sync',
            'content-generation',
            'agent-status',
            'plugin-',
            'analytics-realtime'
        ]

        documented_channels = set()

        for doc_file in self.doc_path.rglob("*.md"):
            with open(doc_file, 'r') as f:
                content = f.read()
                for channel in required_channels:
                    if channel in content:
                        documented_channels.add(channel)

        missing = set(required_channels) - documented_channels
        if missing:
            self.issues.append({
                'issue': 'Missing Pusher channel documentation',
                'channels': list(missing)
            })

        return len(missing) == 0

    def validate_api_documentation_consistency(self):
        """Check that API docs match actual endpoints"""
        api_spec_file = self.doc_path / "03-api" / "openapi-spec.json"

        if not api_spec_file.exists():
            self.issues.append({
                'issue': 'OpenAPI specification file not found',
                'file': str(api_spec_file)
            })
            return False

        try:
            with open(api_spec_file, 'r') as f:
                api_spec = json.load(f)

            # Check for Pusher endpoints
            paths = api_spec.get('paths', {})
            pusher_endpoints = [
                '/pusher/auth',
                '/api/v1/realtime/trigger',
                '/pusher/webhook'
            ]

            for endpoint in pusher_endpoints:
                if endpoint not in paths:
                    self.issues.append({
                        'issue': f'Missing Pusher endpoint in API spec: {endpoint}',
                        'file': str(api_spec_file)
                    })

        except json.JSONDecodeError as e:
            self.issues.append({
                'issue': f'Invalid JSON in API spec: {e}',
                'file': str(api_spec_file)
            })

        return True

    def validate_environment_config_docs(self):
        """Validate environment configuration documentation"""
        env_example_file = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/.env.example")

        if not env_example_file.exists():
            self.issues.append({
                'issue': 'Environment example file not found',
                'file': str(env_example_file)
            })
            return False

        with open(env_example_file, 'r') as f:
            env_content = f.read()

        # Check for required Pusher variables
        required_vars = [
            'PUSHER_APP_ID',
            'PUSHER_KEY',
            'PUSHER_SECRET',
            'PUSHER_CLUSTER'
        ]

        for var in required_vars:
            if var not in env_content:
                self.issues.append({
                    'issue': f'Missing Pusher environment variable: {var}',
                    'file': str(env_example_file)
                })

        return True

    def validate_docker_config_docs(self):
        """Validate Docker configuration includes Pusher setup"""
        docker_compose_file = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/infrastructure/docker/docker-compose.dev.yml")

        if not docker_compose_file.exists():
            self.issues.append({
                'issue': 'Docker compose file not found',
                'file': str(docker_compose_file)
            })
            return False

        with open(docker_compose_file, 'r') as f:
            docker_content = f.read()

        # Check for Pusher environment variables in docker config
        if 'PUSHER_KEY' not in docker_content:
            self.issues.append({
                'issue': 'Docker config missing Pusher environment variables',
                'file': str(docker_compose_file)
            })

        return True

    def generate_report(self):
        """Generate comprehensive documentation validation report"""
        print("Running documentation validation...")

        self.validate_no_active_websocket_refs()
        self.validate_pusher_documentation()
        self.validate_api_documentation_consistency()
        self.validate_environment_config_docs()
        self.validate_docker_config_docs()

        report = {
            'total_issues': len(self.issues),
            'issues': self.issues,
            'validation_passed': len(self.issues) == 0
        }

        return report

if __name__ == "__main__":
    validator = DocumentationValidator()

    print("=== ToolboxAI Documentation Validation ===")
    report = validator.generate_report()

    if report['validation_passed']:
        print("✅ All documentation validation checks passed!")
    else:
        print(f"❌ Found {report['total_issues']} documentation issues:")
        for issue in report['issues']:
            print(f"  - {issue}")

    # Write report to file
    report_file = Path("/Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/tests/reports/documentation_validation_report.json")
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nDetailed report saved to: {report_file}")