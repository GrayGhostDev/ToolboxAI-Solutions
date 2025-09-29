"""Coverage Analysis Agent for identifying testing gaps.

This agent analyzes test coverage across the codebase and identifies:
- Untested code paths
- Missing test scenarios
- Coverage metrics and trends
- Risk assessment for uncovered areas
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import json
import ast
from pathlib import Path
import subprocess
from datetime import datetime
import asyncio

from core.agents.base_agent import BaseAgent
from core.sparc.state_manager import StateManager
from core.coordinators.error_coordinator import ErrorCoordinator

logger = logging.getLogger(__name__)


@dataclass
class CoverageReport:
    """Represents a coverage analysis report."""
    timestamp: datetime
    overall_coverage: float
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    files_analyzed: int
    total_lines: int
    covered_lines: int
    missing_lines: int
    uncovered_files: List[str] = field(default_factory=list)
    partial_files: List[str] = field(default_factory=list)
    risk_areas: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class FileCoverage:
    """Coverage data for a single file."""
    filepath: str
    total_lines: int
    covered_lines: int
    missing_lines: List[int]
    coverage_percentage: float
    branches: Optional[Dict[str, Any]] = None
    functions: Optional[Dict[str, Any]] = None
    complexity: Optional[int] = None
    risk_score: Optional[float] = None


class CoverageAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing test coverage and identifying gaps.

    Capabilities:
    - Analyze code coverage metrics
    - Identify untested code paths
    - Generate coverage reports
    - Prioritize areas needing tests
    - Track coverage trends
    - Risk assessment for uncovered code
    """

    def __init__(self, name: str = "CoverageAnalysisAgent", **kwargs):
        """Initialize the Coverage Analysis Agent."""
        super().__init__(name=name, **kwargs)
        self.state_manager = StateManager()
        self.error_coordinator = ErrorCoordinator()

        # Coverage configuration
        self.config = {
            'coverage_tool': 'pytest-cov',
            'minimum_coverage': 90.0,
            'coverage_targets': {
                'unit': 95.0,
                'integration': 85.0,
                'e2e': 70.0
            },
            'risk_thresholds': {
                'critical': 50.0,  # Coverage below this is critical
                'warning': 70.0,   # Coverage below this is warning
                'acceptable': 85.0  # Coverage below this needs improvement
            },
            'exclude_patterns': [
                '__pycache__',
                '.pytest_cache',
                'test_*',
                '*_test.py',
                'conftest.py',
                'setup.py'
            ]
        }

        # Coverage history for trend analysis
        self.coverage_history: List[CoverageReport] = []

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coverage analysis task."""
        try:
            action = task.get('action')

            if action == 'analyze_project':
                return await self.analyze_project_coverage(task.get('project_path'))
            elif action == 'analyze_file':
                return await self.analyze_file_coverage(task.get('file_path'))
            elif action == 'identify_gaps':
                return await self.identify_coverage_gaps(task.get('coverage_data'))
            elif action == 'generate_report':
                return await self.generate_coverage_report(task.get('format', 'html'))
            elif action == 'track_trends':
                return await self.track_coverage_trends()
            elif action == 'assess_risk':
                return await self.assess_coverage_risk()
            else:
                return await self.comprehensive_analysis(task.get('project_path'))

        except Exception as e:
            return await self.handle_error(e, task)

    async def analyze_project_coverage(self, project_path: str) -> Dict[str, Any]:
        """Analyze coverage for entire project."""
        logger.info(f"Analyzing project coverage: {project_path}")

        # Run coverage analysis
        coverage_data = await self._run_coverage_analysis(project_path)

        # Parse coverage results
        file_coverages = await self._parse_coverage_data(coverage_data)

        # Calculate metrics
        metrics = await self._calculate_coverage_metrics(file_coverages)

        # Identify risk areas
        risk_areas = await self._identify_risk_areas(file_coverages)

        # Generate recommendations
        recommendations = await self._generate_recommendations(metrics, risk_areas)

        # Create report
        report = CoverageReport(
            timestamp=datetime.now(),
            overall_coverage=metrics['overall'],
            line_coverage=metrics['line'],
            branch_coverage=metrics['branch'],
            function_coverage=metrics['function'],
            files_analyzed=len(file_coverages),
            total_lines=metrics['total_lines'],
            covered_lines=metrics['covered_lines'],
            missing_lines=metrics['missing_lines'],
            uncovered_files=[f.filepath for f in file_coverages if f.coverage_percentage == 0],
            partial_files=[f.filepath for f in file_coverages if 0 < f.coverage_percentage < 100],
            risk_areas=risk_areas,
            recommendations=recommendations
        )

        # Store in history
        self.coverage_history.append(report)

        return {
            'status': 'success',
            'coverage_report': self._serialize_report(report),
            'needs_improvement': report.overall_coverage < self.config['minimum_coverage'],
            'critical_files': await self._identify_critical_files(file_coverages),
            'suggested_tests': await self._suggest_tests_for_gaps(file_coverages)
        }

    async def analyze_file_coverage(self, file_path: str) -> Dict[str, Any]:
        """Analyze coverage for a single file."""
        logger.info(f"Analyzing file coverage: {file_path}")

        # Get file coverage data
        coverage_data = await self._get_file_coverage(file_path)

        # Analyze code structure
        code_analysis = await self._analyze_code_structure(file_path)

        # Identify uncovered paths
        uncovered_paths = await self._identify_uncovered_paths(
            file_path,
            coverage_data,
            code_analysis
        )

        # Calculate complexity
        complexity = await self._calculate_complexity(file_path)

        # Generate test suggestions
        test_suggestions = await self._generate_test_suggestions(
            uncovered_paths,
            code_analysis
        )

        return {
            'status': 'success',
            'file': file_path,
            'coverage': coverage_data,
            'uncovered_paths': uncovered_paths,
            'complexity': complexity,
            'test_suggestions': test_suggestions,
            'priority': await self._calculate_test_priority(coverage_data, complexity)
        }

    async def identify_coverage_gaps(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify gaps in test coverage."""
        logger.info("Identifying coverage gaps")

        gaps = {
            'uncovered_functions': [],
            'uncovered_classes': [],
            'uncovered_branches': [],
            'partial_coverage': [],
            'edge_cases_missing': [],
            'error_handling_gaps': []
        }

        # Analyze each file
        for file_path, file_data in coverage_data.items():
            # Find uncovered functions
            uncovered_funcs = await self._find_uncovered_functions(file_path, file_data)
            gaps['uncovered_functions'].extend(uncovered_funcs)

            # Find uncovered classes
            uncovered_classes = await self._find_uncovered_classes(file_path, file_data)
            gaps['uncovered_classes'].extend(uncovered_classes)

            # Find uncovered branches
            uncovered_branches = await self._find_uncovered_branches(file_path, file_data)
            gaps['uncovered_branches'].extend(uncovered_branches)

            # Find partial coverage
            if 0 < file_data.get('coverage', 0) < 100:
                gaps['partial_coverage'].append({
                    'file': file_path,
                    'coverage': file_data['coverage'],
                    'missing_lines': file_data.get('missing_lines', [])
                })

            # Check for edge cases
            edge_gaps = await self._check_edge_case_coverage(file_path, file_data)
            gaps['edge_cases_missing'].extend(edge_gaps)

            # Check error handling
            error_gaps = await self._check_error_handling_coverage(file_path, file_data)
            gaps['error_handling_gaps'].extend(error_gaps)

        # Prioritize gaps
        prioritized_gaps = await self._prioritize_gaps(gaps)

        return {
            'status': 'success',
            'gaps': gaps,
            'prioritized_gaps': prioritized_gaps,
            'total_gaps': sum(len(v) for v in gaps.values()),
            'recommendations': await self._generate_gap_recommendations(gaps),
            'estimated_effort': await self._estimate_coverage_effort(gaps)
        }

    async def generate_coverage_report(self, format: str = 'html') -> Dict[str, Any]:
        """Generate detailed coverage report."""
        logger.info(f"Generating coverage report in {format} format")

        # Get latest coverage data
        latest_report = self.coverage_history[-1] if self.coverage_history else None

        if not latest_report:
            return {'status': 'error', 'message': 'No coverage data available'}

        # Generate report based on format
        if format == 'html':
            report_content = await self._generate_html_report(latest_report)
            report_path = 'coverage_report.html'
        elif format == 'json':
            report_content = await self._generate_json_report(latest_report)
            report_path = 'coverage_report.json'
        elif format == 'markdown':
            report_content = await self._generate_markdown_report(latest_report)
            report_path = 'coverage_report.md'
        else:
            report_content = await self._generate_text_report(latest_report)
            report_path = 'coverage_report.txt'

        # Write report to file
        with open(report_path, 'w') as f:
            f.write(report_content)

        return {
            'status': 'success',
            'report_path': report_path,
            'format': format,
            'summary': {
                'overall_coverage': latest_report.overall_coverage,
                'files_analyzed': latest_report.files_analyzed,
                'risk_areas': len(latest_report.risk_areas),
                'recommendations': len(latest_report.recommendations)
            }
        }

    async def track_coverage_trends(self) -> Dict[str, Any]:
        """Track coverage trends over time."""
        logger.info("Tracking coverage trends")

        if len(self.coverage_history) < 2:
            return {
                'status': 'warning',
                'message': 'Insufficient history for trend analysis'
            }

        trends = {
            'overall_trend': [],
            'line_trend': [],
            'branch_trend': [],
            'function_trend': [],
            'improvement_rate': 0,
            'projection': {}
        }

        # Calculate trends
        for i, report in enumerate(self.coverage_history):
            trends['overall_trend'].append({
                'timestamp': report.timestamp.isoformat(),
                'coverage': report.overall_coverage
            })
            trends['line_trend'].append({
                'timestamp': report.timestamp.isoformat(),
                'coverage': report.line_coverage
            })
            trends['branch_trend'].append({
                'timestamp': report.timestamp.isoformat(),
                'coverage': report.branch_coverage
            })
            trends['function_trend'].append({
                'timestamp': report.timestamp.isoformat(),
                'coverage': report.function_coverage
            })

        # Calculate improvement rate
        first_coverage = self.coverage_history[0].overall_coverage
        last_coverage = self.coverage_history[-1].overall_coverage
        trends['improvement_rate'] = (last_coverage - first_coverage) / len(self.coverage_history)

        # Project future coverage
        trends['projection'] = await self._project_coverage_timeline(trends['improvement_rate'])

        # Identify patterns
        patterns = await self._identify_coverage_patterns(self.coverage_history)

        return {
            'status': 'success',
            'trends': trends,
            'patterns': patterns,
            'current_coverage': last_coverage,
            'target_coverage': self.config['minimum_coverage'],
            'estimated_target_date': trends['projection'].get('target_date'),
            'recommendations': await self._generate_trend_recommendations(trends, patterns)
        }

    async def assess_coverage_risk(self) -> Dict[str, Any]:
        """Assess risk based on coverage analysis."""
        logger.info("Assessing coverage risk")

        if not self.coverage_history:
            return {'status': 'error', 'message': 'No coverage data available'}

        latest_report = self.coverage_history[-1]
        risk_assessment = {
            'overall_risk': 'low',
            'risk_score': 0,
            'critical_areas': [],
            'warning_areas': [],
            'recommendations': []
        }

        # Calculate risk score
        risk_score = await self._calculate_risk_score(latest_report)
        risk_assessment['risk_score'] = risk_score

        # Determine risk level
        if risk_score > 70:
            risk_assessment['overall_risk'] = 'critical'
        elif risk_score > 40:
            risk_assessment['overall_risk'] = 'high'
        elif risk_score > 20:
            risk_assessment['overall_risk'] = 'medium'
        else:
            risk_assessment['overall_risk'] = 'low'

        # Identify critical areas
        for area in latest_report.risk_areas:
            if area['coverage'] < self.config['risk_thresholds']['critical']:
                risk_assessment['critical_areas'].append(area)
            elif area['coverage'] < self.config['risk_thresholds']['warning']:
                risk_assessment['warning_areas'].append(area)

        # Generate risk-based recommendations
        risk_assessment['recommendations'] = await self._generate_risk_recommendations(
            risk_assessment
        )

        return {
            'status': 'success',
            'risk_assessment': risk_assessment,
            'mitigation_plan': await self._generate_mitigation_plan(risk_assessment),
            'priority_files': await self._identify_priority_files_for_testing(latest_report),
            'estimated_effort': await self._estimate_risk_mitigation_effort(risk_assessment)
        }

    async def comprehensive_analysis(self, project_path: str) -> Dict[str, Any]:
        """Perform comprehensive coverage analysis."""
        logger.info("Performing comprehensive coverage analysis")

        # Run all analyses
        project_coverage = await self.analyze_project_coverage(project_path)
        gaps = await self.identify_coverage_gaps(project_coverage['coverage_report'])
        trends = await self.track_coverage_trends()
        risk = await self.assess_coverage_risk()

        # Generate comprehensive report
        comprehensive_report = {
            'timestamp': datetime.now().isoformat(),
            'project': project_path,
            'coverage': project_coverage,
            'gaps': gaps,
            'trends': trends,
            'risk': risk,
            'action_plan': await self._generate_action_plan(
                project_coverage, gaps, trends, risk
            )
        }

        # Generate visualizations
        visualizations = await self._generate_coverage_visualizations(comprehensive_report)

        return {
            'status': 'success',
            'comprehensive_report': comprehensive_report,
            'visualizations': visualizations,
            'executive_summary': await self._generate_executive_summary(comprehensive_report),
            'next_steps': await self._recommend_next_steps(comprehensive_report)
        }

    async def _run_coverage_analysis(self, project_path: str) -> Dict[str, Any]:
        """Run coverage tool and get results."""
        try:
            # Run pytest with coverage
            cmd = [
                'pytest',
                '--cov=' + project_path,
                '--cov-report=json',
                '--cov-report=term',
                project_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_path
            )

            # Parse coverage.json
            coverage_file = Path(project_path) / 'coverage.json'
            if coverage_file.exists():
                with open(coverage_file) as f:
                    return json.load(f)

            return {}

        except Exception as e:
            logger.error(f"Coverage analysis failed: {e}")
            return {}

    async def _parse_coverage_data(self, coverage_data: Dict[str, Any]) -> List[FileCoverage]:
        """Parse raw coverage data into FileCoverage objects."""
        file_coverages = []

        files = coverage_data.get('files', {})
        for filepath, data in files.items():
            file_coverage = FileCoverage(
                filepath=filepath,
                total_lines=len(data.get('executed_lines', [])) + len(data.get('missing_lines', [])),
                covered_lines=len(data.get('executed_lines', [])),
                missing_lines=data.get('missing_lines', []),
                coverage_percentage=data.get('summary', {}).get('percent_covered', 0)
            )
            file_coverages.append(file_coverage)

        return file_coverages

    async def _calculate_coverage_metrics(self, file_coverages: List[FileCoverage]) -> Dict[str, Any]:
        """Calculate overall coverage metrics."""
        if not file_coverages:
            return {
                'overall': 0, 'line': 0, 'branch': 0, 'function': 0,
                'total_lines': 0, 'covered_lines': 0, 'missing_lines': 0
            }

        total_lines = sum(fc.total_lines for fc in file_coverages)
        covered_lines = sum(fc.covered_lines for fc in file_coverages)
        missing_lines = total_lines - covered_lines

        return {
            'overall': (covered_lines / total_lines * 100) if total_lines > 0 else 0,
            'line': (covered_lines / total_lines * 100) if total_lines > 0 else 0,
            'branch': 85.0,  # Placeholder - would need branch coverage data
            'function': 90.0,  # Placeholder - would need function coverage data
            'total_lines': total_lines,
            'covered_lines': covered_lines,
            'missing_lines': missing_lines
        }

    async def _identify_risk_areas(self, file_coverages: List[FileCoverage]) -> List[Dict[str, Any]]:
        """Identify high-risk areas with low coverage."""
        risk_areas = []

        for fc in file_coverages:
            if fc.coverage_percentage < self.config['risk_thresholds']['warning']:
                risk_areas.append({
                    'file': fc.filepath,
                    'coverage': fc.coverage_percentage,
                    'missing_lines': len(fc.missing_lines),
                    'risk_level': 'critical' if fc.coverage_percentage < self.config['risk_thresholds']['critical'] else 'warning'
                })

        return sorted(risk_areas, key=lambda x: x['coverage'])

    async def _generate_recommendations(self, metrics: Dict[str, Any], risk_areas: List[Dict[str, Any]]) -> List[str]:
        """Generate coverage improvement recommendations."""
        recommendations = []

        if metrics['overall'] < self.config['minimum_coverage']:
            recommendations.append(
                f"Overall coverage ({metrics['overall']:.1f}%) is below target ({self.config['minimum_coverage']}%). "
                f"Focus on increasing test coverage by {self.config['minimum_coverage'] - metrics['overall']:.1f}%."
            )

        if risk_areas:
            recommendations.append(
                f"Found {len(risk_areas)} high-risk files with low coverage. "
                f"Prioritize testing for: {', '.join(ra['file'] for ra in risk_areas[:3])}"
            )

        if metrics['branch'] < 80:
            recommendations.append(
                "Branch coverage is low. Add tests for conditional logic and edge cases."
            )

        return recommendations

    def _serialize_report(self, report: CoverageReport) -> Dict[str, Any]:
        """Serialize coverage report to dictionary."""
        return {
            'timestamp': report.timestamp.isoformat(),
            'overall_coverage': report.overall_coverage,
            'line_coverage': report.line_coverage,
            'branch_coverage': report.branch_coverage,
            'function_coverage': report.function_coverage,
            'files_analyzed': report.files_analyzed,
            'total_lines': report.total_lines,
            'covered_lines': report.covered_lines,
            'missing_lines': report.missing_lines,
            'uncovered_files': report.uncovered_files,
            'partial_files': report.partial_files,
            'risk_areas': report.risk_areas,
            'recommendations': report.recommendations
        }

    # Additional helper methods would continue here...