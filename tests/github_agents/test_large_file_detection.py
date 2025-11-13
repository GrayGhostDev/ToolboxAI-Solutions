
"""
Tests for Large File Detection Agent.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from core.agents.github_agents.large_file_detection_agent import LargeFileDetectionAgent


@pytest.fixture
async def detection_agent():
    """Create a detection agent instance."""
    agent = LargeFileDetectionAgent()
    return agent


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary git repository."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    os.system(f"cd {repo_path} && git init > /dev/null 2>&1")

    return repo_path


def create_test_file(path: Path, size_mb: int) -> Path:
    """Create a test file of specified size."""
    file_path = path / f"test_{size_mb}mb.dat"
    with open(file_path, "wb") as f:
        f.write(b"0" * (size_mb * 1024 * 1024))
    return file_path


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_detection_agent_initialization():
    """Test agent initialization."""
    agent = LargeFileDetectionAgent()
    assert agent is not None
    assert agent.size_thresholds["warning_mb"] == 25
    assert agent.size_thresholds["critical_mb"] == 50
    assert agent.size_thresholds["github_limit_mb"] == 100


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_analyze_file_size_categories(detection_agent):
    """Test file size categorization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create files of different sizes
        small_file = create_test_file(tmp_path, 10)  # 10MB - no warning
        warning_file = create_test_file(tmp_path, 30)  # 30MB - warning
        critical_file = create_test_file(tmp_path, 60)  # 60MB - critical
        blocker_file = create_test_file(tmp_path, 120)  # 120MB - blocker

        # Test file analysis
        small_info = detection_agent._analyze_file(small_file, small_file.stat().st_size)
        assert small_info is None  # Below threshold

        warning_info = detection_agent._analyze_file(warning_file, warning_file.stat().st_size)
        assert warning_info["severity"] == "warning"

        critical_info = detection_agent._analyze_file(critical_file, critical_file.stat().st_size)
        assert critical_info["severity"] == "critical"

        blocker_info = detection_agent._analyze_file(blocker_file, blocker_file.stat().st_size)
        assert blocker_info["severity"] == "blocker"
        assert blocker_info["exceeds_github_limit"] is True


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_format_size(detection_agent):
    """Test size formatting."""
    assert detection_agent.format_size(1024) == "1.00 KB"
    assert detection_agent.format_size(1024 * 1024) == "1.00 MB"
    assert detection_agent.format_size(1024 * 1024 * 1024) == "1.00 GB"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_generate_recommendations(detection_agent):
    """Test recommendation generation."""
    large_files = [
        {"severity": "blocker", "file_type": ".json", "size_mb": 150},
        {"severity": "critical", "file_type": ".png", "size_mb": 75},
        {"severity": "warning", "file_type": ".fig", "size_mb": 30},
    ]

    recommendations = detection_agent._generate_recommendations(large_files)

    # Should have recommendations for blockers
    assert any("exceed GitHub's 100MB limit" in r for r in recommendations)
    # Should have recommendations for images
    assert any("image file" in r for r in recommendations)
    # Should have recommendations for design files
    assert any("design file" in r for r in recommendations)


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_pre_commit_check(detection_agent):
    """Test pre-commit check functionality."""
    with patch.object(detection_agent, "_get_staged_files", new_callable=AsyncMock) as mock_staged:
        with patch.object(detection_agent, "get_repository_root") as mock_root:
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                mock_root.return_value = tmp_path

                # Create a large file
                large_file = create_test_file(tmp_path, 120)
                mock_staged.return_value = [large_file.name]

                result = await detection_agent.execute_action("pre_commit_check")

                assert result["success"] is False
                assert "Large files detected" in result["message"]
                assert len(result["large_files"]) > 0
                assert result["large_files"][0]["severity"] == "blocker"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_generate_report_json(detection_agent):
    """Test JSON report generation."""
    with patch.object(detection_agent, "analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = {
            "success": True,
            "large_files": [
                {"path": "test.dat", "size_formatted": "100 MB", "severity": "blocker"}
            ],
            "summary": {
                "total_files": 1,
                "total_size": "100 MB",
                "blockers": 1,
                "critical": 0,
                "warnings": 0,
            },
            "recommendations": ["Remove large files"],
        }

        report = await detection_agent.generate_report("json")
        assert '"success": true' in report
        assert '"test.dat"' in report


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_generate_report_markdown(detection_agent):
    """Test Markdown report generation."""
    with patch.object(detection_agent, "analyze", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = {
            "success": True,
            "large_files": [
                {"path": "test.dat", "size_formatted": "100 MB", "severity": "blocker"}
            ],
            "summary": {
                "total_files": 1,
                "total_size": "100 MB",
                "total_size_mb": 100,
                "blockers": 1,
                "critical": 0,
                "warnings": 0,
            },
            "recommendations": ["Remove large files"],
        }

        report = await detection_agent.generate_report("markdown")
        assert "# Large File Detection Report" in report
        assert "test.dat" in report
        assert "BLOCKER" in report
        assert "## Recommendations" in report


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_exempt_patterns(detection_agent):
    """Test that exempt patterns are properly ignored."""
    assert detection_agent._is_exempt(Path("node_modules/package.json"))
    assert detection_agent._is_exempt(Path(".git/objects/abc"))
    assert detection_agent._is_exempt(Path("venv/lib/python"))
    assert not detection_agent._is_exempt(Path("src/large_file.dat"))


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_metrics_tracking(detection_agent):
    """Test that metrics are properly tracked."""
    initial_ops = detection_agent.metrics["operations_performed"]

    with patch.object(detection_agent, "_get_staged_files", new_callable=AsyncMock) as mock_staged:
        with patch.object(
            detection_agent, "_get_tracked_files", new_callable=AsyncMock
        ) as mock_tracked:
            with patch.object(detection_agent, "get_repository_root") as mock_root:
                mock_root.return_value = Path("/test")
                mock_staged.return_value = []
                mock_tracked.return_value = []

                await detection_agent.analyze()

                assert detection_agent.metrics["operations_performed"] > initial_ops

                summary = detection_agent.get_metrics_summary()
                assert "runtime_seconds" in summary
                assert "success_rate" in summary


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
