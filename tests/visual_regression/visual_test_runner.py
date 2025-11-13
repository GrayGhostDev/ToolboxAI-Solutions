#!/usr/bin/env python3
"""Visual Regression Testing System for ToolBoxAI.

This module implements comprehensive visual regression testing using Playwright
to catch UI changes and ensure consistent visual appearance across updates.
"""

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageChops, ImageDraw
from playwright.async_api import Browser, Page, async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


class VisualRegressionTester:
    """Visual regression testing system."""

    def __init__(
        self,
        base_url: str = "http://localhost:5179",
        baseline_dir: str = "tests/visual_regression/baselines",
        results_dir: str = "tests/visual_regression/results",
        threshold: float = 0.1,
    ):
        self.base_url = base_url
        self.baseline_dir = Path(baseline_dir)
        self.results_dir = Path(results_dir)
        self.threshold = threshold  # Difference threshold (0-1)

        # Create directories
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        (self.results_dir / "diffs").mkdir(exist_ok=True)
        (self.results_dir / "failures").mkdir(exist_ok=True)

        # Test results
        self.results: list[dict[str, Any]] = []

    async def capture_screenshot(
        self,
        page: Page,
        name: str,
        selector: str | None = None,
        full_page: bool = True,
    ) -> bytes:
        """Capture a screenshot of the page or element."""
        screenshot_options = {
            "full_page": full_page,
            "animations": "disabled",
        }

        if selector:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                screenshot = await element.screenshot(**screenshot_options)
            else:
                raise ValueError(f"Element {selector} not found")
        else:
            screenshot = await page.screenshot(**screenshot_options)

        return screenshot

    def compare_images(
        self, baseline: bytes, current: bytes, name: str
    ) -> tuple[bool, float, bytes | None]:
        """Compare two images and return difference metrics."""
        # Convert bytes to PIL Images
        baseline_img = Image.open(Path(baseline) if isinstance(baseline, (str, Path)) else baseline)
        current_img = Image.open(Path(current) if isinstance(current, (str, Path)) else current)

        # Ensure images are the same size
        if baseline_img.size != current_img.size:
            console.print(
                f"[yellow]Warning: Image sizes differ for {name}. "
                f"Baseline: {baseline_img.size}, Current: {current_img.size}[/yellow]"
            )
            # Resize current to match baseline
            current_img = current_img.resize(baseline_img.size, Image.LANCZOS)

        # Convert to RGB if necessary
        if baseline_img.mode != "RGB":
            baseline_img = baseline_img.convert("RGB")
        if current_img.mode != "RGB":
            current_img = current_img.convert("RGB")

        # Calculate difference
        diff = ImageChops.difference(baseline_img, current_img)

        # Convert to numpy arrays for detailed analysis
        baseline_array = np.array(baseline_img)
        current_array = np.array(current_img)
        diff_array = np.array(diff)

        # Calculate difference percentage
        total_pixels = baseline_array.shape[0] * baseline_array.shape[1]
        diff_pixels = np.sum(diff_array > 10) / 3  # Threshold for significant difference
        diff_percentage = diff_pixels / total_pixels

        # Create visual diff image if there are differences
        diff_image = None
        if diff_percentage > 0.001:  # More than 0.1% difference
            # Create a highlighted diff image
            diff_highlighted = Image.new("RGB", baseline_img.size)
            draw = ImageDraw.Draw(diff_highlighted)

            # Overlay images with differences highlighted
            for x in range(0, baseline_img.width, 10):
                for y in range(0, baseline_img.height, 10):
                    # Sample region
                    region_baseline = baseline_array[y : y + 10, x : x + 10]
                    region_current = current_array[y : y + 10, x : x + 10]

                    # Check if region has differences
                    if np.mean(np.abs(region_baseline - region_current)) > 10:
                        # Highlight difference in red
                        draw.rectangle([x, y, x + 10, y + 10], fill=(255, 0, 0, 128))

            # Blend with original for context
            diff_image = Image.blend(current_img, diff_highlighted, 0.5)

            # Save diff image
            diff_path = self.results_dir / "diffs" / f"{name}_diff.png"
            diff_image.save(diff_path)

        # Determine if images match within threshold
        matches = diff_percentage <= self.threshold

        return matches, diff_percentage, diff_path if diff_image else None

    async def test_page(
        self,
        browser: Browser,
        page_config: dict[str, Any],
        update_baseline: bool = False,
    ) -> dict[str, Any]:
        """Test a single page for visual regression."""
        page_name = page_config["name"]
        url = page_config.get("url", "/")
        full_url = f"{self.base_url}{url}"

        console.print(f"Testing page: [cyan]{page_name}[/cyan] ({full_url})")

        # Create browser context with viewport
        context = await browser.new_context(
            viewport=page_config.get("viewport", {"width": 1920, "height": 1080}),
            device_scale_factor=page_config.get("device_scale_factor", 1),
        )

        page = await context.new_page()

        try:
            # Navigate to page
            await page.goto(full_url, wait_until="networkidle")

            # Perform any setup actions (login, etc.)
            if "setup" in page_config:
                await self._perform_setup(page, page_config["setup"])

            # Wait for page to stabilize
            await page.wait_for_timeout(page_config.get("wait", 1000))

            # Capture screenshots for each test case
            test_cases = page_config.get("tests", [{"name": "full", "selector": None}])
            results = []

            for test_case in test_cases:
                test_name = f"{page_name}_{test_case['name']}"
                selector = test_case.get("selector")

                # Capture current screenshot
                current_screenshot = await self.capture_screenshot(
                    page,
                    test_name,
                    selector=selector,
                    full_page=test_case.get("full_page", True),
                )

                # Save current screenshot
                current_path = self.results_dir / f"{test_name}_current.png"
                with open(current_path, "wb") as f:
                    f.write(current_screenshot)

                baseline_path = self.baseline_dir / f"{test_name}.png"

                if update_baseline or not baseline_path.exists():
                    # Create/update baseline
                    with open(baseline_path, "wb") as f:
                        f.write(current_screenshot)
                    console.print(
                        f"  ✓ {'Updated' if baseline_path.exists() else 'Created'} "
                        f"baseline for [green]{test_name}[/green]"
                    )
                    results.append(
                        {
                            "test": test_name,
                            "status": "baseline_updated",
                            "diff_percentage": 0,
                        }
                    )
                else:
                    # Compare with baseline
                    with open(baseline_path, "rb") as f:
                        baseline_screenshot = f.read()

                    matches, diff_percentage, diff_path = self.compare_images(
                        baseline_path, current_path, test_name
                    )

                    if matches:
                        console.print(
                            f"  ✓ [green]{test_name}[/green] matches baseline "
                            f"(diff: {diff_percentage:.2%})"
                        )
                        status = "passed"
                    else:
                        console.print(
                            f"  ✗ [red]{test_name}[/red] differs from baseline "
                            f"(diff: {diff_percentage:.2%})"
                        )
                        status = "failed"

                        # Save failure for review
                        failure_dir = self.results_dir / "failures" / test_name
                        failure_dir.mkdir(parents=True, exist_ok=True)

                        # Copy files for easy comparison
                        (failure_dir / "baseline.png").write_bytes(baseline_screenshot)
                        (failure_dir / "current.png").write_bytes(current_screenshot)
                        if diff_path:
                            (failure_dir / "diff.png").write_bytes(diff_path.read_bytes())

                    results.append(
                        {
                            "test": test_name,
                            "status": status,
                            "diff_percentage": diff_percentage,
                            "diff_path": str(diff_path) if diff_path else None,
                        }
                    )

            return {
                "page": page_name,
                "url": full_url,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }

        finally:
            await context.close()

    async def _perform_setup(self, page: Page, setup: list[dict[str, Any]]):
        """Perform setup actions on the page."""
        for action in setup:
            action_type = action["type"]

            if action_type == "fill":
                await page.fill(action["selector"], action["value"])
            elif action_type == "click":
                await page.click(action["selector"])
            elif action_type == "wait":
                await page.wait_for_timeout(action["duration"])
            elif action_type == "wait_for_selector":
                await page.wait_for_selector(
                    action["selector"], timeout=action.get("timeout", 5000)
                )
            elif action_type == "eval":
                await page.evaluate(action["script"])

    async def run_tests(
        self,
        config_file: str = "tests/visual_regression/config.json",
        update_baseline: bool = False,
        filter_pages: list[str] | None = None,
    ):
        """Run all visual regression tests."""
        # Load test configuration
        with open(config_file) as f:
            config = json.load(f)

        self.threshold = config.get("threshold", self.threshold)
        pages = config["pages"]

        # Filter pages if specified
        if filter_pages:
            pages = [p for p in pages if p["name"] in filter_pages]

        console.print(
            Panel.fit(
                f"[bold cyan]Visual Regression Testing[/bold cyan]\n"
                f"Testing {len(pages)} pages\n"
                f"Threshold: {self.threshold:.1%}\n"
                f"Mode: {'Update Baseline' if update_baseline else 'Test'}",
                title="Test Configuration",
            )
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Running tests...", total=len(pages))

                for page_config in pages:
                    result = await self.test_page(browser, page_config, update_baseline)
                    self.results.append(result)
                    progress.advance(task)

            await browser.close()

        # Generate report
        self._generate_report()

    def _generate_report(self):
        """Generate test report."""
        # Calculate summary statistics
        total_tests = sum(len(r["results"]) for r in self.results)
        passed = sum(1 for r in self.results for t in r["results"] if t["status"] == "passed")
        failed = sum(1 for r in self.results for t in r["results"] if t["status"] == "failed")
        updated = sum(
            1 for r in self.results for t in r["results"] if t["status"] == "baseline_updated"
        )

        # Create summary table
        table = Table(title="Visual Regression Test Results")
        table.add_column("Page", style="cyan")
        table.add_column("Test", style="white")
        table.add_column("Status", style="white")
        table.add_column("Diff %", justify="right")

        for page_result in self.results:
            for test_result in page_result["results"]:
                status_style = {
                    "passed": "[green]✓ Passed[/green]",
                    "failed": "[red]✗ Failed[/red]",
                    "baseline_updated": "[yellow]↻ Updated[/yellow]",
                }.get(test_result["status"], test_result["status"])

                diff_str = (
                    f"{test_result['diff_percentage']:.2%}"
                    if test_result["diff_percentage"] > 0
                    else "-"
                )

                table.add_row(
                    page_result["page"],
                    test_result["test"],
                    status_style,
                    diff_str,
                )

        console.print("\n")
        console.print(table)

        # Print summary
        console.print("\n")
        console.print(
            Panel.fit(
                (
                    f"[bold]Summary[/bold]\n\n"
                    f"Total Tests: {total_tests}\n"
                    f"[green]Passed: {passed}[/green]\n"
                    f"[red]Failed: {failed}[/red]\n"
                    f"[yellow]Updated: {updated}[/yellow]\n\n"
                    f"Pass Rate: {(passed / total_tests * 100):.1f}%"
                    if total_tests > 0
                    else "N/A"
                ),
                title="Test Summary",
            )
        )

        # Save JSON report
        report_path = self.results_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_path, "w") as f:
            json.dump(
                {
                    "summary": {
                        "total": total_tests,
                        "passed": passed,
                        "failed": failed,
                        "updated": updated,
                        "pass_rate": passed / total_tests if total_tests > 0 else 0,
                    },
                    "threshold": self.threshold,
                    "timestamp": datetime.now().isoformat(),
                    "results": self.results,
                },
                f,
                indent=2,
            )

        console.print(f"\n[dim]Report saved to: {report_path}[/dim]")

        # Generate HTML report if there are failures
        if failed > 0:
            self._generate_html_report()

    def _generate_html_report(self):
        """Generate HTML report with visual comparisons."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .test-case {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .test-case.failed {
            border-left: 4px solid #dc3545;
        }
        .test-case.passed {
            border-left: 4px solid #28a745;
        }
        .image-comparison {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .image-container {
            text-align: center;
        }
        .image-container img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .image-label {
            font-weight: bold;
            margin-top: 10px;
            color: #666;
        }
        .diff-percentage {
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
            margin: 10px 0;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        .status.passed {
            background: #d4edda;
            color: #155724;
        }
        .status.failed {
            background: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Visual Regression Test Report</h1>
        """

        # Add summary
        total = sum(len(r["results"]) for r in self.results)
        passed = sum(1 for r in self.results for t in r["results"] if t["status"] == "passed")
        failed = sum(1 for r in self.results for t in r["results"] if t["status"] == "failed")

        html += f"""
        <div class="summary">
            <h2>Summary</h2>
            <p>Generated: {datetime.now():%Y-%m-%d %H:%M:%S}</p>
            <p>Total Tests: {total}</p>
            <p>Passed: {passed} ({passed/total*100:.1f}%)</p>
            <p>Failed: {failed} ({failed/total*100:.1f}%)</p>
            <p>Threshold: {self.threshold:.1%}</p>
        </div>
        """

        # Add failed test details
        for page_result in self.results:
            for test_result in page_result["results"]:
                if test_result["status"] == "failed":
                    test_name = test_result["test"]
                    diff_percentage = test_result["diff_percentage"]

                    html += f"""
                    <div class="test-case failed">
                        <h3>{test_name}</h3>
                        <span class="status failed">FAILED</span>
                        <div class="diff-percentage">Difference: {diff_percentage:.2%}</div>

                        <div class="image-comparison">
                            <div class="image-container">
                                <img src="../failures/{test_name}/baseline.png" alt="Baseline">
                                <div class="image-label">Baseline</div>
                            </div>
                            <div class="image-container">
                                <img src="../failures/{test_name}/current.png" alt="Current">
                                <div class="image-label">Current</div>
                            </div>
                            <div class="image-container">
                                <img src="../failures/{test_name}/diff.png" alt="Difference">
                                <div class="image-label">Difference</div>
                            </div>
                        </div>
                    </div>
                    """

        html += """
    </div>
</body>
</html>
        """

        # Save HTML report
        report_path = self.results_dir / "visual_regression_report.html"
        with open(report_path, "w") as f:
            f.write(html)

        console.print(f"[dim]HTML report saved to: {report_path}[/dim]")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Visual Regression Testing")
    parser.add_argument(
        "--config",
        default="tests/visual_regression/config.json",
        help="Path to test configuration file",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline images",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="Difference threshold (0-1)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:5179",
        help="Base URL for testing",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        help="Specific pages to test",
    )

    args = parser.parse_args()

    tester = VisualRegressionTester(
        base_url=args.base_url,
        threshold=args.threshold,
    )

    asyncio.run(
        tester.run_tests(
            config_file=args.config,
            update_baseline=args.update_baseline,
            filter_pages=args.pages,
        )
    )


if __name__ == "__main__":
    main()
