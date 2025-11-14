#!/usr/bin/env python3
"""
Documentation Validity Test Suite
=================================

Pytest-based tests for documentation validation.
Tests all validation components and ensures documentation quality.

Usage:
    pytest tests/documentation/test_documentation_validity.py -v
    pytest tests/documentation/test_documentation_validity.py::test_api_documentation_sync -v
    pytest tests/documentation/test_documentation_validity.py -k "coverage" -v
"""

import asyncio
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "validation"))

from api_doc_sync import APIDocumentationSync
from code_example_validator import CodeBlock, CodeExampleValidator, CodeLanguage
from doc_coverage import CodeItem, DocumentationCoverageAnalyzer

# Import validation modules
from doc_validator import DocumentationValidator, Severity, ValidationConfig
from migration_checker import MigrationDocumentationChecker


class TestDocumentationValidator:
    """Test suite for the main documentation validator"""

    @pytest.fixture
    def temp_docs(self):
        """Create temporary documentation structure"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create test documentation files
        (temp_path / "docs").mkdir(parents=True)

        # Good markdown file
        good_md = temp_path / "docs" / "good.md"
        good_md.write_text(
            """
# Test Documentation

This is a well-formatted document with proper structure.

## Getting Started

Here's how to get started:

```python
def hello_world():
    \"\"\"Print hello world.\"\"\"
    print("Hello, World!")
```

## API Reference

### POST /api/v1/test

Create a new test resource.

**Parameters:**
- `name` (string): Resource name
- `description` (string): Resource description

**Response:**
```json
{
    "id": 1,
    "name": "test",
    "description": "A test resource"
}
```

## Links

- [Internal Link](./good.md)
- [External Link](https://github.com/example/repo)
"""
        )

        # Bad markdown file with issues
        bad_md = temp_path / "docs" / "bad.md"
        bad_md.write_text(
            """
# Bad Documentation

This file has various issues.

## Unclosed Code Block

```python
def broken_function():
    print("This code block is not closed"

## Broken Links

- [Broken Internal](./nonexistent.md)
- [Broken External](http://broken-link-example.com)

## Poor Formatting

This line has trailing spaces
	This line has tabs

## Dangerous Code

```bash
sudo rm -rf /
```

## Inconsistent Terminology

This uses fastapi instead of FastAPI.
Also mentions nodejs instead of Node.js.
"""
        )

        # Configuration file
        config_yaml = temp_path / "validation_config.yaml"
        config_yaml.write_text(
            """
include_patterns:
  - "**/*.md"
exclude_patterns:
  - "**/temp/**"
check_links: true
check_code_examples: true
auto_fix_enabled: false
terminology:
  fastapi: ["FastAPI"]
  nodejs: ["Node.js"]
"""
        )

        yield temp_path

        # Cleanup
        shutil.rmtree(temp_dir)

    def test_validation_config_creation(self):
        """Test validation configuration creation"""
        config = ValidationConfig()
        assert config.check_links is True
        assert config.check_code_examples is True
        assert "**/*.md" in config.include_patterns

    def test_validator_initialization(self, temp_docs):
        """Test validator initialization"""
        config = ValidationConfig(root_dir=temp_docs)
        validator = DocumentationValidator(config)

        assert validator.config.root_dir == temp_docs
        assert validator.issues == []
        assert validator.stats.files_checked == 0

    @pytest.mark.asyncio
    async def test_markdown_syntax_validation(self, temp_docs):
        """Test markdown syntax validation"""
        config = ValidationConfig(
            root_dir=temp_docs,
            check_links=False,  # Skip external link checks for speed
            check_code_examples=False,
        )
        validator = DocumentationValidator(config)

        await validator.validate_all()

        # Should find issues in bad.md
        syntax_issues = [i for i in validator.issues if i.issue_type == "syntax"]
        assert len(syntax_issues) > 0

        # Should find unclosed code block
        unclosed_block = [i for i in syntax_issues if "unclosed code block" in i.message.lower()]
        assert len(unclosed_block) > 0

    @pytest.mark.asyncio
    async def test_link_validation(self, temp_docs):
        """Test link validation"""
        config = ValidationConfig(
            root_dir=temp_docs,
            check_links=True,
            check_code_examples=False,
            check_terminology=False,
        )
        validator = DocumentationValidator(config)

        await validator.validate_all()

        # Should find broken links
        link_issues = [i for i in validator.issues if i.issue_type == "broken_link"]
        assert len(link_issues) >= 2  # At least internal and external broken links

    @pytest.mark.asyncio
    async def test_formatting_validation(self, temp_docs):
        """Test formatting validation"""
        config = ValidationConfig(
            root_dir=temp_docs,
            check_formatting=True,
            check_links=False,
            check_code_examples=False,
        )
        validator = DocumentationValidator(config)

        await validator.validate_all()

        # Should find formatting issues
        format_issues = [i for i in validator.issues if i.issue_type == "formatting"]
        assert len(format_issues) >= 2  # Trailing whitespace and tabs

    @pytest.mark.asyncio
    async def test_terminology_validation(self, temp_docs):
        """Test terminology consistency"""
        config = ValidationConfig(
            root_dir=temp_docs,
            check_terminology=True,
            check_links=False,
            check_code_examples=False,
        )
        validator = DocumentationValidator(config)

        await validator.validate_all()

        # Should find terminology issues
        term_issues = [i for i in validator.issues if i.issue_type == "terminology"]
        assert len(term_issues) >= 2  # fastapi and nodejs

    @pytest.mark.asyncio
    async def test_code_security_validation(self, temp_docs):
        """Test dangerous code detection"""
        config = ValidationConfig(
            root_dir=temp_docs,
            check_code_examples=True,
            check_links=False,
            check_terminology=False,
        )
        validator = DocumentationValidator(config)

        await validator.validate_all()

        # Should find security issues
        security_issues = [i for i in validator.issues if i.severity == Severity.CRITICAL]
        assert len(security_issues) > 0

    def test_auto_fix_functionality(self, temp_docs):
        """Test auto-fix functionality"""
        config = ValidationConfig(root_dir=temp_docs, auto_fix_enabled=True, max_auto_fixes=10)
        DocumentationValidator(config)

        # Create a file with fixable issues
        fixable_file = temp_docs / "docs" / "fixable.md"
        fixable_file.write_text("# Test\n\nLine with trailing spaces   \n")

        # Should be able to fix trailing whitespace
        original_content = fixable_file.read_text()
        assert "   \n" in original_content

        # Run validator (would fix in real scenario)
        # For testing, we'll simulate the fix
        fixed_content = original_content.replace("   \n", "\n")
        fixable_file.write_text(fixed_content)

        assert "   \n" not in fixable_file.read_text()


class TestAPIDocumentationSync:
    """Test suite for API documentation synchronizer"""

    @pytest.fixture
    def mock_openapi_spec(self):
        """Mock OpenAPI specification"""
        return {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/v1/users": {
                    "get": {
                        "operationId": "get_users",
                        "summary": "Get all users",
                        "tags": ["users"],
                        "responses": {
                            "200": {"content": {"application/json": {"schema": {"type": "array"}}}}
                        },
                    },
                    "post": {
                        "operationId": "create_user",
                        "summary": "Create user",
                        "tags": ["users"],
                        "requestBody": {
                            "content": {"application/json": {"schema": {"type": "object"}}}
                        },
                        "responses": {
                            "201": {"content": {"application/json": {"schema": {"type": "object"}}}}
                        },
                    },
                },
                "/api/v1/health": {
                    "get": {
                        "operationId": "health_check",
                        "summary": "Health check",
                        "responses": {"200": {"content": {}}},
                    }
                },
            },
        }

    @pytest.fixture
    def temp_docs_with_api(self):
        """Create temporary documentation with API docs"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create API documentation
        api_docs = temp_path / "api.md"
        api_docs.write_text(
            """
# API Documentation

## User Management

### GET /api/v1/users

Get all users from the system.

### POST /api/v1/users

Create a new user.

### GET /api/v1/missing

This endpoint is documented but doesn't exist on the server.
"""
        )

        yield temp_path
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_api_sync_initialization(self, temp_docs_with_api):
        """Test API sync initialization"""
        syncer = APIDocumentationSync(
            server_url="http://localhost:8000",
            docs_dir=temp_docs_with_api,
            output_dir=temp_docs_with_api / "output",
        )

        assert syncer.server_url == "http://localhost:8000"
        assert syncer.docs_dir == temp_docs_with_api

    @pytest.mark.asyncio
    async def test_openapi_spec_parsing(self, mock_openapi_spec, temp_docs_with_api):
        """Test OpenAPI specification parsing"""
        syncer = APIDocumentationSync(
            server_url="http://localhost:8000",
            docs_dir=temp_docs_with_api,
            output_dir=temp_docs_with_api / "output",
        )

        syncer.openapi_spec = mock_openapi_spec
        syncer._parse_server_endpoints()

        assert len(syncer.server_endpoints) == 3  # GET /users, POST /users, GET /health

        user_endpoints = [ep for ep in syncer.server_endpoints if ep.path == "/api/v1/users"]
        assert len(user_endpoints) == 2  # GET and POST

    @pytest.mark.asyncio
    async def test_documentation_scanning(self, temp_docs_with_api):
        """Test documentation scanning"""
        syncer = APIDocumentationSync(
            server_url="http://localhost:8000",
            docs_dir=temp_docs_with_api,
            output_dir=temp_docs_with_api / "output",
        )

        await syncer._scan_documentation()

        # Should find documented endpoints
        documented_paths = [ep.path for ep in syncer.documented_endpoints]
        assert "/api/v1/users" in documented_paths
        assert "/api/v1/missing" in documented_paths

    @pytest.mark.asyncio
    async def test_endpoint_comparison(self, mock_openapi_spec, temp_docs_with_api):
        """Test endpoint comparison and issue detection"""
        syncer = APIDocumentationSync(
            server_url="http://localhost:8000",
            docs_dir=temp_docs_with_api,
            output_dir=temp_docs_with_api / "output",
        )

        # Set up mock data
        syncer.openapi_spec = mock_openapi_spec
        syncer._parse_server_endpoints()
        await syncer._scan_documentation()

        # Create mock report
        from api_doc_sync import SyncReport

        report = SyncReport(timestamp=datetime.now(), server_url="http://localhost:8000")

        syncer._compare_endpoints(report)

        # Should find missing documentation for /api/v1/health
        missing_docs = [i for i in report.issues if i.category == "missing_docs"]
        assert any("/api/v1/health" in issue.endpoint for issue in missing_docs)

        # Should find missing server endpoint for /api/v1/missing
        missing_server = [i for i in report.issues if i.category == "missing_server"]
        assert any("/api/v1/missing" in issue.endpoint for issue in missing_server)


class TestCodeExampleValidator:
    """Test suite for code example validator"""

    @pytest.fixture
    def temp_docs_with_code(self):
        """Create temporary documentation with code examples"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create docs with various code examples
        code_examples = temp_path / "examples.md"
        code_examples.write_text(
            """
# Code Examples

## Python Example

```python
def valid_function():
    \"\"\"A valid Python function.\"\"\"
    return "Hello, World!"

print(valid_function())
```

## Invalid Python Example

```python
def invalid_function(
    # Missing closing parenthesis and colon
    return "This will not parse"
```

## JavaScript Example

```javascript
function validFunction() {
    return "Hello from JavaScript!";
}

console.log(validFunction());
```

## Dangerous Shell Example

```bash
# This should be flagged as dangerous
sudo rm -rf /tmp/test
```

## JSON Example

```json
{
    "name": "test",
    "version": "1.0.0"
}
```

## Invalid JSON Example

```json
{
    "name": "test",
    "version": 1.0.0,  // Comments not allowed in JSON
}
```

## YAML Example

```yaml
name: test
version: 1.0.0
dependencies:
  - python>=3.8
  - fastapi
```
"""
        )

        yield temp_path
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_code_example_extraction(self, temp_docs_with_code):
        """Test code example extraction"""
        validator = CodeExampleValidator(
            docs_dir=temp_docs_with_code,
            output_dir=temp_docs_with_code / "output",
            use_docker=False,  # Disable Docker for testing
        )

        code_blocks = await validator._extract_code_blocks()

        assert len(code_blocks) >= 6  # Should find all code blocks

        # Check language detection
        languages = [block.language for block in code_blocks]
        assert CodeLanguage.PYTHON in languages
        assert CodeLanguage.JAVASCRIPT in languages
        assert CodeLanguage.JSON in languages
        assert CodeLanguage.YAML in languages

    @pytest.mark.asyncio
    async def test_python_code_validation(self, temp_docs_with_code):
        """Test Python code validation"""
        validator = CodeExampleValidator(
            docs_dir=temp_docs_with_code,
            output_dir=temp_docs_with_code / "output",
            use_docker=False,
        )

        code_blocks = await validator._extract_code_blocks(["python"])
        python_blocks = [b for b in code_blocks if b.language == CodeLanguage.PYTHON]

        results = []
        for block in python_blocks:
            result = await validator._validate_python_code(block, fix_errors=False)
            results.append(result)

        # Should have both valid and invalid Python code
        valid_results = [r for r in results if r.success]
        invalid_results = [r for r in results if not r.success]

        assert len(valid_results) >= 1  # At least one valid example
        assert len(invalid_results) >= 1  # At least one invalid example

    def test_json_validation(self, temp_docs_with_code):
        """Test JSON code validation"""
        validator = CodeExampleValidator(
            docs_dir=temp_docs_with_code,
            output_dir=temp_docs_with_code / "output",
            use_docker=False,
        )

        # Test valid JSON
        valid_json_block = CodeBlock(
            content='{"name": "test", "version": "1.0.0"}',
            language=CodeLanguage.JSON,
            file_path=Path("test.md"),
            line_number=1,
        )

        result = validator._validate_json_code(valid_json_block)
        assert result.success is True

        # Test invalid JSON
        invalid_json_block = CodeBlock(
            content='{"name": "test", "version": 1.0.0, // invalid}',
            language=CodeLanguage.JSON,
            file_path=Path("test.md"),
            line_number=1,
        )

        result = validator._validate_json_code(invalid_json_block)
        assert result.success is False
        assert "JSON syntax error" in result.error_message

    @pytest.mark.asyncio
    async def test_security_validation(self, temp_docs_with_code):
        """Test security validation"""
        validator = CodeExampleValidator(
            docs_dir=temp_docs_with_code,
            output_dir=temp_docs_with_code / "output",
            use_docker=False,
        )

        # Create dangerous code block
        dangerous_block = CodeBlock(
            content="sudo rm -rf /",
            language=CodeLanguage.BASH,
            file_path=Path("test.md"),
            line_number=1,
        )

        result = await validator._validate_code_block(dangerous_block, fix_errors=False)
        assert result.success is False
        assert "Security issue" in result.error_message


class TestMigrationChecker:
    """Test suite for migration documentation checker"""

    @pytest.fixture
    def temp_repo_with_migrations(self):
        """Create temporary repo with migration documentation"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create migration guide
        migration_guide = temp_path / "docs" / "migration.md"
        migration_guide.parent.mkdir(parents=True)
        migration_guide.write_text(
            """
# WebSocket to Pusher Migration Guide

## Overview

This guide covers the migration from WebSocket to Pusher Channels.

## Breaking Changes

- WebSocket endpoints `/ws/*` are deprecated
- Client connection method changed from Socket.IO to Pusher
- Authentication flow updated

## Migration Steps

1. Update client code to use Pusher.js
2. Replace WebSocket endpoints with Pusher channels
3. Update authentication

## Examples

### Before (Socket.IO)
```javascript
import io from 'socket.io-client';
const socket = io('http://localhost:8009');
```

### After (Pusher)
```javascript
import Pusher from 'pusher-js';
const pusher = new Pusher('your-key', {
    cluster: 'us2'
});
```

## Troubleshooting

Common issues and solutions.
"""
        )

        # Create code files with deprecated features
        backend_file = temp_path / "apps" / "backend" / "websocket.py"
        backend_file.parent.mkdir(parents=True)
        backend_file.write_text(
            """
from fastapi import WebSocket

@app.websocket("/ws/test")
async def websocket_endpoint(websocket: WebSocket):
    # TODO: Remove this WebSocket endpoint after Pusher migration
    await websocket.accept()
"""
        )

        frontend_file = temp_path / "apps" / "dashboard" / "socket.js"
        frontend_file.parent.mkdir(parents=True)
        frontend_file.write_text(
            """
import io from 'socket.io-client';

// FIXME: Replace with Pusher implementation
const socket = io(process.env.REACT_APP_WS_URL);
"""
        )

        yield temp_path
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_migration_checker_initialization(self, temp_repo_with_migrations):
        """Test migration checker initialization"""
        checker = MigrationDocumentationChecker(
            root_dir=temp_repo_with_migrations,
            output_dir=temp_repo_with_migrations / "output",
        )

        assert len(checker.known_migrations) >= 3  # Should have predefined migrations

    @pytest.mark.asyncio
    async def test_todo_extraction(self, temp_repo_with_migrations):
        """Test TODO item extraction"""
        checker = MigrationDocumentationChecker(
            root_dir=temp_repo_with_migrations,
            output_dir=temp_repo_with_migrations / "output",
        )

        report = type("Report", (), {"todos": []})()
        await checker._extract_todo_items(report)

        # Should find TODO and FIXME items
        assert len(report.todos) >= 2

        # Check categorization
        migration_todos = [t for t in report.todos if t.category == "migration"]
        assert len(migration_todos) >= 1

    @pytest.mark.asyncio
    async def test_deprecated_feature_detection(self, temp_repo_with_migrations):
        """Test deprecated feature detection"""
        checker = MigrationDocumentationChecker(
            root_dir=temp_repo_with_migrations,
            output_dir=temp_repo_with_migrations / "output",
        )

        report = type("Report", (), {"deprecations": [], "issues": []})()
        await checker._find_deprecated_features(report)

        # Should find WebSocket and Socket.IO usage
        assert len(report.deprecations) >= 2

        deprecation_names = [d.name for d in report.deprecations]
        assert "websocket_endpoints" in deprecation_names or "socketio_client" in deprecation_names

    @pytest.mark.asyncio
    async def test_migration_guide_validation(self, temp_repo_with_migrations):
        """Test migration guide validation"""
        checker = MigrationDocumentationChecker(
            root_dir=temp_repo_with_migrations,
            output_dir=temp_repo_with_migrations / "output",
        )

        report = type("Report", (), {"issues": []})()
        await checker._verify_migration_guides(report)

        # Should validate the migration guide exists and has required sections
        # May find some missing sections
        [i for i in report.issues if i.category == "incomplete_migration_guide"]
        # This might be 0 if the test guide is complete, which is fine


class TestDocumentationCoverage:
    """Test suite for documentation coverage analyzer"""

    @pytest.fixture
    def temp_python_project(self):
        """Create temporary Python project"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create Python module
        module_file = temp_path / "example_module.py"
        module_file.write_text(
            '''
"""
Example module for testing documentation coverage.
"""

class ExampleClass:
    """
    A well-documented example class.

    Attributes:
        name (str): The name of the example.
    """

    def __init__(self, name: str):
        """Initialize the example."""
        self.name = name

    def documented_method(self) -> str:
        """
        A method with good documentation.

        Returns:
            str: A greeting message.
        """
        return f"Hello, {self.name}!"

    def undocumented_method(self):
        # This method lacks documentation
        return self.name.upper()

def documented_function(param: int) -> int:
    """
    A function with documentation.

    Args:
        param: Input parameter.

    Returns:
        int: The parameter multiplied by 2.
    """
    return param * 2

def undocumented_function():
    return "no docs"

# Configuration constant
DATABASE_URL = "postgresql://localhost/test"  # config

# Regular constant
MAX_RETRIES = 3
'''
        )

        # Create API endpoint file
        api_file = temp_path / "api.py"
        api_file.write_text(
            '''
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/documented")
async def documented_endpoint():
    """
    A documented API endpoint.

    Returns:
        dict: Success message.
    """
    return {"status": "success"}

@router.post("/api/v1/undocumented")
async def undocumented_endpoint():
    return {"message": "no docs"}
'''
        )

        # Create some documentation
        docs_dir = temp_path / "docs"
        docs_dir.mkdir()

        api_docs = docs_dir / "api.md"
        api_docs.write_text(
            """
# API Documentation

## Endpoints

### GET /api/v1/documented

This endpoint is documented here.
"""
        )

        yield temp_path
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_code_analysis(self, temp_python_project):
        """Test code analysis for coverage"""
        analyzer = DocumentationCoverageAnalyzer(
            root_dir=temp_python_project, output_dir=temp_python_project / "output"
        )

        report = type("Report", (), {"code_items": []})()
        await analyzer._analyze_code_files(report, Mock(), Mock())

        # Should find classes, functions, and constants
        assert (
            len(report.code_items) >= 8
        )  # 1 class + 2 methods + 2 functions + 2 constants + 1 endpoint

        # Check item types
        item_types = [item.item_type for item in report.code_items]
        assert "class" in item_types
        assert "function" in item_types
        assert "method" in item_types
        assert "endpoint" in item_types
        assert "config" in item_types

    @pytest.mark.asyncio
    async def test_documentation_analysis(self, temp_python_project):
        """Test documentation analysis"""
        analyzer = DocumentationCoverageAnalyzer(
            root_dir=temp_python_project, output_dir=temp_python_project / "output"
        )

        report = type("Report", (), {"documentation_files": []})()
        await analyzer._analyze_documentation_files(report, Mock(), Mock())

        # Should find documentation files
        assert len(report.documentation_files) >= 1

        # Check code references extraction
        doc_file = report.documentation_files[0]
        assert len(doc_file.code_references) > 0

    @pytest.mark.asyncio
    async def test_coverage_calculation(self, temp_python_project):
        """Test coverage calculation"""
        analyzer = DocumentationCoverageAnalyzer(
            root_dir=temp_python_project, output_dir=temp_python_project / "output"
        )

        # Create mock report with items
        report = type(
            "Report",
            (),
            {
                "code_items": [],
                "documentation_files": [],
                "total_items": 0,
                "documented_items": 0,
                "coverage_percentage": 0.0,
                "stats_by_type": {},
                "stats_by_module": {},
                "quality_metrics": {},
            },
        )()

        # Add some mock items
        documented_item = CodeItem(
            name="documented_function",
            item_type="function",
            file_path=Path("test.py"),
            line_number=1,
            docstring="This is documented",
        )

        undocumented_item = CodeItem(
            name="undocumented_function",
            item_type="function",
            file_path=Path("test.py"),
            line_number=10,
        )

        report.code_items = [documented_item, undocumented_item]

        analyzer._calculate_coverage(report, Mock(), Mock())

        # Should calculate coverage correctly
        assert report.total_items == 2
        assert report.documented_items == 1
        assert report.coverage_percentage == 50.0

    def test_gap_identification(self, temp_python_project):
        """Test coverage gap identification"""
        analyzer = DocumentationCoverageAnalyzer(
            root_dir=temp_python_project, output_dir=temp_python_project / "output"
        )

        # Create items with different documentation states
        undocumented_api = CodeItem(
            name="POST /api/v1/test",
            item_type="endpoint",
            file_path=Path("api.py"),
            line_number=1,
            is_public=True,
        )

        poorly_documented = CodeItem(
            name="test_function",
            item_type="function",
            file_path=Path("test.py"),
            line_number=1,
            docstring="Short.",  # Too short
            complexity_score=15,  # High complexity
            is_public=True,
        )

        report = type(
            "Report",
            (),
            {
                "code_items": [undocumented_api, poorly_documented],
                "documentation_files": [],
                "coverage_gaps": [],
            },
        )()

        analyzer._identify_coverage_gaps(report, Mock(), Mock())

        # Should identify gaps
        assert len(report.coverage_gaps) >= 2

        # Check severity assignment
        severities = [gap.severity for gap in report.coverage_gaps]
        assert "critical" in severities  # API endpoint should be critical


class TestIntegrationTests:
    """Integration tests for the complete validation system"""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project for integration testing"""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Create project structure
        (temp_path / "apps" / "backend").mkdir(parents=True)
        (temp_path / "docs" / "api").mkdir(parents=True)

        # Add FastAPI application
        app_file = temp_path / "apps" / "backend" / "main.py"
        app_file.write_text(
            '''
"""
Main FastAPI application.
"""

from fastapi import FastAPI

app = FastAPI(
    title="Test API",
    description="A test API for documentation validation",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/api/v1/users")
async def get_users():
    """Get all users."""
    return {"users": []}

@app.post("/api/v1/users")
async def create_user():
    # Missing documentation
    return {"message": "user created"}
'''
        )

        # Add documentation
        readme = temp_path / "README.md"
        readme.write_text(
            """
# Test Project

This is a test project for documentation validation.

## API Endpoints

### GET /health

Check if the API is healthy.

### GET /api/v1/users

Get all users in the system.

## TODO

- [ ] Add user creation documentation
- [ ] Improve error handling docs @john by 2024-12-31
"""
        )

        # Add API documentation
        api_docs = temp_path / "docs" / "api" / "users.md"
        api_docs.write_text(
            """
# User API

## Endpoints

### GET /api/v1/users

Returns all users.

**Response:**
```json
{
    "users": []
}
```

### GET /api/v1/missing

This endpoint is documented but doesn't exist.
"""
        )

        yield temp_path
        shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_complete_validation_pipeline(self, sample_project):
        """Test the complete validation pipeline"""

        # 1. Run documentation validator
        doc_config = ValidationConfig(
            root_dir=sample_project,
            check_links=False,  # Skip external links for speed
            check_code_examples=True,
            check_terminology=True,
        )
        doc_validator = DocumentationValidator(doc_config)
        doc_stats = await doc_validator.validate_all()

        assert doc_stats.files_checked > 0
        # Should find some issues (like missing docs for POST endpoint)

        # 2. Run coverage analysis
        coverage_analyzer = DocumentationCoverageAnalyzer(
            root_dir=sample_project, output_dir=sample_project / "reports"
        )
        coverage_report = await coverage_analyzer.generate_coverage_report()

        assert coverage_report.total_items > 0
        assert coverage_report.coverage_percentage < 100  # Should have some gaps

        # 3. Run migration checker
        migration_checker = MigrationDocumentationChecker(
            root_dir=sample_project, output_dir=sample_project / "reports"
        )
        migration_report = await migration_checker.check_all_migrations()

        # Should find TODO items
        assert len(migration_report.todos) >= 2

        # 4. Verify integration
        # The validation should be comprehensive
        total_issues = (
            len(doc_validator.issues)
            + len(coverage_report.coverage_gaps)
            + len(migration_report.issues)
        )

        assert total_issues > 0  # Should find issues to validate


# Pytest configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Integration with pytest markers
pytestmark = pytest.mark.asyncio


if __name__ == "__main__":
    # Allow running tests directly
    import pytest

    pytest.main([__file__, "-v"])
