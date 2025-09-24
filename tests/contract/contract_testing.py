#!/usr/bin/env python3
"""Contract Testing Framework for ToolBoxAI.

This module implements consumer-driven contract testing to ensure API compatibility
between services and prevent breaking changes.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, field
import jsonschema
from jsonschema import validate, ValidationError
import requests
import asyncio
import aiohttp
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
import hashlib
import difflib

console = Console()


@dataclass
class Contract:
    """Represents an API contract."""

    id: str
    name: str
    version: str
    consumer: str
    provider: str
    endpoints: List[Dict[str, Any]]
    schemas: Dict[str, Any]
    created_at: str
    updated_at: str
    status: str = "draft"
    tags: List[str] = field(default_factory=list)


@dataclass
class ContractTest:
    """Represents a contract test case."""

    contract_id: str
    endpoint: str
    method: str
    request: Dict[str, Any]
    expected_response: Dict[str, Any]
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class ContractValidator:
    """Validates API responses against contracts."""

    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.test_results: List[Dict] = []

    def load_contract(self, contract_path: Path) -> Contract:
        """Load a contract from file."""
        with open(contract_path) as f:
            if contract_path.suffix == ".json":
                data = json.load(f)
            else:  # YAML
                data = yaml.safe_load(f)

        contract = Contract(
            id=data.get("id", self._generate_id(data)),
            name=data["name"],
            version=data["version"],
            consumer=data["consumer"],
            provider=data["provider"],
            endpoints=data["endpoints"],
            schemas=data.get("schemas", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            status=data.get("status", "draft"),
            tags=data.get("tags", []),
        )

        self.contracts[contract.id] = contract
        return contract

    def _generate_id(self, data: Dict) -> str:
        """Generate contract ID from data."""
        content = f"{data['consumer']}_{data['provider']}_{data['version']}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def validate_schema(self, data: Any, schema: Dict) -> Tuple[bool, Optional[str]]:
        """Validate data against JSON schema."""
        try:
            validate(instance=data, schema=schema)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def validate_response(
        self,
        response: Dict[str, Any],
        expected: Dict[str, Any],
        rules: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Validate API response against expected contract."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        rules = rules or {}

        # Check status code
        if "status_code" in expected:
            if response.get("status_code") != expected["status_code"]:
                result["valid"] = False
                result["errors"].append(
                    f"Status code mismatch: expected {expected['status_code']}, "
                    f"got {response.get('status_code')}"
                )

        # Check headers
        if "headers" in expected:
            self._validate_headers(
                response.get("headers", {}),
                expected["headers"],
                result,
                rules.get("headers", {})
            )

        # Check body
        if "body" in expected:
            self._validate_body(
                response.get("body"),
                expected["body"],
                result,
                rules.get("body", {})
            )

        # Check schema if provided
        if "schema" in expected:
            valid, error = self.validate_schema(response.get("body"), expected["schema"])
            if not valid:
                result["valid"] = False
                result["errors"].append(f"Schema validation failed: {error}")

        return result

    def _validate_headers(
        self,
        actual: Dict,
        expected: Dict,
        result: Dict,
        rules: Dict
    ):
        """Validate response headers."""
        for key, value in expected.items():
            if key not in actual:
                if rules.get("optional_headers") and key in rules["optional_headers"]:
                    result["warnings"].append(f"Optional header missing: {key}")
                else:
                    result["valid"] = False
                    result["errors"].append(f"Required header missing: {key}")
            elif actual[key] != value and not rules.get("ignore_header_values"):
                # Check if it's a pattern match
                if isinstance(value, str) and value.startswith("regex:"):
                    import re
                    pattern = value[6:]  # Remove "regex:" prefix
                    if not re.match(pattern, actual[key]):
                        result["valid"] = False
                        result["errors"].append(
                            f"Header {key} doesn't match pattern: {pattern}"
                        )
                else:
                    result["valid"] = False
                    result["errors"].append(
                        f"Header value mismatch for {key}: "
                        f"expected {value}, got {actual[key]}"
                    )

    def _validate_body(
        self,
        actual: Any,
        expected: Any,
        result: Dict,
        rules: Dict
    ):
        """Validate response body."""
        if isinstance(expected, dict) and isinstance(actual, dict):
            # Validate object fields
            for key, value in expected.items():
                if key not in actual:
                    if rules.get("optional_fields") and key in rules["optional_fields"]:
                        result["warnings"].append(f"Optional field missing: {key}")
                    else:
                        result["valid"] = False
                        result["errors"].append(f"Required field missing: {key}")
                else:
                    # Recursive validation
                    if isinstance(value, dict):
                        self._validate_body(
                            actual[key],
                            value,
                            result,
                            rules.get(key, {})
                        )
                    elif isinstance(value, list) and value:
                        # Validate array items
                        if not isinstance(actual[key], list):
                            result["valid"] = False
                            result["errors"].append(
                                f"Type mismatch for {key}: expected array, got {type(actual[key])}"
                            )
                        elif rules.get("validate_array_items"):
                            # Validate each item
                            for i, item in enumerate(actual[key][:len(value)]):
                                self._validate_body(
                                    item,
                                    value[0] if value else {},
                                    result,
                                    rules
                                )
                    else:
                        # Direct value comparison
                        if not self._values_match(actual[key], value, rules):
                            result["valid"] = False
                            result["errors"].append(
                                f"Value mismatch for {key}: "
                                f"expected {value}, got {actual[key]}"
                            )

            # Check for unexpected fields
            if rules.get("strict"):
                for key in actual:
                    if key not in expected:
                        result["warnings"].append(f"Unexpected field: {key}")

        elif isinstance(expected, list) and isinstance(actual, list):
            # Validate arrays
            if rules.get("validate_array_length") and len(actual) != len(expected):
                result["valid"] = False
                result["errors"].append(
                    f"Array length mismatch: expected {len(expected)}, got {len(actual)}"
                )
            elif expected:  # Has sample item
                for item in actual:
                    self._validate_body(item, expected[0], result, rules)

        elif actual != expected:
            # Primitive value mismatch
            if not self._values_match(actual, expected, rules):
                result["valid"] = False
                result["errors"].append(
                    f"Value mismatch: expected {expected}, got {actual}"
                )

    def _values_match(self, actual: Any, expected: Any, rules: Dict) -> bool:
        """Check if values match according to rules."""
        if rules.get("ignore_values"):
            return True

        if isinstance(expected, str):
            # Check for special patterns
            if expected == "ANY":
                return True
            elif expected == "NOT_NULL":
                return actual is not None
            elif expected == "NOT_EMPTY":
                return bool(actual)
            elif expected.startswith("TYPE:"):
                expected_type = expected[5:].lower()
                actual_type = type(actual).__name__.lower()
                return actual_type == expected_type
            elif expected.startswith("regex:"):
                import re
                pattern = expected[6:]
                return bool(re.match(pattern, str(actual)))

        return actual == expected

    async def test_contract(
        self,
        contract: Contract,
        base_url: str,
        auth: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Test all endpoints in a contract."""
        console.print(f"\n[cyan]Testing contract: {contract.name} v{contract.version}[/cyan]")

        results = {
            "contract_id": contract.id,
            "contract_name": contract.name,
            "version": contract.version,
            "tested_at": datetime.now().isoformat(),
            "base_url": base_url,
            "endpoints": [],
            "summary": {
                "total": len(contract.endpoints),
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            }
        }

        async with aiohttp.ClientSession() as session:
            for endpoint in contract.endpoints:
                endpoint_result = await self._test_endpoint(
                    session,
                    endpoint,
                    base_url,
                    auth
                )

                results["endpoints"].append(endpoint_result)

                if endpoint_result["passed"]:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1

                if endpoint_result.get("warnings"):
                    results["summary"]["warnings"] += len(endpoint_result["warnings"])

                # Display result
                status = "✓" if endpoint_result["passed"] else "✗"
                color = "green" if endpoint_result["passed"] else "red"
                console.print(
                    f"  [{color}]{status}[/{color}] {endpoint['method']} {endpoint['path']}"
                )

        self.test_results.append(results)
        return results

    async def _test_endpoint(
        self,
        session: aiohttp.ClientSession,
        endpoint: Dict,
        base_url: str,
        auth: Optional[Dict]
    ) -> Dict[str, Any]:
        """Test a single endpoint."""
        url = base_url + endpoint["path"]
        method = endpoint["method"]

        # Prepare request
        headers = endpoint.get("request", {}).get("headers", {})
        if auth:
            headers.update(auth)

        body = endpoint.get("request", {}).get("body")
        params = endpoint.get("request", {}).get("params")

        # Make request
        try:
            async with session.request(
                method,
                url,
                headers=headers,
                json=body if body and method != "GET" else None,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                # Parse response
                response_data = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                }

                try:
                    response_data["body"] = await response.json()
                except:
                    response_data["body"] = await response.text()

                # Validate response
                validation_result = self.validate_response(
                    response_data,
                    endpoint.get("response", {}),
                    endpoint.get("validation_rules", {})
                )

                return {
                    "endpoint": f"{method} {endpoint['path']}",
                    "passed": validation_result["valid"],
                    "errors": validation_result["errors"],
                    "warnings": validation_result["warnings"],
                    "response": response_data,
                }

        except Exception as e:
            return {
                "endpoint": f"{method} {endpoint['path']}",
                "passed": False,
                "errors": [str(e)],
                "warnings": [],
                "response": None,
            }

    def generate_contract_from_openapi(
        self,
        openapi_spec: Union[str, Path, Dict],
        consumer: str = "consumer",
        provider: str = "provider"
    ) -> Contract:
        """Generate contract from OpenAPI specification."""
        # Load OpenAPI spec
        if isinstance(openapi_spec, (str, Path)):
            with open(openapi_spec) as f:
                spec = json.load(f) if str(openapi_spec).endswith('.json') else yaml.safe_load(f)
        else:
            spec = openapi_spec

        # Extract endpoints
        endpoints = []
        schemas = spec.get("components", {}).get("schemas", {})

        for path, methods in spec.get("paths", {}).items():
            for method, details in methods.items():
                if method in ["get", "post", "put", "delete", "patch"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "description": details.get("summary", ""),
                        "request": self._extract_request(details),
                        "response": self._extract_response(details),
                        "validation_rules": {
                            "strict": False,
                            "validate_array_items": True,
                        }
                    }
                    endpoints.append(endpoint)

        # Create contract
        contract = Contract(
            id=self._generate_id({"consumer": consumer, "provider": provider, "version": "1.0.0"}),
            name=spec.get("info", {}).get("title", "API Contract"),
            version=spec.get("info", {}).get("version", "1.0.0"),
            consumer=consumer,
            provider=provider,
            endpoints=endpoints,
            schemas=schemas,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            status="generated",
            tags=["openapi", "generated"],
        )

        return contract

    def _extract_request(self, endpoint_spec: Dict) -> Dict:
        """Extract request specification from OpenAPI."""
        request = {}

        # Parameters
        params = {}
        headers = {}
        for param in endpoint_spec.get("parameters", []):
            if param["in"] == "query":
                params[param["name"]] = param.get("example", "ANY")
            elif param["in"] == "header":
                headers[param["name"]] = param.get("example", "ANY")

        if params:
            request["params"] = params
        if headers:
            request["headers"] = headers

        # Request body
        if "requestBody" in endpoint_spec:
            content = endpoint_spec["requestBody"].get("content", {})
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                request["body"] = self._schema_to_example(schema)

        return request

    def _extract_response(self, endpoint_spec: Dict) -> Dict:
        """Extract response specification from OpenAPI."""
        response = {}

        # Get 200 response by default
        responses = endpoint_spec.get("responses", {})
        success_response = responses.get("200") or responses.get("201") or {}

        response["status_code"] = 200

        # Headers
        if "headers" in success_response:
            response["headers"] = {
                name: header.get("example", "ANY")
                for name, header in success_response["headers"].items()
            }

        # Body
        content = success_response.get("content", {})
        if "application/json" in content:
            schema = content["application/json"].get("schema", {})
            response["body"] = self._schema_to_example(schema)
            response["schema"] = schema

        return response

    def _schema_to_example(self, schema: Dict) -> Any:
        """Convert JSON schema to example value."""
        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type")

        if schema_type == "object":
            example = {}
            for prop, prop_schema in schema.get("properties", {}).items():
                example[prop] = self._schema_to_example(prop_schema)
            return example

        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self._schema_to_example(items_schema)]

        elif schema_type == "string":
            if "enum" in schema:
                return schema["enum"][0]
            elif "format" in schema:
                formats = {
                    "date": "2024-01-01",
                    "date-time": "2024-01-01T00:00:00Z",
                    "email": "user@example.com",
                    "uuid": "123e4567-e89b-12d3-a456-426614174000",
                    "uri": "https://example.com",
                }
                return formats.get(schema["format"], "string")
            return "string"

        elif schema_type == "number":
            return 0.0

        elif schema_type == "integer":
            return 0

        elif schema_type == "boolean":
            return True

        elif schema_type == "null":
            return None

        return "ANY"

    def compare_contracts(
        self,
        old_contract: Contract,
        new_contract: Contract
    ) -> Dict[str, Any]:
        """Compare two contract versions for breaking changes."""
        comparison = {
            "breaking_changes": [],
            "non_breaking_changes": [],
            "additions": [],
            "removals": [],
        }

        old_endpoints = {f"{e['method']} {e['path']}": e for e in old_contract.endpoints}
        new_endpoints = {f"{e['method']} {e['path']}": e for e in new_contract.endpoints}

        # Check for removed endpoints (breaking)
        for key in old_endpoints:
            if key not in new_endpoints:
                comparison["breaking_changes"].append({
                    "type": "endpoint_removed",
                    "endpoint": key,
                })
                comparison["removals"].append(key)

        # Check for added endpoints (non-breaking)
        for key in new_endpoints:
            if key not in old_endpoints:
                comparison["non_breaking_changes"].append({
                    "type": "endpoint_added",
                    "endpoint": key,
                })
                comparison["additions"].append(key)

        # Check for changes in existing endpoints
        for key in old_endpoints:
            if key in new_endpoints:
                old_ep = old_endpoints[key]
                new_ep = new_endpoints[key]

                # Check request changes
                request_changes = self._compare_requests(
                    old_ep.get("request", {}),
                    new_ep.get("request", {})
                )

                for change in request_changes:
                    if change["breaking"]:
                        comparison["breaking_changes"].append({
                            "type": "request_change",
                            "endpoint": key,
                            "change": change,
                        })
                    else:
                        comparison["non_breaking_changes"].append({
                            "type": "request_change",
                            "endpoint": key,
                            "change": change,
                        })

                # Check response changes
                response_changes = self._compare_responses(
                    old_ep.get("response", {}),
                    new_ep.get("response", {})
                )

                for change in response_changes:
                    if change["breaking"]:
                        comparison["breaking_changes"].append({
                            "type": "response_change",
                            "endpoint": key,
                            "change": change,
                        })
                    else:
                        comparison["non_breaking_changes"].append({
                            "type": "response_change",
                            "endpoint": key,
                            "change": change,
                        })

        return comparison

    def _compare_requests(self, old_req: Dict, new_req: Dict) -> List[Dict]:
        """Compare request specifications."""
        changes = []

        # Check required parameters
        old_params = old_req.get("params", {})
        new_params = new_req.get("params", {})

        for param in old_params:
            if param not in new_params:
                changes.append({
                    "breaking": True,
                    "description": f"Required parameter '{param}' removed",
                })

        for param in new_params:
            if param not in old_params:
                changes.append({
                    "breaking": False,
                    "description": f"Optional parameter '{param}' added",
                })

        return changes

    def _compare_responses(self, old_res: Dict, new_res: Dict) -> List[Dict]:
        """Compare response specifications."""
        changes = []

        # Check status code changes
        if old_res.get("status_code") != new_res.get("status_code"):
            changes.append({
                "breaking": True,
                "description": f"Status code changed from {old_res.get('status_code')} to {new_res.get('status_code')}",
            })

        # Check required fields in response body
        old_body = old_res.get("body", {})
        new_body = new_res.get("body", {})

        if isinstance(old_body, dict) and isinstance(new_body, dict):
            # Check for removed fields (breaking for consumers)
            for field in old_body:
                if field not in new_body:
                    changes.append({
                        "breaking": True,
                        "description": f"Response field '{field}' removed",
                    })

            # Check for added fields (non-breaking)
            for field in new_body:
                if field not in old_body:
                    changes.append({
                        "breaking": False,
                        "description": f"Response field '{field}' added",
                    })

        return changes

    def generate_report(self) -> str:
        """Generate contract testing report."""
        report_lines = []
        report_lines.append("# Contract Testing Report")
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append("")

        for result in self.test_results:
            report_lines.append(f"## Contract: {result['contract_name']} v{result['version']}")
            report_lines.append(f"Tested at: {result['tested_at']}")
            report_lines.append(f"Base URL: {result['base_url']}")
            report_lines.append("")

            summary = result["summary"]
            report_lines.append("### Summary")
            report_lines.append(f"- Total Endpoints: {summary['total']}")
            report_lines.append(f"- Passed: {summary['passed']}")
            report_lines.append(f"- Failed: {summary['failed']}")
            report_lines.append(f"- Warnings: {summary['warnings']}")
            report_lines.append("")

            if any(not ep["passed"] for ep in result["endpoints"]):
                report_lines.append("### Failed Endpoints")
                for endpoint in result["endpoints"]:
                    if not endpoint["passed"]:
                        report_lines.append(f"- {endpoint['endpoint']}")
                        for error in endpoint["errors"]:
                            report_lines.append(f"  - Error: {error}")
                report_lines.append("")

        return "\n".join(report_lines)


async def main():
    """Example usage of contract testing."""
    validator = ContractValidator()

    # Example contract
    contract_data = {
        "name": "User API Contract",
        "version": "1.0.0",
        "consumer": "dashboard",
        "provider": "backend",
        "endpoints": [
            {
                "path": "/api/v1/users",
                "method": "GET",
                "request": {
                    "headers": {
                        "Authorization": "Bearer ANY",
                    }
                },
                "response": {
                    "status_code": 200,
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "body": [
                        {
                            "id": "TYPE:string",
                            "username": "TYPE:string",
                            "email": "regex:.*@.*\\..*",
                            "role": "ANY",
                        }
                    ],
                },
                "validation_rules": {
                    "validate_array_items": True,
                }
            },
            {
                "path": "/api/v1/users/{id}",
                "method": "GET",
                "request": {
                    "headers": {
                        "Authorization": "Bearer ANY",
                    }
                },
                "response": {
                    "status_code": 200,
                    "body": {
                        "id": "NOT_NULL",
                        "username": "TYPE:string",
                        "email": "TYPE:string",
                        "role": "TYPE:string",
                        "created_at": "TYPE:string",
                    }
                }
            }
        ],
    }

    # Create contract
    contract = Contract(
        id="user_api_v1",
        name=contract_data["name"],
        version=contract_data["version"],
        consumer=contract_data["consumer"],
        provider=contract_data["provider"],
        endpoints=contract_data["endpoints"],
        schemas={},
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
    )

    # Test contract
    results = await validator.test_contract(
        contract,
        base_url="http://localhost:8009",
        auth={"Authorization": "Bearer test-token"}
    )

    # Display results
    console.print("\n")
    console.print(Panel.fit(
        f"[bold]Contract Test Results[/bold]\n\n"
        f"Contract: {results['contract_name']}\n"
        f"Version: {results['version']}\n"
        f"Passed: {results['summary']['passed']}/{results['summary']['total']}\n"
        f"Warnings: {results['summary']['warnings']}",
        title="Summary"
    ))

    # Generate report
    report = validator.generate_report()
    console.print("\n[dim]Report generated[/dim]")


if __name__ == "__main__":
    asyncio.run(main())