"""
RobloxSecurityValidationAgent - Security Validation and Threat Detection

This agent performs comprehensive security validation of Roblox scripts,
detecting vulnerabilities, malicious patterns, and policy violations.
"""

import re
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from langchain.agents import AgentExecutor
from langchain.tools import Tool, StructuredTool
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from core.agents.base_agent import BaseAgent, AgentConfig, AgentState, TaskResult


class ThreatLevel(Enum):
    """Security threat levels"""
    CRITICAL = "critical"  # Immediate exploitation risk
    HIGH = "high"  # Significant security concern
    MEDIUM = "medium"  # Potential security issue
    LOW = "low"  # Minor security consideration
    INFO = "info"  # Informational finding


class VulnerabilityType(Enum):
    """Types of security vulnerabilities"""
    CODE_INJECTION = "code_injection"
    DATA_EXPOSURE = "data_exposure"
    AUTH_BYPASS = "authentication_bypass"
    INPUT_VALIDATION = "input_validation"
    MEMORY_LEAK = "memory_leak"
    RATE_LIMITING = "rate_limiting"
    ENCRYPTION = "encryption"
    PERMISSIONS = "permissions"
    NETWORK_SECURITY = "network_security"
    POLICY_VIOLATION = "policy_violation"


@dataclass
class SecurityVulnerability:
    """Represents a security vulnerability"""
    threat_level: ThreatLevel
    vulnerability_type: VulnerabilityType
    location: str  # File path or line number
    description: str
    impact: str
    remediation: str
    cve_reference: Optional[str] = None
    cvss_score: Optional[float] = None
    exploitable: bool = False
    false_positive_likelihood: float = 0.0


@dataclass
class SecurityReport:
    """Comprehensive security validation report"""
    scan_id: str
    timestamp: datetime
    vulnerabilities: List[SecurityVulnerability]
    risk_score: float  # 0-10 scale
    compliance_status: Dict[str, bool]
    recommendations: List[str]
    blocked_patterns: List[str]
    safe_patterns: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class RobloxSecurityValidationAgent(BaseAgent):
    """Agent for security validation of Roblox scripts and configurations"""

    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm: Optional[.* = None,
        strict_mode: bool = True
    ):
        # Create default config if not provided
        if not config:
            config = AgentConfig(
                name="RobloxSecurityValidator",
                model="gpt-4",
                temperature=0,  # Zero temperature for consistent security decisions
                system_prompt="""You are an expert Roblox security analyst.
                You identify vulnerabilities, malicious patterns, and policy violations in Luau scripts.
                Provide clear security assessments with risk scores and remediation guidance.""",
                verbose=True,
                memory_enabled=True
            )
        super().__init__(config)
        # Override llm if provided
        if llm is not None:
            self.llm = llm
        elif not self.llm:
            self.llm = from langchain_openai import ChatOpenAI(
                model="gpt-4",
                temperature=0
            )
        self.strict_mode = strict_mode
        self.vulnerability_database = self._load_vulnerability_database()
        self.blocked_patterns = self._load_blocked_patterns()
        self.compliance_rules = self._load_compliance_rules()

    def _load_vulnerability_database(self) -> Dict[str, Any]:
        """Load database of known vulnerabilities and patterns"""
        return {
            "dangerous_functions": {
                "loadstring": {
                    "threat_level": ThreatLevel.CRITICAL,
                    "type": VulnerabilityType.CODE_INJECTION,
                    "description": "Allows arbitrary code execution",
                    "cvss_score": 9.8
                },
                "getfenv": {
                    "threat_level": ThreatLevel.HIGH,
                    "type": VulnerabilityType.DATA_EXPOSURE,
                    "description": "Can expose environment variables",
                    "cvss_score": 7.5
                },
                "setfenv": {
                    "threat_level": ThreatLevel.HIGH,
                    "type": VulnerabilityType.CODE_INJECTION,
                    "description": "Can modify function environment",
                    "cvss_score": 7.5
                },
                "rawset": {
                    "threat_level": ThreatLevel.MEDIUM,
                    "type": VulnerabilityType.DATA_EXPOSURE,
                    "description": "Bypasses metatables",
                    "cvss_score": 5.3
                },
                "rawget": {
                    "threat_level": ThreatLevel.MEDIUM,
                    "type": VulnerabilityType.DATA_EXPOSURE,
                    "description": "Bypasses metatables",
                    "cvss_score": 5.3
                },
                "debug.": {
                    "threat_level": ThreatLevel.HIGH,
                    "type": VulnerabilityType.DATA_EXPOSURE,
                    "description": "Debug library access",
                    "cvss_score": 7.0
                }
            },
            "suspicious_patterns": {
                r"_G\[": "Global table manipulation",
                r"shared\[": "Shared table access",
                r"game\.Players\..*\.UserId": "User ID exposure",
                r"game:GetService\([\"']TeleportService": "Teleport service abuse",
                r"MarketplaceService:PromptPurchase": "Unauthorized purchases",
                r"HttpService:.*Request": "External HTTP requests",
                r"game\.Players\..*\.AccountAge": "Account age checking",
                r"string\.char\(": "Obfuscated strings",
                r"\\x[0-9a-fA-F]{2}": "Hex encoded strings",
                r"require\([\d]+\)": "Module by ID (potential backdoor)"
            },
            "authentication_patterns": {
                r"[\"']password[\"']": "Hardcoded password string",
                r"\bpassword\s*=\s*[\"']": "Hardcoded password variable",
                r"[\"']api[_-]?key[\"']": "Hardcoded API key string",
                r"\bapi[_-]?key\s*=\s*[\"']": "Hardcoded API key variable",
                r"[\"']token[\"']": "Hardcoded token string",
                r"\btoken\s*=\s*[\"']": "Hardcoded token variable",
                r"[\"']secret[\"']": "Hardcoded secret string",
                r"\bsecret\s*=\s*[\"']": "Hardcoded secret variable",
                r"Bearer\s+[\w-]+": "Bearer token exposure"
            },
            "data_exposure_patterns": {
                r"print\(.*UserId": "User ID logging",
                r"warn\(.*password": "Password logging",
                r"tostring\(.*private": "Private data conversion",
                r"JSONEncode.*sensitive": "Sensitive data serialization"
            }
        }

    def _load_blocked_patterns(self) -> Set[str]:
        """Load patterns that should be completely blocked"""
        return {
            "loadstring",
            "getfenv",
            "setfenv",
            "debug.getinfo",
            "debug.getlocal",
            "debug.setupvalue",
            "require(game:GetObjects",  # Asset injection
            "_G.require",
            "shared.require",
            "syn.",  # Exploit-specific
            "hookfunction",
            "getrawmetatable",
            "setrawmetatable",
            "getnamecallmethod",
            "newcclosure",
            "islclosure",
            "checkcaller"
        }

    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load Roblox compliance and policy rules"""
        return {
            "content_moderation": {
                "no_profanity": True,
                "no_personal_info": True,
                "no_external_links": True,
                "age_appropriate": True
            },
            "data_protection": {
                "no_pii_storage": True,
                "encrypted_transmission": True,
                "secure_storage": True,
                "data_minimization": True
            },
            "monetization": {
                "transparent_purchases": True,
                "no_scam_patterns": True,
                "proper_disclaimers": True
            },
            "performance": {
                "rate_limiting": True,
                "memory_management": True,
                "network_optimization": True
            }
        }

    def _scan_for_dangerous_functions(self, code: str) -> List[SecurityVulnerability]:
        """Scan code for dangerous function usage"""
        vulnerabilities = []
        lines = code.split('\n')

        for func_name, details in self.vulnerability_database["dangerous_functions"].items():
            pattern = re.compile(r'\b' + re.escape(func_name) + r'\b', re.IGNORECASE)

            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    vulnerabilities.append(SecurityVulnerability(
                        threat_level=details["threat_level"],
                        vulnerability_type=details["type"],
                        location=f"Line {i}",
                        description=f"Use of dangerous function '{func_name}': {details['description']}",
                        impact=f"CVSS Score: {details.get('cvss_score', 'N/A')}",
                        remediation=f"Remove or replace '{func_name}' with a safe alternative",
                        cvss_score=details.get("cvss_score"),
                        exploitable=True
                    ))

        return vulnerabilities

    def _scan_for_suspicious_patterns(self, code: str) -> List[SecurityVulnerability]:
        """Scan for suspicious code patterns"""
        vulnerabilities = []

        for pattern, description in self.vulnerability_database["suspicious_patterns"].items():
            matches = re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                vulnerabilities.append(SecurityVulnerability(
                    threat_level=ThreatLevel.MEDIUM,
                    vulnerability_type=VulnerabilityType.POLICY_VIOLATION,
                    location=f"Line {line_num}",
                    description=f"Suspicious pattern detected: {description}",
                    impact="Potential security or policy violation",
                    remediation="Review and validate this code pattern",
                    exploitable=False,
                    false_positive_likelihood=0.3
                ))

        return vulnerabilities

    def _scan_for_authentication_issues(self, code: str) -> List[SecurityVulnerability]:
        """Scan for authentication and credential issues"""
        vulnerabilities = []

        for pattern, description in self.vulnerability_database["authentication_patterns"].items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                vulnerabilities.append(SecurityVulnerability(
                    threat_level=ThreatLevel.HIGH,
                    vulnerability_type=VulnerabilityType.DATA_EXPOSURE,
                    location=f"Line {line_num}",
                    description=description,
                    impact="Credentials could be exposed in code",
                    remediation="Use secure configuration management instead of hardcoding",
                    exploitable=True
                ))

        return vulnerabilities

    def _scan_for_input_validation(self, code: str) -> List[SecurityVulnerability]:
        """Scan for input validation issues"""
        vulnerabilities = []

        # Check for RemoteEvent/RemoteFunction without validation
        remote_pattern = r"(RemoteEvent|RemoteFunction)\.OnServerEvent:Connect\(function\([^)]*\)(.*?)end\)"
        matches = re.finditer(remote_pattern, code, re.DOTALL)

        for match in matches:
            func_body = match.group(2)
            # Check if there's any validation
            if not any(keyword in func_body for keyword in ["if ", "assert", "type(", "typeof(", "tonumber", "tostring"]):
                line_num = code[:match.start()].count('\n') + 1
                vulnerabilities.append(SecurityVulnerability(
                    threat_level=ThreatLevel.HIGH,
                    vulnerability_type=VulnerabilityType.INPUT_VALIDATION,
                    location=f"Line {line_num}",
                    description="RemoteEvent/Function handler without input validation",
                    impact="Unvalidated input could lead to exploits",
                    remediation="Add input validation for all remote event parameters",
                    exploitable=True
                ))

        return vulnerabilities

    def _scan_for_rate_limiting(self, code: str) -> List[SecurityVulnerability]:
        """Check for rate limiting implementation"""
        vulnerabilities = []

        # Check for RemoteEvents without rate limiting
        if "RemoteEvent" in code or "RemoteFunction" in code:
            has_rate_limiting = any(pattern in code for pattern in [
                "debounce", "cooldown", "lastCall", "rateLimiter",
                "throttle", "os.clock()", "tick()", "time()"
            ])

            if not has_rate_limiting:
                vulnerabilities.append(SecurityVulnerability(
                    threat_level=ThreatLevel.MEDIUM,
                    vulnerability_type=VulnerabilityType.RATE_LIMITING,
                    location="Global",
                    description="No rate limiting detected for remote events",
                    impact="Service could be overwhelmed by rapid requests",
                    remediation="Implement rate limiting for all remote endpoints",
                    exploitable=True
                ))

        return vulnerabilities

    def _calculate_risk_score(self, vulnerabilities: List[SecurityVulnerability]) -> float:
        """Calculate overall risk score (0-10)"""
        if not vulnerabilities:
            return 0.0

        score = 0.0
        weights = {
            ThreatLevel.CRITICAL: 10.0,
            ThreatLevel.HIGH: 7.0,
            ThreatLevel.MEDIUM: 4.0,
            ThreatLevel.LOW: 2.0,
            ThreatLevel.INFO: 0.5
        }

        for vuln in vulnerabilities:
            vuln_score = weights.get(vuln.threat_level, 1.0)
            if vuln.exploitable:
                vuln_score *= 1.5
            if vuln.false_positive_likelihood > 0.5:
                vuln_score *= 0.5
            score += vuln_score

        # Normalize to 0-10 scale
        return min(10.0, score / len(vulnerabilities) * 2)

    def validate_script(
        self,
        code: str,
        script_type: str = "ServerScript",
        context: Optional[Dict[str, Any]] = None
    ) -> SecurityReport:
        """
        Perform comprehensive security validation on a Roblox script

        Args:
            code: The Luau script to validate
            script_type: Type of script (ServerScript, LocalScript, ModuleScript)
            context: Additional context for validation

        Returns:
            SecurityReport with findings and recommendations
        """
        scan_id = hashlib.sha256(f"{code}{datetime.now()}".encode()).hexdigest()[:16]
        vulnerabilities = []

        # Run all security scans
        vulnerabilities.extend(self._scan_for_dangerous_functions(code))
        vulnerabilities.extend(self._scan_for_suspicious_patterns(code))
        vulnerabilities.extend(self._scan_for_authentication_issues(code))
        vulnerabilities.extend(self._scan_for_input_validation(code))
        vulnerabilities.extend(self._scan_for_rate_limiting(code))

        # Check for blocked patterns
        blocked_found = []
        for pattern in self.blocked_patterns:
            if pattern.lower() in code.lower():
                blocked_found.append(pattern)
                vulnerabilities.append(SecurityVulnerability(
                    threat_level=ThreatLevel.CRITICAL,
                    vulnerability_type=VulnerabilityType.POLICY_VIOLATION,
                    location="Global",
                    description=f"Blocked pattern detected: {pattern}",
                    impact="This pattern is completely prohibited",
                    remediation=f"Remove all usage of {pattern}",
                    exploitable=True
                ))

        # Calculate risk score
        risk_score = self._calculate_risk_score(vulnerabilities)

        # Check compliance
        compliance_status = {
            "no_dangerous_functions": len([v for v in vulnerabilities
                if v.vulnerability_type == VulnerabilityType.CODE_INJECTION]) == 0,
            "input_validation": len([v for v in vulnerabilities
                if v.vulnerability_type == VulnerabilityType.INPUT_VALIDATION]) == 0,
            "no_hardcoded_credentials": len([v for v in vulnerabilities
                if "password" in v.description.lower() or "key" in v.description.lower()]) == 0,
            "rate_limiting": len([v for v in vulnerabilities
                if v.vulnerability_type == VulnerabilityType.RATE_LIMITING]) == 0,
            "roblox_tos_compliant": len(blocked_found) == 0
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities, script_type)

        # Identify safe patterns used
        safe_patterns = self._identify_safe_patterns(code)

        return SecurityReport(
            scan_id=scan_id,
            timestamp=datetime.now(),
            vulnerabilities=vulnerabilities,
            risk_score=risk_score,
            compliance_status=compliance_status,
            recommendations=recommendations,
            blocked_patterns=blocked_found,
            safe_patterns=safe_patterns,
            metadata={
                "script_type": script_type,
                "line_count": len(code.split('\n')),
                "scan_duration": "< 1s",
                "validator_version": "1.0.0"
            }
        )

    def _generate_recommendations(
        self,
        vulnerabilities: List[SecurityVulnerability],
        script_type: str
    ) -> List[str]:
        """Generate actionable security recommendations"""
        recommendations = []

        # Priority recommendations based on critical issues
        critical_vulns = [v for v in vulnerabilities if v.threat_level == ThreatLevel.CRITICAL]
        if critical_vulns:
            recommendations.append("🔴 CRITICAL: Address critical security vulnerabilities immediately")
            for vuln in critical_vulns[:3]:  # Top 3 critical
                recommendations.append(f"  - {vuln.remediation}")

        # Script type specific recommendations
        if script_type == "ServerScript":
            recommendations.append("✅ Validate all inputs from clients")
            recommendations.append("✅ Implement rate limiting for remote events")
            recommendations.append("✅ Use secure configuration management")
        elif script_type == "LocalScript":
            recommendations.append("⚠️  Never trust client-side validation alone")
            recommendations.append("⚠️  Avoid storing sensitive data on client")
            recommendations.append("⚠️  Minimize exposed remote endpoints")

        # General security recommendations
        if not vulnerabilities:
            recommendations.append("✅ No major security issues detected")
            recommendations.append("📋 Continue following security best practices")
        else:
            recommendations.append(f"📊 Total issues found: {len(vulnerabilities)}")
            recommendations.append("🔧 Run security validation after fixing issues")

        return recommendations

    def _identify_safe_patterns(self, code: str) -> List[str]:
        """Identify security best practices being used"""
        safe_patterns = []

        # Check for good security practices
        security_checks = {
            "type checking": r"type\(.*\)\s*==",
            "typeof validation": r"typeof\(.*\)\s*==",
            "assert statements": r"assert\(",
            "pcall error handling": r"pcall\(",
            "rate limiting": r"debounce|cooldown|throttle",
            "secure random": r"Random\.new\(\)",
            "parameter validation": r"if\s+not\s+.*then\s+return",
            "connection cleanup": r":Disconnect\(\)",
            "secure configuration": r"SecureConfiguration|ServerStorage:GetAttribute"
        }

        for practice, pattern in security_checks.items():
            if re.search(pattern, code, re.IGNORECASE):
                safe_patterns.append(practice)

        return safe_patterns

    def generate_security_report_markdown(self, report: SecurityReport) -> str:
        """Generate a markdown security report"""
        md = f"""# 🔒 Security Validation Report

**Scan ID**: {report.scan_id}
**Timestamp**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Risk Score**: {report.risk_score:.1f}/10.0

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total Vulnerabilities | {len(report.vulnerabilities)} |
| Critical Issues | {len([v for v in report.vulnerabilities if v.threat_level == ThreatLevel.CRITICAL])} |
| High Issues | {len([v for v in report.vulnerabilities if v.threat_level == ThreatLevel.HIGH])} |
| Blocked Patterns | {len(report.blocked_patterns)} |
| Safe Patterns Detected | {len(report.safe_patterns)} |

## ⚠️  Vulnerabilities Found

"""
        # Group vulnerabilities by threat level
        for level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH, ThreatLevel.MEDIUM, ThreatLevel.LOW]:
            level_vulns = [v for v in report.vulnerabilities if v.threat_level == level]
            if level_vulns:
                md += f"### {level.value.upper()} Priority\n\n"
                for vuln in level_vulns:
                    md += f"**{vuln.vulnerability_type.value}** ({vuln.location})\n"
                    md += f"- Description: {vuln.description}\n"
                    md += f"- Impact: {vuln.impact}\n"
                    md += f"- Remediation: {vuln.remediation}\n"
                    if vuln.cvss_score:
                        md += f"- CVSS Score: {vuln.cvss_score}\n"
                    md += "\n"

        md += "## ✅ Compliance Status\n\n"
        for rule, passed in report.compliance_status.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            md += f"- {rule.replace('_', ' ').title()}: {status}\n"

        md += "\n## 📋 Recommendations\n\n"
        for rec in report.recommendations:
            md += f"{rec}\n"

        if report.safe_patterns:
            md += "\n## ✅ Security Best Practices Detected\n\n"
            for pattern in report.safe_patterns:
                md += f"- {pattern}\n"

        md += "\n---\n*Generated by RobloxSecurityValidationAgent v1.0.0*"
        return md

    def generate_fix_suggestions(self, vulnerability: SecurityVulnerability) -> str:
        """Generate specific fix suggestions for a vulnerability"""
        fixes = {
            VulnerabilityType.CODE_INJECTION: """
-- Replace loadstring with secure template execution
local TemplateExecutor = require(game.ServerStorage.TemplateExecutor)
local success, result = TemplateExecutor:ExecuteTemplate(templateId, params)
""",
            VulnerabilityType.INPUT_VALIDATION: """
-- Add input validation
local function validateInput(input)
    assert(type(input) == "string", "Invalid input type")
    assert(#input <= 100, "Input too long")
    assert(not string.match(input, "[<>]"), "Invalid characters")
    return true
end

RemoteEvent.OnServerEvent:Connect(function(player, input)
    if not validateInput(input) then
        return
    end
    -- Process validated input
end)
""",
            VulnerabilityType.RATE_LIMITING: """
-- Implement rate limiting
local cooldowns = {}
local COOLDOWN_TIME = 1 -- seconds

RemoteEvent.OnServerEvent:Connect(function(player, ...)
    local userId = player.UserId
    local now = tick()

    if cooldowns[userId] and now - cooldowns[userId] < COOLDOWN_TIME then
        return -- Rate limited
    end

    cooldowns[userId] = now
    -- Process request
end)
""",
            VulnerabilityType.DATA_EXPOSURE: """
-- Use secure configuration management
local SecureConfig = require(game.ServerScriptService.SecureConfigurationManager)
local apiKey = SecureConfig:getSecureValue("API_KEY")
-- Never hardcode sensitive values
"""
        }

        return fixes.get(vulnerability.vulnerability_type, "Review and fix based on security best practices")

    def execute(self, task: str) -> str:
        """Execute security validation task"""
        prompt = f"""
        As a Roblox security expert, analyze the following security concern:

        Task: {task}

        Provide:
        1. Security assessment
        2. Potential vulnerabilities
        3. Remediation steps
        4. Best practices to follow

        Focus on Roblox-specific security considerations.
        """

        response = self.llm.predict(prompt)
        return response

    async def _process_task(self, state: AgentState) -> TaskResult:
        """Process security validation task"""
        # Extract script and settings from state context
        context = state.get("context", {})
        script_code = context.get("script_code", "")
        script_type = context.get("script_type", "ServerScript")
        strict_mode = context.get("strict_mode", True)

        if not script_code:
            return TaskResult(
                success=False,
                error="No script provided for validation",
                message="Script code is required"
            )

        try:
            # Perform security validation
            report = self.validate_script(script_code, script_type)

            # Generate markdown report
            report_markdown = self.generate_security_report_markdown(report)

            return TaskResult(
                success=True,
                result={
                    "scan_id": report.scan_id,
                    "risk_score": report.risk_score,
                    "vulnerabilities": [
                        {
                            "threat_level": vuln.threat_level.value,
                            "type": vuln.vulnerability_type.value,
                            "location": vuln.location,
                            "description": vuln.description,
                            "impact": vuln.impact,
                            "remediation": vuln.remediation,
                            "cvss_score": vuln.cvss_score,
                            "exploitable": vuln.exploitable
                        }
                        for vuln in report.vulnerabilities
                    ],
                    "compliance_status": report.compliance_status,
                    "recommendations": report.recommendations,
                    "blocked_patterns": list(report.blocked_patterns),
                    "safe_patterns": list(report.safe_patterns),
                    "report_markdown": report_markdown
                },
                message=f"Security validation complete: Risk score {report.risk_score}/10"
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error=str(e),
                message="Security validation failed"
            )


# Example usage
if __name__ == "__main__":
    # Example vulnerable script
    vulnerable_script = """
    -- Admin panel with security issues
    local admins = {"Player1", "Player2"}
    local password = "admin123"  -- Hardcoded password

    local RemoteEvent = game.ReplicatedStorage.AdminEvent

    RemoteEvent.OnServerEvent:Connect(function(player, command)
        -- No input validation!
        if command == "execute" then
            loadstring(player.Data.Value)()  -- Critical vulnerability!
        end

        -- No rate limiting
        if command == "kick" then
            game.Players[player.Target.Value]:Kick()
        end
    end)

    -- Dangerous global access
    _G.adminPassword = password

    -- No connection cleanup
    while true do
        wait(0.1)
        print(game.Players.LocalPlayer.UserId)  -- PII exposure
    end
    """

    validator = RobloxSecurityValidationAgent()
    report = validator.validate_script(vulnerable_script, "ServerScript")

    print("Security Report:")
    print(validator.generate_security_report_markdown(report))

    if report.vulnerabilities:
        print("\n\nFix Suggestions:")
        for vuln in report.vulnerabilities[:3]:
            print(f"\n{vuln.description}:")
            print(validator.generate_fix_suggestions(vuln))