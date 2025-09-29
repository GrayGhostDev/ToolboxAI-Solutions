"""
Simple integration tests for Roblox AI Agent Suite

Tests basic functionality of the Roblox agents.
"""

import pytest
from unittest.mock import Mock, patch


def test_roblox_agents_import():
    """Test that all Roblox agents can be imported"""
    try:
        from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent
        from core.agents.roblox.roblox_script_optimization_agent import RobloxScriptOptimizationAgent
        from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

        assert RobloxContentGenerationAgent is not None
        assert RobloxScriptOptimizationAgent is not None
        assert RobloxSecurityValidationAgent is not None

    except ImportError as e:
        pytest.fail(f"Failed to import Roblox agents: {e}")


def test_content_generation_agent_creation():
    """Test creating a content generation agent"""
    from core.agents.roblox.roblox_content_generation_agent import RobloxContentGenerationAgent

    mock_llm = Mock()
    agent = RobloxContentGenerationAgent(llm=mock_llm)

    assert agent.name == "RobloxContentGenerationAgent"
    assert agent.llm is mock_llm


def test_optimization_agent_creation():
    """Test creating an optimization agent"""
    from core.agents.roblox.roblox_script_optimization_agent import (
        RobloxScriptOptimizationAgent,
        OptimizationLevel
    )

    mock_llm = Mock()
    agent = RobloxScriptOptimizationAgent(llm=mock_llm)

    assert agent.name == "RobloxScriptOptimizer"
    assert agent.optimization_level == OptimizationLevel.BALANCED
    assert agent.llm is mock_llm


def test_security_agent_creation():
    """Test creating a security validation agent"""
    from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

    mock_llm = Mock()
    agent = RobloxSecurityValidationAgent(llm=mock_llm)

    assert agent.name == "RobloxSecurityValidator"
    assert agent.strict_mode is True
    assert agent.llm is mock_llm


def test_optimization_agent_analyze_performance():
    """Test performance analysis functionality"""
    from core.agents.roblox.roblox_script_optimization_agent import RobloxScriptOptimizationAgent

    mock_llm = Mock()
    agent = RobloxScriptOptimizationAgent(llm=mock_llm)

    vulnerable_script = """
    while true do
        wait()  -- Bad practice
        print("Hello")
    end
    """

    issues = agent._analyze_script_performance(vulnerable_script)

    assert len(issues) > 0
    assert any("wait()" in issue.description for issue in issues)


def test_security_agent_detect_vulnerabilities():
    """Test vulnerability detection functionality"""
    from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

    mock_llm = Mock()
    agent = RobloxSecurityValidationAgent(llm=mock_llm)

    vulnerable_script = """
    local password = "admin123"  -- Hardcoded password
    loadstring(data)()  -- Critical vulnerability
    """

    vulnerabilities = agent._scan_for_dangerous_functions(vulnerable_script)
    assert len(vulnerabilities) > 0

    auth_issues = agent._scan_for_authentication_issues(vulnerable_script)
    assert len(auth_issues) > 0

    # Check that loadstring is detected
    assert any("loadstring" in v.description for v in vulnerabilities)
    # Check that hardcoded password is detected
    assert any("password" in v.description.lower() for v in auth_issues)


def test_security_report_generation():
    """Test security report generation"""
    from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

    mock_llm = Mock()
    agent = RobloxSecurityValidationAgent(llm=mock_llm)

    test_script = """
    -- Simple test script
    local Players = game:GetService("Players")

    Players.PlayerAdded:Connect(function(player)
        print("Player joined: " .. player.Name)
    end)
    """

    report = agent.validate_script(test_script, "ServerScript")

    assert report is not None
    assert hasattr(report, 'risk_score')
    assert hasattr(report, 'vulnerabilities')
    assert hasattr(report, 'compliance_status')
    assert hasattr(report, 'recommendations')

    # Safe script should have low risk score
    assert report.risk_score < 5.0


def test_optimization_result_generation():
    """Test optimization result generation"""
    from core.agents.roblox.roblox_script_optimization_agent import (
        RobloxScriptOptimizationAgent,
        OptimizationLevel
    )

    mock_llm = Mock()
    agent = RobloxScriptOptimizationAgent(llm=mock_llm)

    test_script = """
    for i = 1, #myTable do
        local item = myTable[i]
        process(item)
    end
    """

    result = agent.optimize_script(test_script, OptimizationLevel.CONSERVATIVE)

    assert result is not None
    assert hasattr(result, 'original_code')
    assert hasattr(result, 'optimized_code')
    assert hasattr(result, 'issues_found')
    assert hasattr(result, 'metrics')
    assert result.optimization_level == OptimizationLevel.CONSERVATIVE


def test_agent_integration_pipeline():
    """Test integration between multiple agents"""
    from core.agents.roblox.roblox_script_optimization_agent import RobloxScriptOptimizationAgent
    from core.agents.roblox.roblox_security_validation_agent import RobloxSecurityValidationAgent

    mock_llm = Mock()
    mock_llm.predict.return_value = "-- Generated educational content"

    optimization_agent = RobloxScriptOptimizationAgent(llm=mock_llm)
    security_agent = RobloxSecurityValidationAgent(llm=mock_llm)

    # Sample script to process
    script = """
    -- Educational game script
    local Players = game:GetService("Players")

    local function welcomePlayer(player)
        print("Welcome " .. player.Name)
    end

    Players.PlayerAdded:Connect(welcomePlayer)
    """

    # Optimize the script
    opt_result = optimization_agent.optimize_script(script)

    # Validate security of optimized script
    sec_report = security_agent.validate_script(opt_result.optimized_code)

    # Verify pipeline worked
    assert opt_result.optimized_code is not None
    assert sec_report.risk_score < 7.0  # Should be relatively safe
    assert len(sec_report.vulnerabilities) == 0 or all(
        v.threat_level.value != "critical" for v in sec_report.vulnerabilities
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])