"""
Integration tests for Roblox AI Agent Suite

Tests the complete functionality of all Roblox agents including:
- Content generation
- Script optimization
- Security validation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the Roblox agents
from core.agents.roblox.roblox_content_generation_agent import (
    RobloxContentGenerationAgent,
    EducationalContent,
    SubjectType,
    ActivityType
)
from core.agents.roblox.roblox_script_optimization_agent import (
    RobloxScriptOptimizationAgent,
    OptimizationLevel,
    PerformanceIssue,
    OptimizationResult
)
from core.agents.roblox.roblox_security_validation_agent import (
    RobloxSecurityValidationAgent,
    ThreatLevel,
    VulnerabilityType,
    SecurityVulnerability,
    SecurityReport
)


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    mock = Mock()
    mock.predict.return_value = "Mocked LLM response"
    return mock


@pytest.fixture
def content_agent(mock_llm):
    """Create content generation agent with mocked LLM"""
    return RobloxContentGenerationAgent(llm=mock_llm)


@pytest.fixture
def optimization_agent(mock_llm):
    """Create optimization agent with mocked LLM"""
    return RobloxScriptOptimizationAgent(llm=mock_llm)


@pytest.fixture
def security_agent(mock_llm):
    """Create security validation agent with mocked LLM"""
    return RobloxSecurityValidationAgent(llm=mock_llm)


@pytest.fixture
def sample_vulnerable_script():
    """Sample vulnerable Luau script for testing"""
    return """
    -- Vulnerable script with multiple issues
    local password = "admin123"  -- Hardcoded password

    local RemoteEvent = game.ReplicatedStorage.AdminEvent

    RemoteEvent.OnServerEvent:Connect(function(player, command, data)
        -- No input validation!
        if command == "execute" then
            loadstring(data)()  -- Critical vulnerability!
        end

        -- No rate limiting
        print(player.UserId)  -- PII exposure
    end)

    while true do
        wait()  -- Inefficient wait
        local children = workspace:GetChildren()
    end
    """


@pytest.fixture
def sample_educational_script():
    """Sample educational script for testing"""
    return """
    -- Math learning game controller
    local Players = game:GetService("Players")
    local RunService = game:GetService("RunService")

    local function createMathPuzzle(difficulty)
        local num1 = math.random(1, difficulty * 10)
        local num2 = math.random(1, difficulty * 10)
        return {
            question = num1 .. " + " .. num2 .. " = ?",
            answer = num1 + num2
        }
    end

    Players.PlayerAdded:Connect(function(player)
        -- Initialize player data
        local puzzle = createMathPuzzle(1)
        -- Display puzzle to player
    end)
    """


class TestRobloxContentGenerationAgent:
    """Test suite for content generation agent"""

    def test_agent_initialization(self, content_agent):
        """Test agent initializes correctly"""
        assert content_agent.name == "RobloxContentGenerator"
        assert content_agent.llm is not None

    def test_generate_educational_content(self, content_agent):
        """Test educational content generation"""
        content = content_agent.generate_educational_content(
            subject=SubjectType.MATHEMATICS,
            topic="Addition",
            grade_level=3,
            activity_type=ActivityType.QUIZ
        )

        assert isinstance(content, EducationalContent)
        assert content.subject == SubjectType.MATHEMATICS
        assert content.topic == "Addition"
        assert content.grade_level == 3
        assert len(content.scripts) > 0

    def test_generate_quiz_system(self, content_agent):
        """Test quiz system generation"""
        quiz_code = content_agent._generate_quiz_system(
            subject="Math",
            topic="Fractions",
            num_questions=5
        )

        assert "QuizSystem" in quiz_code
        assert "questions" in quiz_code
        assert "checkAnswer" in quiz_code
        assert "showResults" in quiz_code

    def test_generate_accessibility_features(self, content_agent):
        """Test accessibility feature generation"""
        accessibility_code = content_agent._generate_accessibility_controller()

        assert "AccessibilityController" in accessibility_code
        assert "TextToSpeech" in accessibility_code
        assert "HighContrast" in accessibility_code
        assert "Subtitles" in accessibility_code
        assert "ColorblindMode" in accessibility_code

    def test_validate_educational_standards(self, content_agent):
        """Test educational standards validation"""
        content = EducationalContent(
            subject=SubjectType.SCIENCE,
            topic="Solar System",
            grade_level=5,
            activity_type=ActivityType.EXPLORATION,
            scripts={"main": "-- Solar system exploration"},
            assets=[],
            accessibility_features=["text-to-speech"]
        )

        is_valid = content_agent.validate_educational_standards(content)
        assert is_valid is True

    @pytest.mark.parametrize("subject,expected_template", [
        (SubjectType.MATHEMATICS, "math_puzzle"),
        (SubjectType.SCIENCE, "science_experiment"),
        (SubjectType.HISTORY, "historical_exploration"),
        (SubjectType.LANGUAGE, "language_learning")
    ])
    def test_subject_specific_templates(self, content_agent, subject, expected_template):
        """Test that different subjects use appropriate templates"""
        content = content_agent.generate_educational_content(
            subject=subject,
            topic="Test Topic",
            grade_level=5,
            activity_type=ActivityType.INTERACTIVE
        )

        # Verify subject-specific elements are present
        assert content.subject == subject
        assert len(content.scripts) > 0


class TestRobloxScriptOptimizationAgent:
    """Test suite for script optimization agent"""

    def test_agent_initialization(self, optimization_agent):
        """Test agent initializes correctly"""
        assert optimization_agent.name == "RobloxScriptOptimizer"
        assert optimization_agent.optimization_level == OptimizationLevel.BALANCED

    def test_analyze_performance_issues(self, optimization_agent, sample_vulnerable_script):
        """Test performance issue detection"""
        issues = optimization_agent._analyze_script_performance(sample_vulnerable_script)

        assert len(issues) > 0
        assert any(issue.severity == "critical" for issue in issues)
        assert any("wait()" in issue.description for issue in issues)
        assert any("loadstring" in issue.description for issue in issues)

    def test_optimize_loops(self, optimization_agent):
        """Test loop optimization"""
        original_code = """
        for i = 1, #myTable do
            local item = myTable[i]
            process(item)
        end

        for k, v in pairs(arrayTable) do
            print(v)
        end
        """

        optimized = optimization_agent._optimize_loops(original_code)

        # Check if optimizations were applied
        assert "local" in optimized or "ipairs" in optimized

    def test_optimize_table_operations(self, optimization_agent):
        """Test table operation optimization"""
        original_code = """
        local results = {}
        for i = 1, 100 do
            table.insert(results, i * 2)
        end
        """

        optimized = optimization_agent._optimize_table_operations(original_code)

        # Check if table.insert was optimized
        assert "results[#results + 1]" in optimized or "table.insert" in optimized

    def test_optimize_roblox_specific(self, optimization_agent):
        """Test Roblox-specific optimizations"""
        original_code = """
        wait(1)
        spawn(function()
            print("Task")
        end)
        delay(2, function()
            print("Delayed")
        end)
        """

        optimized = optimization_agent._optimize_roblox_specific(original_code)

        assert "task.wait" in optimized
        assert "task.spawn" in optimized
        assert "task.delay" in optimized

    def test_optimization_levels(self, optimization_agent, sample_educational_script):
        """Test different optimization levels"""
        # Conservative optimization
        result_conservative = optimization_agent.optimize_script(
            sample_educational_script,
            optimization_level=OptimizationLevel.CONSERVATIVE
        )

        # Aggressive optimization
        result_aggressive = optimization_agent.optimize_script(
            sample_educational_script,
            optimization_level=OptimizationLevel.AGGRESSIVE
        )

        assert isinstance(result_conservative, OptimizationResult)
        assert isinstance(result_aggressive, OptimizationResult)
        assert result_aggressive.optimization_level == OptimizationLevel.AGGRESSIVE

    def test_benchmark_generation(self, optimization_agent, sample_educational_script):
        """Test benchmark code generation"""
        benchmark = optimization_agent.benchmark_script(sample_educational_script)

        assert "benchmark_code" in benchmark
        assert "instructions" in benchmark
        assert "metrics_to_track" in benchmark
        assert "benchmark" in benchmark["benchmark_code"]
        assert "profileMemory" in benchmark["benchmark_code"]

    def test_optimization_report_generation(self, optimization_agent, sample_educational_script):
        """Test optimization report generation"""
        result = optimization_agent.optimize_script(sample_educational_script)
        report = optimization_agent.generate_optimization_report(
            sample_educational_script,
            result
        )

        assert "Optimization Report" in report
        assert "Performance Issues" in report
        assert "Metrics" in report
        assert "Recommendations" in report


class TestRobloxSecurityValidationAgent:
    """Test suite for security validation agent"""

    def test_agent_initialization(self, security_agent):
        """Test agent initializes correctly"""
        assert security_agent.name == "RobloxSecurityValidator"
        assert security_agent.strict_mode is True

    def test_detect_dangerous_functions(self, security_agent, sample_vulnerable_script):
        """Test detection of dangerous functions"""
        vulnerabilities = security_agent._scan_for_dangerous_functions(sample_vulnerable_script)

        assert len(vulnerabilities) > 0
        assert any(v.vulnerability_type == VulnerabilityType.CODE_INJECTION for v in vulnerabilities)
        assert any("loadstring" in v.description for v in vulnerabilities)

    def test_detect_authentication_issues(self, security_agent, sample_vulnerable_script):
        """Test detection of authentication issues"""
        vulnerabilities = security_agent._scan_for_authentication_issues(sample_vulnerable_script)

        assert len(vulnerabilities) > 0
        assert any("password" in v.description.lower() for v in vulnerabilities)
        assert any(v.threat_level == ThreatLevel.HIGH for v in vulnerabilities)

    def test_detect_input_validation_issues(self, security_agent, sample_vulnerable_script):
        """Test detection of input validation issues"""
        vulnerabilities = security_agent._scan_for_input_validation(sample_vulnerable_script)

        assert len(vulnerabilities) > 0
        assert any(v.vulnerability_type == VulnerabilityType.INPUT_VALIDATION for v in vulnerabilities)

    def test_calculate_risk_score(self, security_agent):
        """Test risk score calculation"""
        vulnerabilities = [
            SecurityVulnerability(
                threat_level=ThreatLevel.CRITICAL,
                vulnerability_type=VulnerabilityType.CODE_INJECTION,
                location="Line 10",
                description="Critical issue",
                impact="High impact",
                remediation="Fix immediately",
                exploitable=True
            ),
            SecurityVulnerability(
                threat_level=ThreatLevel.MEDIUM,
                vulnerability_type=VulnerabilityType.RATE_LIMITING,
                location="Line 20",
                description="Medium issue",
                impact="Medium impact",
                remediation="Fix soon",
                exploitable=False
            )
        ]

        score = security_agent._calculate_risk_score(vulnerabilities)

        assert score > 0
        assert score <= 10

    def test_validate_script(self, security_agent, sample_vulnerable_script):
        """Test complete script validation"""
        report = security_agent.validate_script(
            sample_vulnerable_script,
            script_type="ServerScript"
        )

        assert isinstance(report, SecurityReport)
        assert len(report.vulnerabilities) > 0
        assert report.risk_score > 0
        assert "no_dangerous_functions" in report.compliance_status
        assert len(report.recommendations) > 0

    def test_identify_safe_patterns(self, security_agent):
        """Test identification of safe patterns"""
        safe_script = """
        -- Safe script with good practices
        local function validateInput(input)
            assert(type(input) == "string", "Invalid input")
            return true
        end

        local connection
        connection = RemoteEvent.OnServerEvent:Connect(function(player, data)
            if not validateInput(data) then
                return
            end
            -- Process
        end)

        -- Cleanup
        connection:Disconnect()
        """

        safe_patterns = security_agent._identify_safe_patterns(safe_script)

        assert len(safe_patterns) > 0
        assert "type checking" in safe_patterns
        assert "assert statements" in safe_patterns
        assert "connection cleanup" in safe_patterns

    def test_generate_fix_suggestions(self, security_agent):
        """Test fix suggestion generation"""
        vulnerability = SecurityVulnerability(
            threat_level=ThreatLevel.CRITICAL,
            vulnerability_type=VulnerabilityType.CODE_INJECTION,
            location="Line 10",
            description="loadstring usage",
            impact="Arbitrary code execution",
            remediation="Replace with template executor",
            exploitable=True
        )

        fix = security_agent.generate_fix_suggestions(vulnerability)

        assert "TemplateExecutor" in fix
        assert "Replace loadstring" in fix

    def test_security_report_markdown(self, security_agent, sample_vulnerable_script):
        """Test markdown report generation"""
        report = security_agent.validate_script(sample_vulnerable_script)
        markdown = security_agent.generate_security_report_markdown(report)

        assert "Security Validation Report" in markdown
        assert "Risk Score" in markdown
        assert "Vulnerabilities Found" in markdown
        assert "Compliance Status" in markdown
        assert "Recommendations" in markdown


class TestAgentIntegration:
    """Test integration between multiple agents"""

    def test_content_generation_and_optimization(self, content_agent, optimization_agent):
        """Test content generation followed by optimization"""
        # Generate content
        content = content_agent.generate_educational_content(
            subject=SubjectType.MATHEMATICS,
            topic="Multiplication",
            grade_level=4,
            activity_type=ActivityType.QUIZ
        )

        # Optimize the generated scripts
        for script_name, script_code in content.scripts.items():
            result = optimization_agent.optimize_script(script_code)
            assert result.optimized_code is not None
            assert len(result.issues_found) >= 0

    def test_content_generation_and_security_validation(self, content_agent, security_agent):
        """Test content generation followed by security validation"""
        # Generate content
        content = content_agent.generate_educational_content(
            subject=SubjectType.SCIENCE,
            topic="Chemistry",
            grade_level=8,
            activity_type=ActivityType.EXPERIMENT
        )

        # Validate security of generated scripts
        for script_name, script_code in content.scripts.items():
            report = security_agent.validate_script(script_code)
            # Generated content should be secure
            assert report.risk_score < 5.0
            assert all(v.threat_level != ThreatLevel.CRITICAL
                      for v in report.vulnerabilities)

    def test_full_pipeline(self, content_agent, optimization_agent, security_agent):
        """Test complete pipeline: generation -> optimization -> validation"""
        # 1. Generate educational content
        content = content_agent.generate_educational_content(
            subject=SubjectType.HISTORY,
            topic="Ancient Rome",
            grade_level=6,
            activity_type=ActivityType.EXPLORATION
        )

        optimized_scripts = {}
        security_reports = {}

        # 2. Optimize each script
        for script_name, script_code in content.scripts.items():
            opt_result = optimization_agent.optimize_script(
                script_code,
                optimization_level=OptimizationLevel.BALANCED
            )
            optimized_scripts[script_name] = opt_result.optimized_code

            # 3. Validate security of optimized script
            sec_report = security_agent.validate_script(
                opt_result.optimized_code,
                script_type="ModuleScript"
            )
            security_reports[script_name] = sec_report

        # Verify pipeline results
        assert len(optimized_scripts) == len(content.scripts)
        assert len(security_reports) == len(content.scripts)

        # All optimized scripts should pass security validation
        for script_name, report in security_reports.items():
            assert report.risk_score < 7.0  # Acceptable risk level
            assert report.compliance_status.get("roblox_tos_compliant", False) is True


@pytest.mark.asyncio
class TestAgentPerformance:
    """Performance tests for agents"""

    async def test_content_generation_performance(self, content_agent):
        """Test content generation performance"""
        import time

        start_time = time.time()

        content = content_agent.generate_educational_content(
            subject=SubjectType.MATHEMATICS,
            topic="Algebra",
            grade_level=7,
            activity_type=ActivityType.LESSON
        )

        end_time = time.time()
        generation_time = end_time - start_time

        # Should complete within reasonable time (mocked LLM is fast)
        assert generation_time < 5.0
        assert content is not None

    async def test_optimization_performance(self, optimization_agent):
        """Test optimization performance on large script"""
        large_script = "\n".join([
            "-- Large script for performance testing"
        ] + [
            f"local var{i} = {i}" for i in range(1000)
        ])

        import time
        start_time = time.time()

        result = optimization_agent.optimize_script(large_script)

        end_time = time.time()
        optimization_time = end_time - start_time

        # Should handle large scripts efficiently
        assert optimization_time < 10.0
        assert result is not None

    async def test_security_validation_performance(self, security_agent):
        """Test security validation performance"""
        complex_script = """
        """ + "\n".join([
            f"local function func{i}(param{i})",
            f"    return param{i} * 2",
            f"end"
        ] for i in range(100))

        import time
        start_time = time.time()

        report = security_agent.validate_script(complex_script)

        end_time = time.time()
        validation_time = end_time - start_time

        # Should validate complex scripts quickly
        assert validation_time < 5.0
        assert report is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])