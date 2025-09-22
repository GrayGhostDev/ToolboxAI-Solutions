#!/usr/bin/env python3
"""Accessibility Testing System for ToolBoxAI.

This module implements comprehensive accessibility testing using axe-core
and Playwright to ensure WCAG 2.1 AA compliance.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page, Browser
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.markdown import Markdown
import argparse

console = Console()


@dataclass
class AccessibilityViolation:
    """Represents an accessibility violation."""

    id: str
    impact: str  # critical, serious, moderate, minor
    description: str
    help: str
    help_url: str
    tags: List[str]
    nodes: List[Dict[str, Any]]
    page_url: str
    timestamp: str


@dataclass
class A11yTestResult:
    """Result of accessibility testing."""

    page_name: str
    url: str
    violations: List[AccessibilityViolation]
    passes: int
    incomplete: int
    inapplicable: int
    tested_at: str
    wcag_level: str = "AA"
    compliance_score: float = 0.0


class AccessibilityTester:
    """Comprehensive accessibility testing system."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.test_results: List[A11yTestResult] = []
        self.axe_script = self._load_axe_script()

    def _default_config(self) -> Dict:
        """Default accessibility testing configuration."""
        return {
            "wcag_level": "AA",  # A, AA, or AAA
            "rules": {
                "enabled": [
                    "area-alt",
                    "aria-allowed-attr",
                    "aria-required-attr",
                    "aria-required-children",
                    "aria-required-parent",
                    "aria-roles",
                    "aria-valid-attr",
                    "aria-valid-attr-value",
                    "audio-caption",
                    "button-name",
                    "color-contrast",
                    "document-title",
                    "duplicate-id",
                    "html-has-lang",
                    "html-lang-valid",
                    "image-alt",
                    "input-image-alt",
                    "label",
                    "link-name",
                    "list",
                    "listitem",
                    "meta-viewport",
                    "object-alt",
                    "role-img-alt",
                    "scrollable-region-focusable",
                    "td-headers-attr",
                    "th-has-data-cells",
                    "valid-lang",
                    "video-caption",
                    "video-description",
                ],
                "disabled": [],
            },
            "viewport": {
                "width": 1920,
                "height": 1080,
            },
            "test_states": {
                "default": True,
                "focus": True,
                "hover": True,
                "active": True,
                "dark_mode": True,
                "mobile": True,
                "keyboard_only": True,
                "screen_reader": True,
            },
            "color_blindness_tests": [
                "protanopia",  # Red-blind
                "deuteranopia",  # Green-blind
                "tritanopia",  # Blue-blind
                "achromatopsia",  # Complete color blindness
            ],
            "thresholds": {
                "critical": 0,  # No critical violations allowed
                "serious": 3,  # Max 3 serious violations
                "moderate": 10,  # Max 10 moderate violations
                "minor": 20,  # Max 20 minor violations
            },
        }

    def _load_axe_script(self) -> str:
        """Load axe-core script for injection."""
        # In production, load from node_modules or CDN
        # For now, return CDN URL
        return "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js"

    async def test_page(
        self,
        page: Page,
        page_name: str,
        url: str
    ) -> A11yTestResult:
        """Test a single page for accessibility."""
        console.print(f"Testing accessibility for: [cyan]{page_name}[/cyan]")

        # Navigate to page
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(2000)  # Wait for dynamic content

        # Inject axe-core
        await page.add_script_tag(url=self.axe_script)
        await page.wait_for_timeout(1000)  # Wait for script to load

        # Configure axe
        await page.evaluate("""
            axe.configure({
                rules: arguments[0].rules.enabled.map(id => ({ id, enabled: true }))
                    .concat(arguments[0].rules.disabled.map(id => ({ id, enabled: false })))
            });
        """, self.config)

        # Run accessibility tests
        results = await page.evaluate("""
            async () => {
                const results = await axe.run();
                return {
                    violations: results.violations,
                    passes: results.passes.length,
                    incomplete: results.incomplete.length,
                    inapplicable: results.inapplicable.length,
                };
            }
        """)

        # Parse violations
        violations = []
        for violation in results["violations"]:
            violations.append(AccessibilityViolation(
                id=violation["id"],
                impact=violation["impact"],
                description=violation["description"],
                help=violation["help"],
                help_url=violation["helpUrl"],
                tags=violation["tags"],
                nodes=violation["nodes"],
                page_url=url,
                timestamp=datetime.now().isoformat(),
            ))

        # Calculate compliance score
        score = self._calculate_compliance_score(violations, results["passes"])

        result = A11yTestResult(
            page_name=page_name,
            url=url,
            violations=violations,
            passes=results["passes"],
            incomplete=results["incomplete"],
            inapplicable=results["inapplicable"],
            tested_at=datetime.now().isoformat(),
            wcag_level=self.config["wcag_level"],
            compliance_score=score,
        )

        return result

    def _calculate_compliance_score(
        self,
        violations: List[AccessibilityViolation],
        passes: int
    ) -> float:
        """Calculate accessibility compliance score."""
        # Weight violations by impact
        weights = {
            "critical": 10,
            "serious": 5,
            "moderate": 2,
            "minor": 1,
        }

        total_weight = 0
        for violation in violations:
            total_weight += weights.get(violation.impact, 1) * len(violation.nodes)

        # Calculate score (0-100)
        total_checks = passes + len(violations)
        if total_checks == 0:
            return 100.0

        # Penalize based on weighted violations
        penalty = min(total_weight * 2, 100)  # Cap at 100
        score = max(0, 100 - penalty)

        return score

    async def test_keyboard_navigation(self, page: Page) -> Dict[str, Any]:
        """Test keyboard navigation accessibility."""
        results = {
            "focusable_elements": 0,
            "tab_order_valid": True,
            "skip_links": False,
            "keyboard_traps": [],
            "focus_visible": True,
        }

        # Check for skip links
        skip_links = await page.query_selector_all('a[href^="#"]:first-child')
        results["skip_links"] = len(skip_links) > 0

        # Get all focusable elements
        focusable = await page.evaluate("""
            () => {
                const selector = 'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])';
                const elements = document.querySelectorAll(selector);
                return Array.from(elements).map(el => ({
                    tag: el.tagName,
                    tabIndex: el.tabIndex,
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect(),
                }));
            }
        """)

        results["focusable_elements"] = len(focusable)

        # Test tab order
        previous_y = 0
        for element in focusable:
            if element["visible"] and element["tabIndex"] >= 0:
                # Check if tab order follows visual flow (top to bottom, left to right)
                if element["rect"]["y"] < previous_y - 100:  # Allow some tolerance
                    results["tab_order_valid"] = False
                previous_y = element["rect"]["y"]

        # Test for keyboard traps
        trap_candidates = await page.query_selector_all('div[tabindex="0"], span[tabindex="0"]')
        for element in trap_candidates:
            # Check if element has proper keyboard interaction
            has_key_handler = await element.evaluate("""
                el => el.onkeydown !== null || el.onkeyup !== null || el.onkeypress !== null
            """)
            if not has_key_handler:
                results["keyboard_traps"].append(await element.evaluate("el => el.outerHTML"))

        # Test focus visibility
        await page.evaluate("""
            () => {
                // Trigger focus on first focusable element
                const firstFocusable = document.querySelector('a, button, input, textarea, select');
                if (firstFocusable) firstFocusable.focus();
            }
        """)

        focus_styles = await page.evaluate("""
            () => {
                const focused = document.activeElement;
                if (!focused) return null;
                const styles = window.getComputedStyle(focused);
                return {
                    outline: styles.outline,
                    outlineWidth: styles.outlineWidth,
                    boxShadow: styles.boxShadow,
                    border: styles.border,
                };
            }
        """)

        # Check if focus is visually indicated
        if focus_styles:
            has_focus_indicator = (
                (focus_styles["outline"] != "none" and focus_styles["outlineWidth"] != "0px") or
                "box-shadow" in focus_styles["boxShadow"] or
                focus_styles["border"] != "none"
            )
            results["focus_visible"] = has_focus_indicator

        return results

    async def test_screen_reader(self, page: Page) -> Dict[str, Any]:
        """Test screen reader compatibility."""
        results = {
            "aria_landmarks": 0,
            "aria_labels": 0,
            "headings_structure": True,
            "images_with_alt": 0,
            "forms_labeled": True,
            "tables_accessible": True,
            "live_regions": 0,
        }

        # Check ARIA landmarks
        landmarks = await page.query_selector_all('[role="main"], [role="navigation"], [role="banner"], [role="contentinfo"], [role="complementary"]')
        results["aria_landmarks"] = len(landmarks)

        # Check ARIA labels
        labeled = await page.query_selector_all('[aria-label], [aria-labelledby], [aria-describedby]')
        results["aria_labels"] = len(labeled)

        # Check heading structure
        headings = await page.evaluate("""
            () => {
                const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
                return Array.from(headings).map(h => ({
                    level: parseInt(h.tagName[1]),
                    text: h.textContent,
                }));
            }
        """)

        # Validate heading hierarchy
        previous_level = 0
        for heading in headings:
            if heading["level"] - previous_level > 1:
                results["headings_structure"] = False
                break
            previous_level = heading["level"]

        # Check images
        images = await page.evaluate("""
            () => {
                const imgs = document.querySelectorAll('img');
                return {
                    total: imgs.length,
                    with_alt: Array.from(imgs).filter(img => img.alt).length,
                };
            }
        """)
        results["images_with_alt"] = images["with_alt"] if images["total"] > 0 else 100

        # Check form labels
        form_inputs = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, textarea, select');
                const labeled = Array.from(inputs).filter(input => {
                    const id = input.id;
                    const label = id ? document.querySelector(`label[for="${id}"]`) : null;
                    return label !== null || input.getAttribute('aria-label') !== null;
                });
                return {
                    total: inputs.length,
                    labeled: labeled.length,
                };
            }
        """)

        if form_inputs["total"] > 0:
            results["forms_labeled"] = form_inputs["labeled"] == form_inputs["total"]

        # Check tables
        tables = await page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                return Array.from(tables).every(table => {
                    const headers = table.querySelectorAll('th');
                    const caption = table.querySelector('caption');
                    return headers.length > 0 || caption !== null;
                });
            }
        """)
        results["tables_accessible"] = tables

        # Check live regions
        live_regions = await page.query_selector_all('[aria-live], [role="alert"], [role="status"]')
        results["live_regions"] = len(live_regions)

        return results

    async def test_color_contrast(self, page: Page) -> Dict[str, Any]:
        """Test color contrast for WCAG compliance."""
        results = {
            "issues": [],
            "passed": 0,
            "failed": 0,
        }

        # Inject color contrast checking script
        contrast_results = await page.evaluate("""
            () => {
                function getLuminance(r, g, b) {
                    const [rs, gs, bs] = [r, g, b].map(c => {
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    });
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }

                function getContrastRatio(l1, l2) {
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                }

                function parseColor(color) {
                    const match = color.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                    if (match) {
                        return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
                    }
                    return null;
                }

                const elements = document.querySelectorAll('*');
                const results = [];

                elements.forEach(el => {
                    const styles = window.getComputedStyle(el);
                    const bgColor = parseColor(styles.backgroundColor);
                    const textColor = parseColor(styles.color);

                    if (bgColor && textColor && el.textContent.trim()) {
                        const bgLuminance = getLuminance(...bgColor);
                        const textLuminance = getLuminance(...textColor);
                        const ratio = getContrastRatio(bgLuminance, textLuminance);

                        const fontSize = parseFloat(styles.fontSize);
                        const isBold = parseInt(styles.fontWeight) >= 700;

                        // WCAG AA requirements
                        let requiredRatio = 4.5;  // Normal text
                        if (fontSize >= 18 || (fontSize >= 14 && isBold)) {
                            requiredRatio = 3;  // Large text
                        }

                        results.push({
                            element: el.tagName,
                            ratio: ratio.toFixed(2),
                            required: requiredRatio,
                            passed: ratio >= requiredRatio,
                            text: el.textContent.substring(0, 50),
                        });
                    }
                });

                return results;
            }
        """)

        for item in contrast_results:
            if item["passed"]:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["issues"].append({
                    "element": item["element"],
                    "ratio": item["ratio"],
                    "required": item["required"],
                    "text": item["text"],
                })

        return results

    async def test_responsive_accessibility(self, page: Page) -> Dict[str, Any]:
        """Test accessibility across different viewport sizes."""
        results = {
            "mobile": {},
            "tablet": {},
            "desktop": {},
        }

        viewports = {
            "mobile": {"width": 375, "height": 812},
            "tablet": {"width": 768, "height": 1024},
            "desktop": {"width": 1920, "height": 1080},
        }

        for device, viewport in viewports.items():
            await page.set_viewport_size(viewport)
            await page.wait_for_timeout(1000)

            # Check touch target sizes for mobile/tablet
            if device in ["mobile", "tablet"]:
                touch_targets = await page.evaluate("""
                    () => {
                        const clickable = document.querySelectorAll('a, button, [onclick]');
                        return Array.from(clickable).map(el => {
                            const rect = el.getBoundingClientRect();
                            return {
                                width: rect.width,
                                height: rect.height,
                                adequate: rect.width >= 44 && rect.height >= 44,  // 44px minimum
                            };
                        });
                    }
                """)

                adequate = sum(1 for t in touch_targets if t["adequate"])
                results[device]["touch_targets"] = {
                    "total": len(touch_targets),
                    "adequate": adequate,
                    "percentage": (adequate / len(touch_targets) * 100) if touch_targets else 100,
                }

            # Check zoom capability
            zoom_test = await page.evaluate("""
                () => {
                    const viewport = document.querySelector('meta[name="viewport"]');
                    if (!viewport) return { zoomable: true };

                    const content = viewport.getAttribute('content');
                    const hasMaxScale = content.includes('maximum-scale=1');
                    const hasUserScalable = content.includes('user-scalable=no');

                    return {
                        zoomable: !hasMaxScale && !hasUserScalable,
                        viewport_tag: content,
                    };
                }
            """)

            results[device]["zoom_capable"] = zoom_test["zoomable"]

            # Check text reflow at 200% zoom
            await page.evaluate("document.body.style.zoom = '200%'")
            horizontal_scroll = await page.evaluate("""
                () => document.documentElement.scrollWidth > window.innerWidth
            """)
            results[device]["text_reflows"] = not horizontal_scroll
            await page.evaluate("document.body.style.zoom = '100%'")

        return results

    async def run_comprehensive_test(self, base_url: str, pages: List[Dict[str, str]]):
        """Run comprehensive accessibility testing on multiple pages."""
        console.print(
            Panel.fit(
                "[bold cyan]Accessibility Testing[/bold cyan]\n"
                f"WCAG Level: {self.config['wcag_level']}\n"
                f"Pages to test: {len(pages)}",
                title="A11y Testing"
            )
        )

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport=self.config["viewport"],
                device_scale_factor=2,
            )

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                console=console,
            ) as progress:

                task = progress.add_task("Testing pages...", total=len(pages))

                for page_info in pages:
                    page = await context.new_page()

                    try:
                        # Basic accessibility test
                        result = await self.test_page(
                            page,
                            page_info["name"],
                            base_url + page_info["path"]
                        )
                        self.test_results.append(result)

                        # Additional tests
                        if self.config["test_states"]["keyboard_only"]:
                            keyboard_results = await self.test_keyboard_navigation(page)
                            result.keyboard_navigation = keyboard_results

                        if self.config["test_states"]["screen_reader"]:
                            sr_results = await self.test_screen_reader(page)
                            result.screen_reader = sr_results

                        # Color contrast test
                        contrast_results = await self.test_color_contrast(page)
                        result.color_contrast = contrast_results

                        # Responsive accessibility
                        responsive_results = await self.test_responsive_accessibility(page)
                        result.responsive = responsive_results

                    finally:
                        await page.close()
                        progress.advance(task)

            await browser.close()

        # Generate report
        self._generate_report()

    def _generate_report(self):
        """Generate accessibility testing report."""
        # Summary table
        table = Table(title="Accessibility Test Results")
        table.add_column("Page", style="cyan")
        table.add_column("Violations", justify="right")
        table.add_column("Critical", justify="right", style="red")
        table.add_column("Serious", justify="right", style="yellow")
        table.add_column("Score", justify="right")
        table.add_column("Status", justify="center")

        for result in self.test_results:
            critical = sum(1 for v in result.violations if v.impact == "critical")
            serious = sum(1 for v in result.violations if v.impact == "serious")

            # Determine status
            if critical > 0:
                status = "[red]✗ Failed[/red]"
            elif serious > self.config["thresholds"]["serious"]:
                status = "[yellow]⚠ Warning[/yellow]"
            elif result.compliance_score >= 90:
                status = "[green]✓ Passed[/green]"
            else:
                status = "[yellow]⚠ Needs Work[/yellow]"

            table.add_row(
                result.page_name,
                str(len(result.violations)),
                str(critical),
                str(serious),
                f"{result.compliance_score:.1f}%",
                status,
            )

        console.print("\n")
        console.print(table)

        # Show critical violations
        critical_violations = []
        for result in self.test_results:
            for violation in result.violations:
                if violation.impact in ["critical", "serious"]:
                    critical_violations.append((result.page_name, violation))

        if critical_violations:
            console.print("\n[red]Critical Accessibility Issues:[/red]")
            for page_name, violation in critical_violations[:10]:  # Show first 10
                console.print(f"\n• {page_name}: {violation.description}")
                console.print(f"  Impact: {violation.impact}")
                console.print(f"  Help: {violation.help}")
                console.print(f"  URL: [link]{violation.help_url}[/link]")
                console.print(f"  Affected elements: {len(violation.nodes)}")

        # Save detailed report
        report_path = Path("accessibility_report.json")
        report_data = {
            "summary": {
                "total_pages": len(self.test_results),
                "wcag_level": self.config["wcag_level"],
                "tested_at": datetime.now().isoformat(),
            },
            "results": [
                {
                    "page": result.page_name,
                    "url": result.url,
                    "score": result.compliance_score,
                    "violations": len(result.violations),
                    "critical": sum(1 for v in result.violations if v.impact == "critical"),
                    "serious": sum(1 for v in result.violations if v.impact == "serious"),
                    "moderate": sum(1 for v in result.violations if v.impact == "moderate"),
                    "minor": sum(1 for v in result.violations if v.impact == "minor"),
                    "details": [
                        {
                            "id": v.id,
                            "impact": v.impact,
                            "description": v.description,
                            "help": v.help,
                            "nodes": len(v.nodes),
                        }
                        for v in result.violations
                    ],
                }
                for result in self.test_results
            ],
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        console.print(f"\n[dim]Detailed report saved to: {report_path}[/dim]")

        # Overall assessment
        total_critical = sum(
            sum(1 for v in r.violations if v.impact == "critical")
            for r in self.test_results
        )
        avg_score = sum(r.compliance_score for r in self.test_results) / len(self.test_results)

        if total_critical == 0 and avg_score >= 90:
            console.print("\n[green]✓ Excellent accessibility compliance![/green]")
        elif total_critical == 0 and avg_score >= 80:
            console.print("\n[yellow]⚠ Good accessibility, minor improvements needed[/yellow]")
        else:
            console.print("\n[red]✗ Significant accessibility issues found[/red]")
            console.print("Please address critical issues immediately")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Accessibility Testing")
    parser.add_argument(
        "--base-url",
        default="http://localhost:5179",
        help="Base URL for testing",
    )
    parser.add_argument(
        "--wcag-level",
        choices=["A", "AA", "AAA"],
        default="AA",
        help="WCAG compliance level",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        help="Pages to test (paths)",
    )

    args = parser.parse_args()

    # Default pages to test
    pages = [
        {"name": "Home", "path": "/"},
        {"name": "Login", "path": "/login"},
        {"name": "Dashboard", "path": "/dashboard"},
        {"name": "Profile", "path": "/profile"},
        {"name": "Settings", "path": "/settings"},
    ]

    if args.pages:
        pages = [{"name": p.split("/")[-1] or "Home", "path": p} for p in args.pages]

    config = {
        "wcag_level": args.wcag_level,
        "viewport": {"width": 1920, "height": 1080},
        "test_states": {
            "keyboard_only": True,
            "screen_reader": True,
        },
        "thresholds": {
            "critical": 0,
            "serious": 3,
            "moderate": 10,
            "minor": 20,
        },
    }

    tester = AccessibilityTester(config)
    asyncio.run(tester.run_comprehensive_test(args.base_url, pages))


if __name__ == "__main__":
    main()