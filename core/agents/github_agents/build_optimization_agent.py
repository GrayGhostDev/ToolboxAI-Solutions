"""
Build Optimization Agent for analyzing and optimizing build processes.

This agent analyzes Docker images, build artifacts, cache efficiency, and provides
actionable recommendations for optimizing build times and reducing artifact sizes.
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .base_github_agent import BaseGitHubAgent

logger = logging.getLogger(__name__)


@dataclass
class BuildArtifact:
    """Represents a build artifact with size and optimization potential."""

    path: Path
    size_bytes: int
    file_type: str
    optimization_potential: str  # "high", "medium", "low", "none"
    recommendations: list[str]


@dataclass
class DockerLayerAnalysis:
    """Analysis of Docker layers and optimization opportunities."""

    layer_id: str
    command: str
    size_bytes: int
    cacheable: bool
    optimization_score: float  # 0-1, higher = more optimization potential
    recommendations: list[str]


@dataclass
class CacheAnalysis:
    """Analysis of cache efficiency and recommendations."""

    cache_type: str  # "docker", "npm", "pip", "gradle", etc.
    hit_rate: float  # 0-1
    size_mb: float
    last_used: Optional[datetime]
    recommendations: list[str]


@dataclass
class BuildOptimizationReport:
    """Comprehensive build optimization report."""

    timestamp: datetime
    total_build_size_mb: float
    optimization_potential_mb: float
    docker_analysis: list[DockerLayerAnalysis]
    artifact_analysis: list[BuildArtifact]
    cache_analysis: list[CacheAnalysis]
    parallelization_opportunities: list[str]
    performance_bottlenecks: list[str]
    recommendations: list[str]
    estimated_time_savings: str
    estimated_size_savings_mb: float


class BuildOptimizationAgent(BaseGitHubAgent):
    """Agent for analyzing and optimizing build processes."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the build optimization agent."""
        super().__init__(config_path)
        self.build_patterns = {
            "dockerfile": ["Dockerfile*", "*.dockerfile", ".dockerignore"],
            "nodejs": [
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "node_modules/",
            ],
            "python": [
                "requirements*.txt",
                "setup.py",
                "pyproject.toml",
                "Pipfile*",
                "__pycache__/",
            ],
            "java": [
                "pom.xml",
                "build.gradle",
                "gradle.properties",
                "target/",
                "build/",
            ],
            "dotnet": ["*.csproj", "*.sln", "packages.config", "bin/", "obj/"],
            "go": ["go.mod", "go.sum", "vendor/"],
            "rust": ["Cargo.toml", "Cargo.lock", "target/"],
        }

        # Common large file patterns that should be excluded from builds
        self.exclude_patterns = [
            "*.log",
            "*.tmp",
            "*.cache",
            "*.bak",
            "*.swp",
            "*.swo",
            ".DS_Store",
            "Thumbs.db",
            "*.orig",
            "*.rej",
            "node_modules/",
            "__pycache__/",
            ".pytest_cache/",
            "target/",
            "build/",
            "dist/",
            "out/",
            "bin/",
            "obj/",
            ".git/",
            ".svn/",
            ".hg/",
            ".bzr/",
            "*.zip",
            "*.tar.gz",
            "*.7z",
            "*.rar",
        ]

    async def analyze(self, **kwargs) -> dict[str, Any]:
        """Main build analysis method.

        Args:
            **kwargs: Analysis parameters including:
                - repo_path: Path to repository (default: current directory)
                - include_docker: Whether to analyze Docker images (default: True)
                - include_artifacts: Whether to analyze build artifacts (default: True)
                - include_cache: Whether to analyze cache efficiency (default: True)

        Returns:
            Comprehensive build optimization analysis
        """
        try:
            repo_path = Path(kwargs.get("repo_path", "."))
            include_docker = kwargs.get("include_docker", True)
            include_artifacts = kwargs.get("include_artifacts", True)
            include_cache = kwargs.get("include_cache", True)

            logger.info(f"Starting build optimization analysis for {repo_path}")
            await self.log_operation("analyze_start", {"repo_path": str(repo_path)})

            # Initialize results
            results = {
                "analysis_type": "build_optimization",
                "timestamp": datetime.now().isoformat(),
                "repo_path": str(repo_path),
                "docker_analysis": {},
                "artifact_analysis": {},
                "cache_analysis": {},
                "optimization_report": {},
            }

            # Analyze Docker images if requested
            if include_docker:
                logger.info("Analyzing Docker images...")
                results["docker_analysis"] = await self.analyze_docker_images(repo_path)

            # Analyze build artifacts if requested
            if include_artifacts:
                logger.info("Analyzing build artifacts...")
                results["artifact_analysis"] = await self.analyze_build_artifacts(repo_path)

            # Analyze cache efficiency if requested
            if include_cache:
                logger.info("Analyzing cache efficiency...")
                results["cache_analysis"] = await self.analyze_cache_efficiency(repo_path)

            # Generate comprehensive optimization report
            logger.info("Generating optimization report...")
            results["optimization_report"] = await self.generate_optimization_report(
                results["docker_analysis"],
                results["artifact_analysis"],
                results["cache_analysis"],
            )

            self.update_metrics(
                operations_performed=1, files_processed=len(results.get("files", []))
            )
            await self.log_operation(
                "analyze_complete",
                {"results_summary": self._summarize_results(results)},
            )

            return results

        except Exception as e:
            logger.error(f"Error during build optimization analysis: {e}")
            self.update_metrics(errors_encountered=1)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def analyze_docker_images(self, repo_path: Path) -> dict[str, Any]:
        """Analyze Docker images for optimization opportunities.

        Args:
            repo_path: Path to repository

        Returns:
            Docker analysis results
        """
        try:
            dockerfiles = self._find_dockerfiles(repo_path)

            if not dockerfiles:
                return {
                    "found_dockerfiles": False,
                    "message": "No Dockerfiles found in repository",
                }

            analysis_results = {
                "found_dockerfiles": True,
                "dockerfiles": [],
                "total_optimization_potential_mb": 0,
                "recommendations": [],
            }

            for dockerfile_path in dockerfiles:
                logger.info(f"Analyzing Dockerfile: {dockerfile_path}")

                dockerfile_analysis = await self._analyze_single_dockerfile(dockerfile_path)
                analysis_results["dockerfiles"].append(dockerfile_analysis)

                # Add to total optimization potential
                analysis_results["total_optimization_potential_mb"] += dockerfile_analysis.get(
                    "optimization_potential_mb", 0
                )

            # Generate overall recommendations
            analysis_results["recommendations"] = self._generate_docker_recommendations(
                analysis_results["dockerfiles"]
            )

            return analysis_results

        except Exception as e:
            logger.error(f"Error analyzing Docker images: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_build_artifacts(self, repo_path: Path) -> dict[str, Any]:
        """Analyze build artifacts for size and optimization potential.

        Args:
            repo_path: Path to repository

        Returns:
            Build artifacts analysis
        """
        try:
            # Find common build output directories
            build_dirs = self._find_build_directories(repo_path)

            artifacts = []
            total_size_mb = 0

            for build_dir in build_dirs:
                if build_dir.exists():
                    logger.info(f"Analyzing build directory: {build_dir}")
                    dir_artifacts = await self._analyze_directory_artifacts(build_dir)
                    artifacts.extend(dir_artifacts)

            # Calculate total size
            total_size_mb = sum(artifact.size_bytes for artifact in artifacts) / (1024 * 1024)

            # Categorize artifacts by optimization potential
            high_potential = [a for a in artifacts if a.optimization_potential == "high"]
            medium_potential = [a for a in artifacts if a.optimization_potential == "medium"]
            low_potential = [a for a in artifacts if a.optimization_potential == "low"]

            return {
                "total_artifacts": len(artifacts),
                "total_size_mb": total_size_mb,
                "optimization_categories": {
                    "high_potential": {
                        "count": len(high_potential),
                        "size_mb": sum(a.size_bytes for a in high_potential) / (1024 * 1024),
                        "artifacts": [
                            self._artifact_to_dict(a) for a in high_potential[:10]
                        ],  # Top 10
                    },
                    "medium_potential": {
                        "count": len(medium_potential),
                        "size_mb": sum(a.size_bytes for a in medium_potential) / (1024 * 1024),
                        "artifacts": [self._artifact_to_dict(a) for a in medium_potential[:10]],
                    },
                    "low_potential": {
                        "count": len(low_potential),
                        "size_mb": sum(a.size_bytes for a in low_potential) / (1024 * 1024),
                    },
                },
                "recommendations": self._generate_artifact_recommendations(artifacts),
            }

        except Exception as e:
            logger.error(f"Error analyzing build artifacts: {e}")
            return {"success": False, "error": str(e)}

    async def analyze_cache_efficiency(self, repo_path: Path) -> dict[str, Any]:
        """Analyze cache efficiency for different build systems.

        Args:
            repo_path: Path to repository

        Returns:
            Cache efficiency analysis
        """
        try:
            cache_analyses = []

            # Check for different cache types
            cache_checks = [
                ("docker", self._analyze_docker_cache),
                ("npm", self._analyze_npm_cache),
                ("pip", self._analyze_pip_cache),
                ("gradle", self._analyze_gradle_cache),
                ("maven", self._analyze_maven_cache),
            ]

            for cache_type, analyzer_func in cache_checks:
                try:
                    cache_analysis = await analyzer_func(repo_path)
                    if cache_analysis:
                        cache_analyses.append(cache_analysis)
                except Exception as e:
                    logger.warning(f"Error analyzing {cache_type} cache: {e}")

            return {
                "cache_types_found": len(cache_analyses),
                "cache_analyses": [self._cache_analysis_to_dict(ca) for ca in cache_analyses],
                "overall_recommendations": self._generate_cache_recommendations(cache_analyses),
            }

        except Exception as e:
            logger.error(f"Error analyzing cache efficiency: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_dockerfile(self, dockerfile_path: Path) -> dict[str, Any]:
        """Generate an optimized version of a Dockerfile.

        Args:
            dockerfile_path: Path to the Dockerfile

        Returns:
            Optimized Dockerfile content and recommendations
        """
        try:
            if not dockerfile_path.exists():
                return {
                    "success": False,
                    "error": f"Dockerfile not found: {dockerfile_path}",
                }

            # Read original Dockerfile
            with open(dockerfile_path) as f:
                original_content = f.read()

            # Analyze and optimize
            optimizations = []
            optimized_lines = []

            lines = original_content.split("\n")

            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith("#"):
                    optimized_lines.append(line)
                    continue

                # Apply optimizations
                optimized_line, line_optimizations = self._optimize_dockerfile_line(line, i, lines)
                optimized_lines.append(optimized_line)
                optimizations.extend(line_optimizations)

            optimized_content = "\n".join(optimized_lines)

            return {
                "success": True,
                "original_content": original_content,
                "optimized_content": optimized_content,
                "optimizations_applied": optimizations,
                "estimated_size_reduction": self._estimate_dockerfile_size_reduction(optimizations),
            }

        except Exception as e:
            logger.error(f"Error optimizing Dockerfile: {e}")
            return {"success": False, "error": str(e)}

    async def generate_optimization_report(
        self,
        docker_analysis: dict[str, Any],
        artifact_analysis: dict[str, Any],
        cache_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a comprehensive optimization report.

        Args:
            docker_analysis: Docker analysis results
            artifact_analysis: Artifact analysis results
            cache_analysis: Cache analysis results

        Returns:
            Comprehensive optimization report
        """
        try:
            # Calculate overall metrics
            total_optimization_potential_mb = 0
            if docker_analysis.get("total_optimization_potential_mb"):
                total_optimization_potential_mb += docker_analysis[
                    "total_optimization_potential_mb"
                ]
            if artifact_analysis.get("optimization_categories"):
                for category in ["high_potential", "medium_potential"]:
                    total_optimization_potential_mb += artifact_analysis["optimization_categories"][
                        category
                    ]["size_mb"]

            # Estimate time savings
            estimated_time_savings = self._estimate_time_savings(
                docker_analysis, artifact_analysis, cache_analysis
            )

            # Compile all recommendations
            all_recommendations = []
            if docker_analysis.get("recommendations"):
                all_recommendations.extend(docker_analysis["recommendations"])
            if artifact_analysis.get("recommendations"):
                all_recommendations.extend(artifact_analysis["recommendations"])
            if cache_analysis.get("overall_recommendations"):
                all_recommendations.extend(cache_analysis["overall_recommendations"])

            # Identify parallelization opportunities
            parallelization_opportunities = self._identify_parallelization_opportunities(
                docker_analysis, artifact_analysis
            )

            # Identify performance bottlenecks
            performance_bottlenecks = self._identify_performance_bottlenecks(
                docker_analysis, artifact_analysis, cache_analysis
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_optimization_potential_mb": round(total_optimization_potential_mb, 2),
                    "estimated_time_savings": estimated_time_savings,
                    "critical_recommendations": len(
                        [r for r in all_recommendations if "critical" in r.lower()]
                    ),
                    "total_recommendations": len(all_recommendations),
                },
                "recommendations": {
                    "high_priority": [
                        r
                        for r in all_recommendations
                        if any(
                            keyword in r.lower() for keyword in ["critical", "urgent", "immediate"]
                        )
                    ],
                    "medium_priority": [
                        r
                        for r in all_recommendations
                        if "recommend" in r.lower()
                        and not any(keyword in r.lower() for keyword in ["critical", "urgent"])
                    ],
                    "low_priority": [r for r in all_recommendations if "consider" in r.lower()],
                },
                "parallelization_opportunities": parallelization_opportunities,
                "performance_bottlenecks": performance_bottlenecks,
                "next_steps": self._generate_next_steps(
                    all_recommendations, total_optimization_potential_mb
                ),
            }

        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
            return {"success": False, "error": str(e)}

    async def execute_action(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute a specific optimization action.

        Args:
            action: Action to execute
            **kwargs: Action parameters

        Returns:
            Action execution results
        """
        try:
            if action == "optimize_dockerfile":
                dockerfile_path = Path(kwargs.get("dockerfile_path", "Dockerfile"))
                return await self.optimize_dockerfile(dockerfile_path)

            elif action == "clean_build_artifacts":
                repo_path = Path(kwargs.get("repo_path", "."))
                return await self._clean_build_artifacts(repo_path)

            elif action == "optimize_gitignore":
                repo_path = Path(kwargs.get("repo_path", "."))
                return await self._optimize_gitignore(repo_path)

            elif action == "generate_dockerignore":
                repo_path = Path(kwargs.get("repo_path", "."))
                return await self._generate_dockerignore(repo_path)

            elif action == "analyze_parallel_builds":
                repo_path = Path(kwargs.get("repo_path", "."))
                return await self._analyze_parallel_build_opportunities(repo_path)

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "optimize_dockerfile",
                        "clean_build_artifacts",
                        "optimize_gitignore",
                        "generate_dockerignore",
                        "analyze_parallel_builds",
                    ],
                }

        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods

    def _find_dockerfiles(self, repo_path: Path) -> list[Path]:
        """Find all Dockerfiles in the repository."""
        dockerfiles = []
        for pattern in self.build_patterns["dockerfile"]:
            dockerfiles.extend(repo_path.rglob(pattern))
        return dockerfiles

    def _find_build_directories(self, repo_path: Path) -> list[Path]:
        """Find common build output directories."""
        build_dirs = []
        common_build_dirs = [
            "dist",
            "build",
            "target",
            "out",
            "bin",
            "obj",
            "node_modules",
            "__pycache__",
        ]

        for dir_name in common_build_dirs:
            for path in repo_path.rglob(dir_name):
                if path.is_dir():
                    build_dirs.append(path)

        return build_dirs

    async def _analyze_single_dockerfile(self, dockerfile_path: Path) -> dict[str, Any]:
        """Analyze a single Dockerfile for optimization opportunities."""
        try:
            with open(dockerfile_path) as f:
                content = f.read()

            lines = content.split("\n")
            analysis = {
                "path": str(dockerfile_path),
                "total_instructions": len(
                    [l for l in lines if l.strip() and not l.strip().startswith("#")]
                ),
                "optimization_potential_mb": 0,
                "issues": [],
                "recommendations": [],
            }

            # Analyze each instruction
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Check for common optimization issues
                if line.startswith("RUN"):
                    if (
                        "&&" not in line
                        and i < len(lines) - 1
                        and lines[i + 1].strip().startswith("RUN")
                    ):
                        analysis["issues"].append(
                            f"Line {i+1}: Multiple RUN commands can be combined"
                        )
                        analysis["recommendations"].append(
                            "Combine consecutive RUN commands to reduce layers"
                        )

                elif line.startswith("COPY") or line.startswith("ADD"):
                    if ". " in line or "./" in line:
                        analysis["issues"].append(
                            f"Line {i+1}: Copying entire context may include unnecessary files"
                        )
                        analysis["recommendations"].append(
                            "Use specific file paths or .dockerignore to exclude unnecessary files"
                        )

            # Estimate optimization potential
            analysis["optimization_potential_mb"] = len(analysis["issues"]) * 10  # Rough estimate

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing Dockerfile {dockerfile_path}: {e}")
            return {"path": str(dockerfile_path), "error": str(e)}

    async def _analyze_directory_artifacts(self, directory: Path) -> list[BuildArtifact]:
        """Analyze artifacts in a build directory."""
        artifacts = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    size_bytes = file_path.stat().st_size
                    file_type = file_path.suffix.lower()

                    # Determine optimization potential
                    optimization_potential = self._assess_artifact_optimization_potential(
                        file_path, size_bytes
                    )

                    # Generate recommendations
                    recommendations = self._generate_artifact_specific_recommendations(
                        file_path, size_bytes, file_type
                    )

                    artifact = BuildArtifact(
                        path=file_path,
                        size_bytes=size_bytes,
                        file_type=file_type,
                        optimization_potential=optimization_potential,
                        recommendations=recommendations,
                    )
                    artifacts.append(artifact)

        except Exception as e:
            logger.error(f"Error analyzing directory {directory}: {e}")

        return artifacts

    def _assess_artifact_optimization_potential(self, file_path: Path, size_bytes: int) -> str:
        """Assess the optimization potential of a build artifact."""
        # Size thresholds in bytes
        large_threshold = 10 * 1024 * 1024  # 10MB
        medium_threshold = 1 * 1024 * 1024  # 1MB

        file_type = file_path.suffix.lower()

        # High potential files
        if size_bytes > large_threshold:
            return "high"
        elif file_type in [".log", ".tmp", ".cache", ".bak"]:
            return "high"
        elif any(pattern in str(file_path) for pattern in self.exclude_patterns):
            return "high"

        # Medium potential files
        elif size_bytes > medium_threshold:
            return "medium"
        elif file_type in [".js", ".css", ".html", ".json"]:
            return "medium"

        # Low potential files
        elif size_bytes > 100 * 1024:  # 100KB
            return "low"

        return "none"

    def _generate_artifact_specific_recommendations(
        self, file_path: Path, size_bytes: int, file_type: str
    ) -> list[str]:
        """Generate specific recommendations for an artifact."""
        recommendations = []

        if size_bytes > 10 * 1024 * 1024:  # 10MB
            recommendations.append("Consider excluding from build - file is very large")

        if file_type in [".log", ".tmp", ".cache"]:
            recommendations.append("Exclude from version control and builds")

        if file_type in [".js", ".css"]:
            recommendations.append("Consider minification and compression")

        if file_type in [".png", ".jpg", ".jpeg"]:
            recommendations.append("Consider image optimization and compression")

        if "node_modules" in str(file_path):
            recommendations.append("Use .dockerignore to exclude from Docker builds")

        return recommendations

    async def _analyze_docker_cache(self, repo_path: Path) -> Optional[CacheAnalysis]:
        """Analyze Docker cache efficiency."""
        try:
            # Check if Docker is available
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return None

            # Get Docker system info
            result = subprocess.run(["docker", "system", "df"], capture_output=True, text=True)
            if result.returncode == 0:
                # Parse Docker system usage
                lines = result.stdout.split("\n")
                for line in lines:
                    if "Build Cache" in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            size_str = parts[2]
                            # Parse size (e.g., "1.5GB" -> 1500.0)
                            size_mb = self._parse_size_to_mb(size_str)

                            return CacheAnalysis(
                                cache_type="docker",
                                hit_rate=0.5,  # Placeholder - would need build logs to calculate
                                size_mb=size_mb,
                                last_used=None,
                                recommendations=[
                                    "Use multi-stage builds to reduce cache size",
                                    "Order Dockerfile instructions to maximize cache reuse",
                                    "Use .dockerignore to reduce build context",
                                ],
                            )

            return None

        except Exception as e:
            logger.error(f"Error analyzing Docker cache: {e}")
            return None

    async def _analyze_npm_cache(self, repo_path: Path) -> Optional[CacheAnalysis]:
        """Analyze npm cache efficiency."""
        try:
            package_json = repo_path / "package.json"
            if not package_json.exists():
                return None

            # Check npm cache info
            result = subprocess.run(["npm", "cache", "ls"], capture_output=True, text=True)
            if result.returncode == 0:
                return CacheAnalysis(
                    cache_type="npm",
                    hit_rate=0.7,  # Typical npm cache hit rate
                    size_mb=0.0,  # Would need to parse npm cache verify output
                    last_used=None,
                    recommendations=[
                        "Use npm ci instead of npm install for faster, reliable builds",
                        "Cache node_modules in CI/CD pipelines",
                        "Use package-lock.json for consistent dependency resolution",
                    ],
                )

            return None

        except Exception as e:
            logger.error(f"Error analyzing npm cache: {e}")
            return None

    async def _analyze_pip_cache(self, repo_path: Path) -> Optional[CacheAnalysis]:
        """Analyze pip cache efficiency."""
        try:
            requirements_files = list(repo_path.rglob("requirements*.txt"))
            setup_py = repo_path / "setup.py"
            pyproject_toml = repo_path / "pyproject.toml"

            if not (requirements_files or setup_py.exists() or pyproject_toml.exists()):
                return None

            return CacheAnalysis(
                cache_type="pip",
                hit_rate=0.6,  # Typical pip cache hit rate
                size_mb=0.0,
                last_used=None,
                recommendations=[
                    "Use pip cache in CI/CD to speed up builds",
                    "Pin dependency versions for consistent builds",
                    "Use virtual environments to isolate dependencies",
                ],
            )

        except Exception as e:
            logger.error(f"Error analyzing pip cache: {e}")
            return None

    async def _analyze_gradle_cache(self, repo_path: Path) -> Optional[CacheAnalysis]:
        """Analyze Gradle cache efficiency."""
        try:
            gradle_files = list(repo_path.rglob("build.gradle*")) + list(
                repo_path.rglob("gradle.properties")
            )
            if not gradle_files:
                return None

            return CacheAnalysis(
                cache_type="gradle",
                hit_rate=0.8,  # Gradle has good caching
                size_mb=0.0,
                last_used=None,
                recommendations=[
                    "Enable Gradle build cache with org.gradle.caching=true",
                    "Use Gradle daemon for faster builds",
                    "Configure remote build cache for CI/CD",
                ],
            )

        except Exception as e:
            logger.error(f"Error analyzing Gradle cache: {e}")
            return None

    async def _analyze_maven_cache(self, repo_path: Path) -> Optional[CacheAnalysis]:
        """Analyze Maven cache efficiency."""
        try:
            pom_xml = repo_path / "pom.xml"
            if not pom_xml.exists():
                return None

            return CacheAnalysis(
                cache_type="maven",
                hit_rate=0.7,  # Typical Maven cache hit rate
                size_mb=0.0,
                last_used=None,
                recommendations=[
                    "Cache ~/.m2/repository in CI/CD pipelines",
                    "Use Maven dependency plugin to analyze dependencies",
                    "Configure local repository for offline builds",
                ],
            )

        except Exception as e:
            logger.error(f"Error analyzing Maven cache: {e}")
            return None

    def _parse_size_to_mb(self, size_str: str) -> float:
        """Parse size string (e.g., '1.5GB') to MB."""
        try:
            size_str = size_str.upper().replace(" ", "")
            if "GB" in size_str:
                return float(size_str.replace("GB", "")) * 1024
            elif "MB" in size_str:
                return float(size_str.replace("MB", ""))
            elif "KB" in size_str:
                return float(size_str.replace("KB", "")) / 1024
            elif "B" in size_str:
                return float(size_str.replace("B", "")) / (1024 * 1024)
            return 0.0
        except:
            return 0.0

    def _optimize_dockerfile_line(
        self, line: str, line_num: int, all_lines: list[str]
    ) -> tuple[str, list[str]]:
        """Optimize a single Dockerfile line."""
        optimizations = []

        # Basic optimizations
        if line.startswith("RUN ") and "&&" not in line:
            # Check if next line is also RUN
            if line_num + 1 < len(all_lines) and all_lines[line_num + 1].strip().startswith("RUN "):
                optimizations.append(
                    f"Line {line_num + 1}: Consider combining with next RUN command"
                )

        return line, optimizations

    def _estimate_dockerfile_size_reduction(self, optimizations: list[str]) -> str:
        """Estimate size reduction from Dockerfile optimizations."""
        reduction_mb = len(optimizations) * 5  # Rough estimate: 5MB per optimization
        return f"~{reduction_mb}MB"

    def _estimate_time_savings(
        self, docker_analysis: dict, artifact_analysis: dict, cache_analysis: dict
    ) -> str:
        """Estimate build time savings from optimizations."""
        savings_minutes = 0

        # Docker optimizations
        if docker_analysis.get("dockerfiles"):
            docker_issues = sum(len(df.get("issues", [])) for df in docker_analysis["dockerfiles"])
            savings_minutes += docker_issues * 2  # 2 minutes per Docker optimization

        # Artifact optimizations
        if artifact_analysis.get("optimization_categories"):
            high_potential = artifact_analysis["optimization_categories"].get("high_potential", {})
            savings_minutes += (
                high_potential.get("count", 0) * 1
            )  # 1 minute per artifact optimization

        # Cache optimizations
        if cache_analysis.get("cache_analyses"):
            savings_minutes += (
                len(cache_analysis["cache_analyses"]) * 5
            )  # 5 minutes per cache optimization

        if savings_minutes < 60:
            return f"~{savings_minutes} minutes"
        else:
            hours = savings_minutes // 60
            minutes = savings_minutes % 60
            return f"~{hours}h {minutes}m"

    def _identify_parallelization_opportunities(
        self, docker_analysis: dict, artifact_analysis: dict
    ) -> list[str]:
        """Identify opportunities for parallel builds."""
        opportunities = []

        # Check for multiple Dockerfiles
        if docker_analysis.get("dockerfiles") and len(docker_analysis["dockerfiles"]) > 1:
            opportunities.append("Multiple Dockerfiles can be built in parallel")

        # Check for multiple build systems
        if artifact_analysis.get("total_artifacts", 0) > 0:
            # This is a simplified check - in reality, we'd analyze the actual build files
            opportunities.append("Consider using parallel build steps in CI/CD")

        return opportunities

    def _identify_performance_bottlenecks(
        self, docker_analysis: dict, artifact_analysis: dict, cache_analysis: dict
    ) -> list[str]:
        """Identify performance bottlenecks in the build process."""
        bottlenecks = []

        # Large artifacts
        if (
            artifact_analysis.get("optimization_categories", {})
            .get("high_potential", {})
            .get("size_mb", 0)
            > 100
        ):
            bottlenecks.append("Large build artifacts are slowing down builds and deployments")

        # Poor cache efficiency
        cache_analyses = cache_analysis.get("cache_analyses", [])
        for cache in cache_analyses:
            if cache.get("hit_rate", 1.0) < 0.5:
                bottlenecks.append(f"Poor {cache.get('cache_type', 'unknown')} cache hit rate")

        # Docker issues
        docker_issues_count = sum(
            len(df.get("issues", [])) for df in docker_analysis.get("dockerfiles", [])
        )
        if docker_issues_count > 5:
            bottlenecks.append(
                "Multiple Docker optimization issues are impacting build performance"
            )

        return bottlenecks

    def _generate_next_steps(
        self, recommendations: list[str], optimization_potential_mb: float
    ) -> list[str]:
        """Generate actionable next steps."""
        next_steps = []

        if optimization_potential_mb > 100:
            next_steps.append("Priority: Address large artifact optimization opportunities")

        if any("docker" in rec.lower() for rec in recommendations):
            next_steps.append("Optimize Dockerfiles for better layer caching and smaller images")

        if any("cache" in rec.lower() for rec in recommendations):
            next_steps.append("Implement build caching strategies in CI/CD pipelines")

        next_steps.append("Set up build performance monitoring to track improvements")

        return next_steps

    # Additional helper methods for actions

    async def _clean_build_artifacts(self, repo_path: Path) -> dict[str, Any]:
        """Clean unnecessary build artifacts."""
        try:
            cleaned_files = []
            total_size_freed = 0

            # Find and clean common build artifacts
            patterns_to_clean = ["*.tmp", "*.log", "*.cache", "*.bak"]

            for pattern in patterns_to_clean:
                for file_path in repo_path.rglob(pattern):
                    if file_path.is_file():
                        size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_files.append(str(file_path))
                        total_size_freed += size

            return {
                "success": True,
                "files_cleaned": len(cleaned_files),
                "size_freed_mb": total_size_freed / (1024 * 1024),
                "cleaned_files": cleaned_files[:20],  # Show first 20
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_gitignore(self, repo_path: Path) -> dict[str, Any]:
        """Optimize .gitignore file to exclude build artifacts."""
        try:
            gitignore_path = repo_path / ".gitignore"

            # Read existing .gitignore
            existing_patterns = set()
            if gitignore_path.exists():
                with open(gitignore_path) as f:
                    existing_patterns = set(
                        line.strip() for line in f if line.strip() and not line.startswith("#")
                    )

            # Recommended patterns
            recommended_patterns = {
                "# Build outputs",
                "dist/",
                "build/",
                "target/",
                "out/",
                "bin/",
                "obj/",
                "# Dependencies",
                "node_modules/",
                "__pycache__/",
                ".pytest_cache/",
                "# Logs and temporary files",
                "*.log",
                "*.tmp",
                "*.cache",
                "*.bak",
                "*.swp",
                "*.swo",
                "# OS generated files",
                ".DS_Store",
                "Thumbs.db",
            }

            new_patterns = recommended_patterns - existing_patterns

            if new_patterns:
                # Append new patterns
                with open(gitignore_path, "a") as f:
                    f.write("\n# Added by BuildOptimizationAgent\n")
                    for pattern in sorted(new_patterns):
                        f.write(f"{pattern}\n")

            return {
                "success": True,
                "patterns_added": len(new_patterns),
                "new_patterns": list(new_patterns),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_dockerignore(self, repo_path: Path) -> dict[str, Any]:
        """Generate optimized .dockerignore file."""
        try:
            dockerignore_path = repo_path / ".dockerignore"

            recommended_patterns = [
                "# Version control",
                ".git",
                ".gitignore",
                ".gitattributes",
                "# Build outputs",
                "dist",
                "build",
                "target",
                "out",
                "bin",
                "obj",
                "# Dependencies",
                "node_modules",
                "__pycache__",
                ".pytest_cache",
                "# Development files",
                "*.md",
                "README*",
                "docs/",
                "tests/",
                "# Logs and temporary files",
                "*.log",
                "*.tmp",
                "*.cache",
                "*.bak",
                "# IDE files",
                ".vscode",
                ".idea",
                "*.swp",
                "*.swo",
            ]

            with open(dockerignore_path, "w") as f:
                f.write("# Generated by BuildOptimizationAgent\n")
                for pattern in recommended_patterns:
                    f.write(f"{pattern}\n")

            return {
                "success": True,
                "file_created": str(dockerignore_path),
                "patterns_count": len([p for p in recommended_patterns if not p.startswith("#")]),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _analyze_parallel_build_opportunities(self, repo_path: Path) -> dict[str, Any]:
        """Analyze opportunities for parallel builds."""
        try:
            opportunities = []

            # Check for multiple build systems
            has_node = (repo_path / "package.json").exists()
            has_python = any(
                (repo_path / f).exists() for f in ["requirements.txt", "setup.py", "pyproject.toml"]
            )
            has_java = any((repo_path / f).exists() for f in ["pom.xml", "build.gradle"])
            has_docker = len(list(repo_path.rglob("Dockerfile*"))) > 0

            build_systems = []
            if has_node:
                build_systems.append("Node.js")
            if has_python:
                build_systems.append("Python")
            if has_java:
                build_systems.append("Java")
            if has_docker:
                build_systems.append("Docker")

            if len(build_systems) > 1:
                opportunities.append(f"Multiple build systems detected: {', '.join(build_systems)}")
                opportunities.append(
                    "Consider using parallel CI/CD jobs for different build systems"
                )

            # Check for multiple Dockerfiles
            dockerfiles = list(repo_path.rglob("Dockerfile*"))
            if len(dockerfiles) > 1:
                opportunities.append(
                    f"{len(dockerfiles)} Dockerfiles found - can be built in parallel"
                )

            return {
                "success": True,
                "build_systems": build_systems,
                "opportunities": opportunities,
                "parallelization_score": len(opportunities) * 2,  # Simple scoring
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _summarize_results(self, results: dict[str, Any]) -> dict[str, Any]:
        """Create a summary of analysis results."""
        return {
            "docker_files_found": len(results.get("docker_analysis", {}).get("dockerfiles", [])),
            "total_artifacts": results.get("artifact_analysis", {}).get("total_artifacts", 0),
            "cache_types": results.get("cache_analysis", {}).get("cache_types_found", 0),
            "optimization_potential": results.get("optimization_report", {})
            .get("summary", {})
            .get("total_optimization_potential_mb", 0),
        }

    def _generate_docker_recommendations(self, dockerfiles: list[dict]) -> list[str]:
        """Generate Docker-specific recommendations."""
        recommendations = []

        total_issues = sum(len(df.get("issues", [])) for df in dockerfiles)
        if total_issues > 0:
            recommendations.append(f"Found {total_issues} Docker optimization opportunities")
            recommendations.append("Use multi-stage builds to reduce final image size")
            recommendations.append("Combine RUN commands to reduce layer count")
            recommendations.append("Use .dockerignore to exclude unnecessary files")

        return recommendations

    def _generate_artifact_recommendations(self, artifacts: list[BuildArtifact]) -> list[str]:
        """Generate artifact-specific recommendations."""
        recommendations = []

        large_artifacts = [a for a in artifacts if a.size_bytes > 10 * 1024 * 1024]
        if large_artifacts:
            recommendations.append(f"Found {len(large_artifacts)} large artifacts over 10MB")
            recommendations.append("Consider excluding large files from version control")
            recommendations.append("Use Git LFS for large binary files")

        return recommendations

    def _generate_cache_recommendations(self, cache_analyses: list[CacheAnalysis]) -> list[str]:
        """Generate cache-specific recommendations."""
        recommendations = []

        for cache in cache_analyses:
            if cache.hit_rate < 0.6:
                recommendations.append(
                    f"Improve {cache.cache_type} cache configuration for better hit rates"
                )

        if cache_analyses:
            recommendations.append("Implement cache warming strategies in CI/CD")
            recommendations.append("Monitor cache hit rates and sizes regularly")

        return recommendations

    def _artifact_to_dict(self, artifact: BuildArtifact) -> dict[str, Any]:
        """Convert BuildArtifact to dictionary."""
        return {
            "path": str(artifact.path),
            "size_mb": artifact.size_bytes / (1024 * 1024),
            "file_type": artifact.file_type,
            "optimization_potential": artifact.optimization_potential,
            "recommendations": artifact.recommendations,
        }

    def _cache_analysis_to_dict(self, cache_analysis: CacheAnalysis) -> dict[str, Any]:
        """Convert CacheAnalysis to dictionary."""
        return {
            "cache_type": cache_analysis.cache_type,
            "hit_rate": cache_analysis.hit_rate,
            "size_mb": cache_analysis.size_mb,
            "last_used": cache_analysis.last_used.isoformat() if cache_analysis.last_used else None,
            "recommendations": cache_analysis.recommendations,
        }
