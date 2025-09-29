import pytest_asyncio
"""
Unit tests for the Validation Engine

Tests the comprehensive validation system for Roblox Lua scripts.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from core.validation.validation_engine import (
    ValidationEngine, ValidationRequest, ComprehensiveReport, ValidationStatus
)
from core.validation.educational_validator import GradeLevel, Subject, LearningObjective
from core.validation.lua_validator import ValidationResult, ValidationIssue, ValidationSeverity
from core.validation.security_analyzer import SecurityReport, SecurityThreat, SecurityFinding, ExploitType
from core.validation.quality_checker import QualityReport, QualityLevel, QualityMetrics
from core.validation.roblox_compliance import ComplianceReport, ComplianceLevel


class TestValidationEngine:
    """Test cases for ValidationEngine"""

    @pytest.fixture
    def validation_engine(self):
        """Create validation engine instance"""
        return ValidationEngine()

    @pytest.fixture
    def sample_lua_code(self):
        """Sample Lua code for testing"""
        return '''
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local function greetPlayer(player)
    print("Hello, " .. player.Name .. "!")
end

game.Players.PlayerAdded:Connect(greetPlayer)
        '''

    @pytest.fixture
    def validation_request(self, sample_lua_code):
        """Create sample validation request"""
        return ValidationRequest(
            script_code=sample_lua_code,
            script_name="test_script.lua",
            grade_level=GradeLevel.ELEMENTARY,
            subject=Subject.COMPUTER_SCIENCE,
            learning_objectives=[
                LearningObjective(
                    id="obj1",
                    description="Learn basic Roblox scripting",
                    grade_level=GradeLevel.ELEMENTARY,
                    subject=Subject.COMPUTER_SCIENCE,
                    bloom_level="understand"
                )
            ],
            educational_context=True,
            strict_mode=False,
            include_suggestions=True
        )

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_script_success(self, validation_engine, validation_request):
        """Test successful script validation"""
        # Mock all validators to return successful results
        with patch.object(validation_engine.lua_validator, 'validate_script') as mock_lua, \
             patch.object(validation_engine.security_analyzer, 'analyze_security') as mock_security, \
             patch.object(validation_engine.educational_validator, 'validate_educational_content') as mock_edu, \
             patch.object(validation_engine.quality_checker, 'check_quality') as mock_quality, \
             patch.object(validation_engine.compliance_checker, 'check_compliance') as mock_compliance:

            # Setup successful mocks
            mock_lua.return_value = ValidationResult(
                success=True,
                issues=[],
                syntax_valid=True,
                api_compatible=True,
                performance_score=90.0,
                memory_score=85.0,
                complexity_score=80.0,
                total_lines=10,
                function_count=2,
                variable_count=3
            )

            mock_security.return_value = SecurityReport(
                overall_score=95.0,
                threat_level=SecurityThreat.LOW,
                findings=[],
                remote_events_secure=True,
                input_validation_present=True,
                rate_limiting_present=True,
                authentication_checks=True,
                recommendations=[],
                compliant_with_standards=True
            )

            mock_edu.return_value = Mock(
                appropriate_for_grade=True,
                subject_aligned=True,
                learning_objectives_met=["obj1"],
                content_rating=Mock(value="appropriate"),
                accessibility_score=90.0,
                engagement_score=85.0,
                educational_value_score=88.0,
                issues=[],
                recommendations=[]
            )

            mock_quality.return_value = QualityReport(
                overall_score=85.0,
                quality_level=QualityLevel.GOOD,
                metrics=QualityMetrics(
                    lines_of_code=10, logical_lines=8, comment_lines=1, blank_lines=1,
                    function_count=2, complexity_score=80, maintainability_score=85,
                    readability_score=90, documentation_score=70, test_coverage=0
                ),
                issues=[],
                recommendations=[],
                best_practices_followed=[],
                areas_for_improvement=[]
            )

            mock_compliance.return_value = ComplianceReport(
                overall_compliance=ComplianceLevel.COMPLIANT,
                violations=[],
                compliant_areas=["proper_service_usage"],
                warnings=[],
                critical_issues=[],
                platform_ready=True,
                moderation_risk="low",
                recommendations=[]
            )

            # Run validation
            result = await validation_engine.validate_script(validation_request)

            # Assertions
            assert isinstance(result, ComprehensiveReport)
            assert result.script_name == "test_script.lua"
            assert result.overall_status == ValidationStatus.PASSED
            assert result.overall_score > 80.0
            assert result.deployment_ready is True
            assert result.educational_ready is True
            assert result.platform_compliant is True
            assert len(result.critical_issues) == 0

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_script_with_critical_issues(self, validation_engine, validation_request):
        """Test script validation with critical security issues"""
        # Mock security analyzer to return critical findings
        with patch.object(validation_engine.lua_validator, 'validate_script') as mock_lua, \
             patch.object(validation_engine.security_analyzer, 'analyze_security') as mock_security, \
             patch.object(validation_engine.educational_validator, 'validate_educational_content') as mock_edu, \
             patch.object(validation_engine.quality_checker, 'check_quality') as mock_quality, \
             patch.object(validation_engine.compliance_checker, 'check_compliance') as mock_compliance:

            # Setup mocks with critical security issue
            mock_lua.return_value = ValidationResult(
                success=True, issues=[], syntax_valid=True, api_compatible=True,
                performance_score=90.0, memory_score=85.0, complexity_score=80.0,
                total_lines=10, function_count=2, variable_count=3
            )

            mock_security.return_value = SecurityReport(
                overall_score=20.0,
                threat_level=SecurityThreat.CRITICAL,
                findings=[
                    SecurityFinding(
                        threat_level=SecurityThreat.CRITICAL,
                        exploit_type=ExploitType.CODE_INJECTION,
                        line_number=5,
                        column=1,
                        description="loadstring usage detected",
                        code_snippet="loadstring(code)()",
                        mitigation="Remove loadstring usage"
                    )
                ],
                remote_events_secure=False,
                input_validation_present=False,
                rate_limiting_present=False,
                authentication_checks=False,
                recommendations=["Remove dynamic code execution"],
                compliant_with_standards=False
            )

            mock_edu.return_value = Mock(
                appropriate_for_grade=True, subject_aligned=True, learning_objectives_met=["obj1"],
                content_rating=Mock(value="appropriate"), accessibility_score=90.0,
                engagement_score=85.0, educational_value_score=88.0, issues=[], recommendations=[]
            )

            mock_quality.return_value = QualityReport(
                overall_score=75.0, quality_level=QualityLevel.GOOD,
                metrics=QualityMetrics(
                    lines_of_code=10, logical_lines=8, comment_lines=1, blank_lines=1,
                    function_count=2, complexity_score=80, maintainability_score=85,
                    readability_score=90, documentation_score=70, test_coverage=0
                ),
                issues=[], recommendations=[], best_practices_followed=[], areas_for_improvement=[]
            )

            mock_compliance.return_value = ComplianceReport(
                overall_compliance=ComplianceLevel.COMPLIANT, violations=[], compliant_areas=[],
                warnings=[], critical_issues=[], platform_ready=True, moderation_risk="low", recommendations=[]
            )

            # Run validation
            result = await validation_engine.validate_script(validation_request)

            # Assertions
            assert result.overall_status == ValidationStatus.FAILED
            assert result.deployment_ready is False
            assert len(result.critical_issues) > 0
            assert "loadstring usage detected" in result.critical_issues

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validate_script_syntax_error(self, validation_engine, validation_request):
        """Test script validation with syntax errors"""
        # Update request with invalid Lua code
        validation_request.script_code = "function invalid_syntax( print('missing end')"

        with patch.object(validation_engine.lua_validator, 'validate_script') as mock_lua, \
             patch.object(validation_engine.security_analyzer, 'analyze_security') as mock_security, \
             patch.object(validation_engine.educational_validator, 'validate_educational_content') as mock_edu, \
             patch.object(validation_engine.quality_checker, 'check_quality') as mock_quality, \
             patch.object(validation_engine.compliance_checker, 'check_compliance') as mock_compliance:

            # Setup syntax error mock
            mock_lua.return_value = ValidationResult(
                success=False,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        line=1,
                        column=10,
                        message="Syntax error: unexpected symbol",
                        rule="syntax_error"
                    )
                ],
                syntax_valid=False,
                api_compatible=False,
                performance_score=0.0,
                memory_score=0.0,
                complexity_score=0.0,
                total_lines=1,
                function_count=0,
                variable_count=0
            )

            # Other mocks return neutral results
            mock_security.return_value = SecurityReport(
                overall_score=100.0, threat_level=SecurityThreat.LOW, findings=[],
                remote_events_secure=True, input_validation_present=True,
                rate_limiting_present=True, authentication_checks=True,
                recommendations=[], compliant_with_standards=True
            )

            mock_edu.return_value = Mock(
                appropriate_for_grade=True, subject_aligned=True, learning_objectives_met=[],
                content_rating=Mock(value="appropriate"), accessibility_score=50.0,
                engagement_score=50.0, educational_value_score=50.0, issues=[], recommendations=[]
            )

            mock_quality.return_value = QualityReport(
                overall_score=50.0, quality_level=QualityLevel.FAIR,
                metrics=QualityMetrics(
                    lines_of_code=1, logical_lines=1, comment_lines=0, blank_lines=0,
                    function_count=0, complexity_score=0, maintainability_score=50,
                    readability_score=50, documentation_score=0, test_coverage=0
                ),
                issues=[], recommendations=[], best_practices_followed=[], areas_for_improvement=[]
            )

            mock_compliance.return_value = ComplianceReport(
                overall_compliance=ComplianceLevel.COMPLIANT, violations=[], compliant_areas=[],
                warnings=[], critical_issues=[], platform_ready=True, moderation_risk="low", recommendations=[]
            )

            # Run validation
            result = await validation_engine.validate_script(validation_request)

            # Assertions
            assert result.overall_status == ValidationStatus.FAILED
            assert result.deployment_ready is False
            assert len(result.critical_issues) > 0
            assert "Syntax error" in str(result.critical_issues)

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_batch_validate(self, validation_engine):
        """Test batch validation of multiple scripts"""
        requests = [
            ValidationRequest(
                script_code="print('Script 1')",
                script_name="script1.lua",
                educational_context=False
            ),
            ValidationRequest(
                script_code="print('Script 2')",
                script_name="script2.lua",
                educational_context=False
            )
        ]

        with patch.object(validation_engine, 'validate_script') as mock_validate:
            # Mock successful validation for both scripts
            mock_validate.side_effect = [
                ComprehensiveReport(
                    script_name="script1.lua",
                    validation_timestamp=datetime.now().isoformat(),
                    validation_duration_ms=100.0,
                    overall_status=ValidationStatus.PASSED,
                    overall_score=85.0,
                    syntax_validation=Mock(),
                    security_analysis=Mock(),
                    educational_validation=None,
                    quality_assessment=Mock(),
                    compliance_check=Mock(),
                    critical_issues=[],
                    warnings=[],
                    recommendations=[],
                    auto_fix_suggestions=[],
                    scores={"syntax": 90.0, "security": 85.0},
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True
                ),
                ComprehensiveReport(
                    script_name="script2.lua",
                    validation_timestamp=datetime.now().isoformat(),
                    validation_duration_ms=120.0,
                    overall_status=ValidationStatus.PASSED,
                    overall_score=90.0,
                    syntax_validation=Mock(),
                    security_analysis=Mock(),
                    educational_validation=None,
                    quality_assessment=Mock(),
                    compliance_check=Mock(),
                    critical_issues=[],
                    warnings=[],
                    recommendations=[],
                    auto_fix_suggestions=[],
                    scores={"syntax": 95.0, "security": 90.0},
                    deployment_ready=True,
                    educational_ready=True,
                    platform_compliant=True
                )
            ]

            # Run batch validation
            results = await validation_engine.batch_validate(requests)

            # Assertions
            assert len(results) == 2
            assert all(isinstance(result, ComprehensiveReport) for result in results)
            assert results[0].script_name == "script1.lua"
            assert results[1].script_name == "script2.lua"
            assert mock_validate.call_count == 2

    def test_export_report_json(self, validation_engine):
        """Test exporting report as JSON"""
        # Create a minimal report
        report = ComprehensiveReport(
            script_name="test.lua",
            validation_timestamp=datetime.now().isoformat(),
            validation_duration_ms=100.0,
            overall_status=ValidationStatus.PASSED,
            overall_score=85.0,
            syntax_validation=Mock(),
            security_analysis=Mock(),
            educational_validation=None,
            quality_assessment=Mock(),
            compliance_check=Mock(),
            critical_issues=[],
            warnings=[],
            recommendations=[],
            auto_fix_suggestions=[],
            scores={"syntax": 90.0},
            deployment_ready=True,
            educational_ready=True,
            platform_compliant=True
        )

        # Export as JSON
        json_report = validation_engine.export_report(report, "json")

        # Assertions
        assert isinstance(json_report, str)
        assert "test.lua" in json_report
        assert "validation_timestamp" in json_report
        assert "overall_status" in json_report

    def test_export_report_summary(self, validation_engine):
        """Test exporting report as summary"""
        # Create a minimal report
        report = ComprehensiveReport(
            script_name="test.lua",
            validation_timestamp=datetime.now().isoformat(),
            validation_duration_ms=100.0,
            overall_status=ValidationStatus.PASSED,
            overall_score=85.0,
            syntax_validation=Mock(),
            security_analysis=Mock(),
            educational_validation=None,
            quality_assessment=Mock(),
            compliance_check=Mock(),
            critical_issues=["Critical issue 1"],
            warnings=["Warning 1"],
            recommendations=["Recommendation 1"],
            auto_fix_suggestions=[],
            scores={"syntax": 90.0, "security": 85.0},
            deployment_ready=True,
            educational_ready=True,
            platform_compliant=True
        )

        # Export as summary
        summary_report = validation_engine.export_report(report, "summary")

        # Assertions
        assert isinstance(summary_report, str)
        assert "test.lua" in summary_report
        assert "PASSED" in summary_report
        assert "85.0/100" in summary_report
        assert "Critical issue 1" in summary_report

    def test_get_validation_statistics(self, validation_engine):
        """Test getting validation statistics"""
        # Get initial statistics
        stats = validation_engine.get_validation_statistics()

        # Assertions
        assert isinstance(stats, dict)
        assert 'total_validations' in stats
        assert 'passed_validations' in stats
        assert 'failed_validations' in stats
        assert 'average_score' in stats
        assert 'common_issues' in stats

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validation_error_handling(self, validation_engine, validation_request):
        """Test error handling during validation"""
        with patch.object(validation_engine.lua_validator, 'validate_script') as mock_lua:
            # Mock validator to raise an exception
            mock_lua.side_effect = Exception("Validation engine failure")

            # Run validation
            result = await validation_engine.validate_script(validation_request)

            # Assertions
            assert result.overall_status == ValidationStatus.FAILED
            assert result.deployment_ready is False
            assert "Validation error" in str(result.critical_issues)

    def test_invalid_export_format(self, validation_engine):
        """Test invalid export format handling"""
        report = Mock()

        with pytest.raises(ValueError, match="Unsupported export format"):
            validation_engine.export_report(report, "invalid_format")

    @pytest.mark.asyncio
    @pytest.mark.asyncio
async def test_validation_without_educational_context(self, validation_engine):
        """Test validation without educational context"""
        request = ValidationRequest(
            script_code="print('Hello World')",
            script_name="simple.lua",
            educational_context=False
        )

        with patch.object(validation_engine.lua_validator, 'validate_script') as mock_lua, \
             patch.object(validation_engine.security_analyzer, 'analyze_security') as mock_security, \
             patch.object(validation_engine.quality_checker, 'check_quality') as mock_quality, \
             patch.object(validation_engine.compliance_checker, 'check_compliance') as mock_compliance:

            # Setup mocks
            mock_lua.return_value = ValidationResult(
                success=True, issues=[], syntax_valid=True, api_compatible=True,
                performance_score=90.0, memory_score=85.0, complexity_score=80.0,
                total_lines=1, function_count=0, variable_count=0
            )

            mock_security.return_value = SecurityReport(
                overall_score=95.0, threat_level=SecurityThreat.LOW, findings=[],
                remote_events_secure=True, input_validation_present=True,
                rate_limiting_present=True, authentication_checks=True,
                recommendations=[], compliant_with_standards=True
            )

            mock_quality.return_value = QualityReport(
                overall_score=85.0, quality_level=QualityLevel.GOOD,
                metrics=QualityMetrics(
                    lines_of_code=1, logical_lines=1, comment_lines=0, blank_lines=0,
                    function_count=0, complexity_score=80, maintainability_score=85,
                    readability_score=90, documentation_score=70, test_coverage=0
                ),
                issues=[], recommendations=[], best_practices_followed=[], areas_for_improvement=[]
            )

            mock_compliance.return_value = ComplianceReport(
                overall_compliance=ComplianceLevel.COMPLIANT, violations=[], compliant_areas=[],
                warnings=[], critical_issues=[], platform_ready=True, moderation_risk="low", recommendations=[]
            )

            # Run validation
            result = await validation_engine.validate_script(request)

            # Assertions
            assert result.educational_validation is None
            assert result.overall_status == ValidationStatus.PASSED
            assert 'educational' not in result.scores or result.scores['educational'] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])