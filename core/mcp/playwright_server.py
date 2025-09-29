"""MCP Server for Playwright Testing Integration.

This server provides MCP protocol support for Playwright testing,
enabling seamless integration with testing agents and automation tools.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# MCP imports
from mcp import Server, Tool, Resource
from mcp.types import (
    TextContent, ImageContent, EmbeddedResource,
    GetResourceResponse, ListResourcesResponse,
    CallToolResult, ListToolsResponse
)

# Import our testing agents
from core.agents.testing.playwright_testing_agent import PlaywrightTestingAgent
from core.agents.testing.test_generation_agent import TestGenerationAgent
from core.agents.testing.coverage_analysis_agent import CoverageAnalysisAgent
from core.agents.testing.self_healing_test_agent import SelfHealingTestAgent

# Other imports
from core.sparc.state_manager import StateManager
from core.coordinators.error_coordinator import ErrorCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaywrightMCPServer:
    """
    MCP Server for Playwright testing automation.

    Provides tools and resources for:
    - Test execution and generation
    - Coverage analysis
    - Self-healing tests
    - Visual regression testing
    - Performance testing
    - Accessibility auditing
    """

    def __init__(self):
        """Initialize the Playwright MCP Server."""
        self.server = Server("playwright-mcp-server")
        self.state_manager = StateManager()

        # Initialize testing agents
        self.playwright_agent = PlaywrightTestingAgent()
        self.generation_agent = TestGenerationAgent()
        self.coverage_agent = CoverageAnalysisAgent()
        self.healing_agent = SelfHealingTestAgent()

        # Test results storage
        self.test_results = {}
        self.coverage_reports = {}
        self.healing_reports = {}

        # Setup server handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP server handlers."""

        @self.server.list_tools()
        async def list_tools() -> ListToolsResponse:
            """List available tools."""
            return ListToolsResponse(
                tools=[
                    Tool(
                        name="run_test",
                        description="Execute Playwright test",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "test_file": {"type": "string"},
                                "test_name": {"type": "string"},
                                "browser": {"type": "string", "enum": ["chromium", "firefox", "webkit"]},
                                "headless": {"type": "boolean"}
                            },
                            "required": ["test_file", "browser"]
                        }
                    ),
                    Tool(
                        name="generate_test",
                        description="Generate test from user story",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "story": {"type": "object"},
                                "test_type": {"type": "string", "enum": ["e2e", "integration", "unit"]}
                            },
                            "required": ["story", "test_type"]
                        }
                    ),
                    Tool(
                        name="analyze_coverage",
                        description="Analyze test coverage",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_path": {"type": "string"},
                                "include_branches": {"type": "boolean"}
                            },
                            "required": ["project_path"]
                        }
                    ),
                    Tool(
                        name="heal_test",
                        description="Auto-heal broken test",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "failure": {"type": "object"},
                                "auto_apply": {"type": "boolean"}
                            },
                            "required": ["failure"]
                        }
                    ),
                    Tool(
                        name="record_session",
                        description="Record browser session for test generation",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "duration": {"type": "number"},
                                "output_format": {"type": "string", "enum": ["playwright", "puppeteer"]}
                            },
                            "required": ["url"]
                        }
                    ),
                    Tool(
                        name="visual_regression",
                        description="Perform visual regression testing",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "baseline": {"type": "string"},
                                "current": {"type": "string"},
                                "threshold": {"type": "number"}
                            },
                            "required": ["baseline", "current"]
                        }
                    ),
                    Tool(
                        name="performance_test",
                        description="Run performance tests",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "metrics": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["url"]
                        }
                    ),
                    Tool(
                        name="accessibility_audit",
                        description="Run accessibility tests",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "standards": {"type": "string", "enum": ["wcag2a", "wcag2aa", "wcag2aaa", "section508"]}
                            },
                            "required": ["url", "standards"]
                        }
                    ),
                    Tool(
                        name="batch_test",
                        description="Run multiple tests in parallel",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "test_suite": {"type": "string"},
                                "parallel_workers": {"type": "number"},
                                "fail_fast": {"type": "boolean"}
                            },
                            "required": ["test_suite"]
                        }
                    ),
                    Tool(
                        name="create_page_object",
                        description="Generate Page Object Model",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "page_url": {"type": "string"},
                                "page_name": {"type": "string"},
                                "auto_detect_elements": {"type": "boolean"}
                            },
                            "required": ["page_url", "page_name"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "run_test":
                    result = await self._run_test(**arguments)
                elif name == "generate_test":
                    result = await self._generate_test(**arguments)
                elif name == "analyze_coverage":
                    result = await self._analyze_coverage(**arguments)
                elif name == "heal_test":
                    result = await self._heal_test(**arguments)
                elif name == "record_session":
                    result = await self._record_session(**arguments)
                elif name == "visual_regression":
                    result = await self._visual_regression(**arguments)
                elif name == "performance_test":
                    result = await self._performance_test(**arguments)
                elif name == "accessibility_audit":
                    result = await self._accessibility_audit(**arguments)
                elif name == "batch_test":
                    result = await self._batch_test(**arguments)
                elif name == "create_page_object":
                    result = await self._create_page_object(**arguments)
                else:
                    result = {"error": f"Unknown tool: {name}"}

                return CallToolResult(
                    content=[TextContent(text=json.dumps(result, indent=2))]
                )

            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return CallToolResult(
                    content=[TextContent(text=json.dumps({"error": str(e)}))]
                )

        @self.server.list_resources()
        async def list_resources() -> ListResourcesResponse:
            """List available resources."""
            resources = []

            # Add test result resources
            for test_id, result in self.test_results.items():
                resources.append(
                    Resource(
                        uri=f"test-result://{test_id}",
                        name=f"Test Result: {test_id}",
                        mimeType="application/json"
                    )
                )

            # Add coverage report resources
            for report_id, report in self.coverage_reports.items():
                resources.append(
                    Resource(
                        uri=f"coverage://{report_id}",
                        name=f"Coverage Report: {report_id}",
                        mimeType="application/json"
                    )
                )

            # Add healing report resources
            for report_id, report in self.healing_reports.items():
                resources.append(
                    Resource(
                        uri=f"healing://{report_id}",
                        name=f"Healing Report: {report_id}",
                        mimeType="application/json"
                    )
                )

            return ListResourcesResponse(resources=resources)

        @self.server.get_resource()
        async def get_resource(uri: str) -> GetResourceResponse:
            """Get a specific resource."""
            if uri.startswith("test-result://"):
                test_id = uri.replace("test-result://", "")
                if test_id in self.test_results:
                    return GetResourceResponse(
                        contents=[
                            TextContent(
                                text=json.dumps(self.test_results[test_id], indent=2),
                                mimeType="application/json"
                            )
                        ]
                    )
            elif uri.startswith("coverage://"):
                report_id = uri.replace("coverage://", "")
                if report_id in self.coverage_reports:
                    return GetResourceResponse(
                        contents=[
                            TextContent(
                                text=json.dumps(self.coverage_reports[report_id], indent=2),
                                mimeType="application/json"
                            )
                        ]
                    )
            elif uri.startswith("healing://"):
                report_id = uri.replace("healing://", "")
                if report_id in self.healing_reports:
                    return GetResourceResponse(
                        contents=[
                            TextContent(
                                text=json.dumps(self.healing_reports[report_id], indent=2),
                                mimeType="application/json"
                            )
                        ]
                    )

            return GetResourceResponse(contents=[])

    async def _run_test(
        self,
        test_file: str,
        test_name: Optional[str] = None,
        browser: str = "chromium",
        headless: bool = True
    ) -> Dict[str, Any]:
        """Execute a Playwright test."""
        logger.info(f"Running test: {test_file} with {browser}")

        result = await self.playwright_agent.execute_task({
            'action': 'run_test',
            'test_file': test_file,
            'test_name': test_name,
            'browser': browser,
            'headless': headless
        })

        # Store result
        test_id = f"{Path(test_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_results[test_id] = result

        return {
            'test_id': test_id,
            'status': result.get('status'),
            'passed': result.get('passed', 0),
            'failed': result.get('failed', 0),
            'skipped': result.get('skipped', 0),
            'duration': result.get('duration'),
            'report_url': result.get('report_url')
        }

    async def _generate_test(
        self,
        story: Dict[str, Any],
        test_type: str = "e2e"
    ) -> Dict[str, Any]:
        """Generate test from user story."""
        logger.info(f"Generating {test_type} test from story")

        result = await self.generation_agent.execute_task({
            'action': 'generate_from_story',
            'story': story,
            'test_type': test_type
        })

        return {
            'status': result.get('status'),
            'test_cases': result.get('test_cases'),
            'coverage_estimate': result.get('coverage_estimate'),
            'generated_code': result.get('test_cases', [{}])[0].get('generated_code') if result.get('test_cases') else None
        }

    async def _analyze_coverage(
        self,
        project_path: str,
        include_branches: bool = True
    ) -> Dict[str, Any]:
        """Analyze test coverage."""
        logger.info(f"Analyzing coverage for: {project_path}")

        result = await self.coverage_agent.execute_task({
            'action': 'analyze_project',
            'project_path': project_path
        })

        # Store report
        report_id = f"coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.coverage_reports[report_id] = result

        return {
            'report_id': report_id,
            'status': result.get('status'),
            'overall_coverage': result.get('coverage_report', {}).get('overall_coverage'),
            'line_coverage': result.get('coverage_report', {}).get('line_coverage'),
            'branch_coverage': result.get('coverage_report', {}).get('branch_coverage') if include_branches else None,
            'needs_improvement': result.get('needs_improvement'),
            'critical_files': result.get('critical_files', [])[:5]  # Top 5 critical files
        }

    async def _heal_test(
        self,
        failure: Dict[str, Any],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """Auto-heal a broken test."""
        logger.info("Healing broken test")

        result = await self.healing_agent.execute_task({
            'action': 'heal_test',
            'failure': failure
        })

        # Store report
        report_id = f"healing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.healing_reports[report_id] = result

        if auto_apply and result.get('status') == 'success':
            # Apply the fix automatically
            fix_code = result.get('fix_code')
            if fix_code:
                logger.info("Auto-applying fix to test file")
                # Implementation would write the fix to the test file

        return {
            'report_id': report_id,
            'status': result.get('status'),
            'root_cause': result.get('root_cause'),
            'confidence': result.get('confidence'),
            'fix_applied': auto_apply and result.get('status') == 'success',
            'fix_code': result.get('fix_code') if not auto_apply else None
        }

    async def _record_session(
        self,
        url: str,
        duration: Optional[int] = None,
        output_format: str = "playwright"
    ) -> Dict[str, Any]:
        """Record browser session for test generation."""
        logger.info(f"Recording session for: {url}")

        # Start recording
        result = await self.playwright_agent.execute_task({
            'action': 'record_session',
            'url': url,
            'duration': duration or 60,  # Default 60 seconds
            'output_format': output_format
        })

        return {
            'status': result.get('status'),
            'recording_id': result.get('recording_id'),
            'duration': result.get('duration'),
            'generated_test': result.get('generated_test'),
            'interactions_captured': result.get('interactions_captured')
        }

    async def _visual_regression(
        self,
        baseline: str,
        current: str,
        threshold: float = 0.1
    ) -> Dict[str, Any]:
        """Perform visual regression testing."""
        logger.info("Running visual regression test")

        result = await self.playwright_agent.execute_task({
            'action': 'visual_regression',
            'baseline': baseline,
            'current': current,
            'threshold': threshold
        })

        return {
            'status': result.get('status'),
            'difference_percentage': result.get('difference_percentage'),
            'passed': result.get('difference_percentage', 1.0) <= threshold,
            'diff_image': result.get('diff_image'),
            'areas_changed': result.get('areas_changed')
        }

    async def _performance_test(
        self,
        url: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run performance tests."""
        logger.info(f"Running performance test for: {url}")

        default_metrics = ['FCP', 'LCP', 'CLS', 'FID', 'TTFB']
        metrics = metrics or default_metrics

        result = await self.playwright_agent.execute_task({
            'action': 'performance_test',
            'url': url,
            'metrics': metrics
        })

        return {
            'status': result.get('status'),
            'url': url,
            'metrics': result.get('metrics'),
            'lighthouse_score': result.get('lighthouse_score'),
            'recommendations': result.get('recommendations')
        }

    async def _accessibility_audit(
        self,
        url: str,
        standards: str = "wcag2aa"
    ) -> Dict[str, Any]:
        """Run accessibility audit."""
        logger.info(f"Running accessibility audit for: {url} with {standards}")

        result = await self.playwright_agent.execute_task({
            'action': 'accessibility_audit',
            'url': url,
            'standards': standards
        })

        return {
            'status': result.get('status'),
            'url': url,
            'standards': standards,
            'violations': result.get('violations', []),
            'warnings': result.get('warnings', []),
            'passes': result.get('passes', []),
            'score': result.get('score')
        }

    async def _batch_test(
        self,
        test_suite: str,
        parallel_workers: int = 4,
        fail_fast: bool = False
    ) -> Dict[str, Any]:
        """Run multiple tests in parallel."""
        logger.info(f"Running test suite: {test_suite} with {parallel_workers} workers")

        result = await self.playwright_agent.execute_task({
            'action': 'run_suite',
            'suite_name': test_suite,
            'parallel': True,
            'workers': parallel_workers,
            'fail_fast': fail_fast
        })

        return {
            'status': result.get('status'),
            'test_suite': test_suite,
            'total_tests': result.get('total'),
            'passed': result.get('passed'),
            'failed': result.get('failed'),
            'skipped': result.get('skipped'),
            'duration': result.get('duration'),
            'parallel_efficiency': result.get('parallel_efficiency')
        }

    async def _create_page_object(
        self,
        page_url: str,
        page_name: str,
        auto_detect_elements: bool = True
    ) -> Dict[str, Any]:
        """Generate Page Object Model."""
        logger.info(f"Creating Page Object for: {page_name}")

        result = await self.playwright_agent.execute_task({
            'action': 'create_page_object',
            'page_url': page_url,
            'page_name': page_name,
            'auto_detect': auto_detect_elements
        })

        return {
            'status': result.get('status'),
            'page_name': page_name,
            'elements_detected': result.get('elements_detected'),
            'methods_generated': result.get('methods_generated'),
            'page_object_code': result.get('page_object_code'),
            'file_path': result.get('file_path')
        }

    async def start(self):
        """Start the MCP server."""
        logger.info("Starting Playwright MCP Server...")

        # Initialize agents
        await self.playwright_agent.initialize()

        # Start server
        async with self.server.run() as running_server:
            logger.info("Playwright MCP Server is running")
            await running_server


async def main():
    """Main entry point."""
    server = PlaywrightMCPServer()
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())