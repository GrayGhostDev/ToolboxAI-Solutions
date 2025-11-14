"""
Security Analysis for Roblox Lua Scripts

Comprehensive security validation including exploit detection,
remote event security, and vulnerability assessment.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SecurityThreat(Enum):
    """Security threat levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExploitType(Enum):
    """Types of exploits that can be detected"""

    CODE_INJECTION = "code_injection"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    REMOTE_EXPLOIT = "remote_exploit"
    MEMORY_MANIPULATION = "memory_manipulation"
    ENVIRONMENT_MANIPULATION = "environment_manipulation"
    ANTI_CHEAT_BYPASS = "anti_cheat_bypass"
    DATA_LEAK = "data_leak"


@dataclass
class SecurityFinding:
    """Represents a security finding in the code"""

    threat_level: SecurityThreat
    exploit_type: ExploitType
    line_number: int
    column: int
    description: str
    code_snippet: str
    cve_reference: Optional[str] = None
    mitigation: Optional[str] = None
    confidence: float = 1.0


@dataclass
class SecurityReport:
    """Complete security analysis report"""

    overall_score: float  # 0-100, higher is safer
    threat_level: SecurityThreat
    findings: list[SecurityFinding]
    remote_events_secure: bool
    input_validation_present: bool
    rate_limiting_present: bool
    authentication_checks: bool
    recommendations: list[str]
    compliant_with_standards: bool


class SecurityAnalyzer:
    """
    Advanced security analyzer for Roblox Lua scripts
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Critical exploit patterns
        self.critical_patterns = {
            r"loadstring\s*\(": {
                "type": ExploitType.CODE_INJECTION,
                "description": "Dynamic code execution can lead to arbitrary code execution",
                "mitigation": "Remove loadstring usage or use pre-compiled functions",
            },
            r"getfenv\s*\(": {
                "type": ExploitType.ENVIRONMENT_MANIPULATION,
                "description": "Environment manipulation can bypass security measures",
                "mitigation": "Avoid getfenv or implement proper sandboxing",
            },
            r"setfenv\s*\(": {
                "type": ExploitType.ENVIRONMENT_MANIPULATION,
                "description": "Environment manipulation can alter global state",
                "mitigation": "Use module patterns instead of environment manipulation",
            },
            r"debug\.\w+": {
                "type": ExploitType.PRIVILEGE_ESCALATION,
                "description": "Debug library can be used for privilege escalation",
                "mitigation": "Remove debug library usage in production",
            },
            r"rawget\s*\(.*_G": {
                "type": ExploitType.MEMORY_MANIPULATION,
                "description": "Direct global table access can bypass metamethods",
                "mitigation": "Use proper accessor patterns",
            },
            r"rawset\s*\(.*_G": {
                "type": ExploitType.MEMORY_MANIPULATION,
                "description": "Direct global table modification can corrupt state",
                "mitigation": "Use proper setter patterns",
            },
        }

        # High-risk patterns
        self.high_risk_patterns = {
            r"while\s+true\s+do\s*(?!.*wait|.*yield)": {
                "type": ExploitType.ANTI_CHEAT_BYPASS,
                "description": "Infinite loop without yield can cause server lag/crash",
                "mitigation": "Add wait() or task.wait() in loops",
            },
            r"game:Shutdown\s*\(": {
                "type": ExploitType.PRIVILEGE_ESCALATION,
                "description": "Server shutdown can be used for griefing",
                "mitigation": "Remove server shutdown calls or add proper authorization",
            },
            r"Players:GetPlayers\s*\(\s*\)\s*\[\s*1\s*\]\s*:Kick": {
                "type": ExploitType.PRIVILEGE_ESCALATION,
                "description": "Unauthorized player kicking detected",
                "mitigation": "Add proper permission checks before kicking players",
            },
            r"HttpService:RequestAsync\s*\([^)]*http://(?!127\.0\.0\.1|localhost)": {
                "type": ExploitType.DATA_LEAK,
                "description": "External HTTP requests can leak data",
                "mitigation": "Validate and restrict external HTTP destinations",
            },
        }

        # Medium-risk patterns
        self.medium_risk_patterns = {
            r"RemoteEvent\s*:\s*FireClient\s*\([^)]*\)\s*(?!--.*validation)": {
                "type": ExploitType.REMOTE_EXPLOIT,
                "description": "RemoteEvent without apparent input validation",
                "mitigation": "Add input validation and rate limiting",
            },
            r"RemoteFunction\s*:\s*InvokeClient\s*\([^)]*\)\s*(?!--.*validation)": {
                "type": ExploitType.REMOTE_EXPLOIT,
                "description": "RemoteFunction without apparent input validation",
                "mitigation": "Add input validation and error handling",
            },
            r"Players\.PlayerAdded\s*:\s*Connect\s*\([^)]*\)\s*(?!--.*auth)": {
                "type": ExploitType.PRIVILEGE_ESCALATION,
                "description": "Player join handler without authentication checks",
                "mitigation": "Add player authentication and validation",
            },
        }

        # Low-risk patterns
        self.low_risk_patterns = {
            r"print\s*\([^)]*password[^)]*\)": {
                "type": ExploitType.DATA_LEAK,
                "description": "Potential password logging detected",
                "mitigation": "Remove sensitive data from print statements",
            },
            r"warn\s*\([^)]*token[^)]*\)": {
                "type": ExploitType.DATA_LEAK,
                "description": "Potential token logging detected",
                "mitigation": "Remove sensitive data from warn statements",
            },
        }

        # Security best practices patterns
        self.security_patterns = {
            "rate_limiting": r"local\s+lastAction.*tick\(\)",
            "input_validation": r'if\s+type\s*\([^)]+\)\s*[=!~]+\s*["\']',
            "permission_check": r"if\s+.*player.*UserId.*then",
            "authentication": r"if\s+.*authenticate.*then",
            "sanitization": r'string\.gsub\s*\([^)]*[<>&"\']\s*,',
            "rate_limit_check": r"if\s+.*cooldown.*then",
            "whitelist_check": r"if\s+.*whitelist.*then",
        }

        # Remote event security patterns
        self.remote_security_patterns = {
            "has_rate_limiting": r"local\s+.*cooldown|rate.*limit",
            "has_input_validation": r"if\s+type\s*\([^)]+\)\s*~=",
            "has_permission_check": r"if\s+.*player.*UserId",
            "has_sanity_check": r"if\s+.*and.*<.*then",
            "disconnects_events": r"\.Disconnect\s*\(\s*\)",
        }

        # Known vulnerability signatures
        self.vulnerability_signatures = {
            "exploitable_loadstring": r"loadstring\s*\(\s*.*HttpService.*RequestAsync",
            "unsafe_remote_eval": r"RemoteFunction.*loadstring",
            "privilege_bypass": r"getfenv.*_G.*game\.Players",
            "memory_corruption": r"rawset.*getmetatable",
        }

    def analyze_security(self, lua_code: str, script_name: str = "unknown") -> SecurityReport:
        """
        Perform comprehensive security analysis of Lua code

        Args:
            lua_code: The Lua code to analyze
            script_name: Name of the script for reporting

        Returns:
            SecurityReport with all security findings
        """
        findings = []

        # Analyze critical threats
        self._analyze_patterns(lua_code, self.critical_patterns, SecurityThreat.CRITICAL, findings)

        # Analyze high-risk threats
        self._analyze_patterns(lua_code, self.high_risk_patterns, SecurityThreat.HIGH, findings)

        # Analyze medium-risk threats
        self._analyze_patterns(lua_code, self.medium_risk_patterns, SecurityThreat.MEDIUM, findings)

        # Analyze low-risk threats
        self._analyze_patterns(lua_code, self.low_risk_patterns, SecurityThreat.LOW, findings)

        # Analyze known vulnerability signatures
        self._analyze_vulnerability_signatures(lua_code, findings)

        # Check remote event security
        remote_events_secure = self._analyze_remote_security(lua_code, findings)

        # Check for security best practices
        security_practices = self._check_security_practices(lua_code)

        # Calculate overall security score
        overall_score = self._calculate_security_score(findings, security_practices)

        # Determine overall threat level
        threat_level = self._determine_threat_level(findings)

        # Generate recommendations
        recommendations = self._generate_recommendations(findings, security_practices)

        # Check compliance with security standards
        compliant = self._check_compliance(findings, security_practices)

        return SecurityReport(
            overall_score=overall_score,
            threat_level=threat_level,
            findings=findings,
            remote_events_secure=remote_events_secure,
            input_validation_present=security_practices.get("input_validation", False),
            rate_limiting_present=security_practices.get("rate_limiting", False),
            authentication_checks=security_practices.get("authentication", False),
            recommendations=recommendations,
            compliant_with_standards=compliant,
        )

    def _analyze_patterns(
        self,
        lua_code: str,
        patterns: dict,
        threat_level: SecurityThreat,
        findings: list[SecurityFinding],
    ):
        """Analyze code against security patterns"""
        lines = lua_code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, details in patterns.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    finding = SecurityFinding(
                        threat_level=threat_level,
                        exploit_type=details["type"],
                        line_number=line_num,
                        column=match.start() + 1,
                        description=details["description"],
                        code_snippet=line.strip(),
                        mitigation=details["mitigation"],
                        confidence=0.9,
                    )
                    findings.append(finding)

    def _analyze_vulnerability_signatures(self, lua_code: str, findings: list[SecurityFinding]):
        """Analyze code for known vulnerability signatures"""
        for signature_name, pattern in self.vulnerability_signatures.items():
            matches = re.finditer(pattern, lua_code, re.IGNORECASE | re.DOTALL)
            for match in matches:
                line_num = lua_code[: match.start()].count("\n") + 1

                finding = SecurityFinding(
                    threat_level=SecurityThreat.CRITICAL,
                    exploit_type=ExploitType.CODE_INJECTION,
                    line_number=line_num,
                    column=match.start() - lua_code.rfind("\n", 0, match.start()),
                    description=f"Known vulnerability signature detected: {signature_name}",
                    code_snippet=(
                        match.group(0)[:100] + "..."
                        if len(match.group(0)) > 100
                        else match.group(0)
                    ),
                    mitigation="Remove or replace with secure implementation",
                    confidence=0.95,
                )
                findings.append(finding)

    def _analyze_remote_security(self, lua_code: str, findings: list[SecurityFinding]) -> bool:
        """Analyze RemoteEvent/RemoteFunction security"""
        has_remote_events = bool(re.search(r"RemoteEvent|RemoteFunction", lua_code, re.IGNORECASE))

        if not has_remote_events:
            return True  # No remote events, so secure by default

        security_checks = {}
        for check_name, pattern in self.remote_security_patterns.items():
            security_checks[check_name] = bool(re.search(pattern, lua_code, re.IGNORECASE))

        # Check for insecure remote event handlers
        remote_handlers = re.finditer(
            r"(RemoteEvent|RemoteFunction).*OnServer(Event|Invoke)",
            lua_code,
            re.IGNORECASE | re.DOTALL,
        )

        for match in remote_handlers:
            line_num = lua_code[: match.start()].count("\n") + 1

            # Extract handler code (simplified)
            handler_start = match.end()
            handler_code = lua_code[handler_start : handler_start + 500]  # Look ahead 500 chars

            # Check for security measures in handler
            has_validation = bool(re.search(r"if\s+type\s*\(", handler_code, re.IGNORECASE))
            has_rate_limit = bool(re.search(r"tick\(\)|cooldown|rate", handler_code, re.IGNORECASE))
            has_permission = bool(
                re.search(r"player.*UserId|permission|auth", handler_code, re.IGNORECASE)
            )

            if not (has_validation and has_rate_limit and has_permission):
                threat_level = SecurityThreat.HIGH if not has_validation else SecurityThreat.MEDIUM

                finding = SecurityFinding(
                    threat_level=threat_level,
                    exploit_type=ExploitType.REMOTE_EXPLOIT,
                    line_number=line_num,
                    column=1,
                    description="Remote handler lacks proper security measures",
                    code_snippet=match.group(0),
                    mitigation="Add input validation, rate limiting, and permission checks",
                    confidence=0.8,
                )
                findings.append(finding)

        # Overall remote security assessment
        required_checks = [
            "has_input_validation",
            "has_rate_limiting",
            "has_permission_check",
        ]
        secure_count = sum(1 for check in required_checks if security_checks.get(check, False))

        return secure_count >= 2  # At least 2 out of 3 security measures

    def _check_security_practices(self, lua_code: str) -> dict[str, bool]:
        """Check for security best practices"""
        practices = {}

        for practice_name, pattern in self.security_patterns.items():
            practices[practice_name] = bool(re.search(pattern, lua_code, re.IGNORECASE))

        return practices

    def _calculate_security_score(
        self, findings: list[SecurityFinding], practices: dict[str, bool]
    ) -> float:
        """Calculate overall security score (0-100)"""
        base_score = 100.0

        # Deduct points for findings
        for finding in findings:
            if finding.threat_level == SecurityThreat.CRITICAL:
                base_score -= 25 * finding.confidence
            elif finding.threat_level == SecurityThreat.HIGH:
                base_score -= 15 * finding.confidence
            elif finding.threat_level == SecurityThreat.MEDIUM:
                base_score -= 10 * finding.confidence
            elif finding.threat_level == SecurityThreat.LOW:
                base_score -= 5 * finding.confidence

        # Add points for good practices
        practice_bonus = sum(5 for practice, present in practices.items() if present)
        base_score = min(100.0, base_score + practice_bonus)

        return max(0.0, base_score)

    def _determine_threat_level(self, findings: list[SecurityFinding]) -> SecurityThreat:
        """Determine overall threat level"""
        if any(f.threat_level == SecurityThreat.CRITICAL for f in findings):
            return SecurityThreat.CRITICAL
        elif any(f.threat_level == SecurityThreat.HIGH for f in findings):
            return SecurityThreat.HIGH
        elif any(f.threat_level == SecurityThreat.MEDIUM for f in findings):
            return SecurityThreat.MEDIUM
        else:
            return SecurityThreat.LOW

    def _generate_recommendations(
        self, findings: list[SecurityFinding], practices: dict[str, bool]
    ) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        # Specific recommendations based on findings
        finding_types = set(f.exploit_type for f in findings)

        if ExploitType.CODE_INJECTION in finding_types:
            recommendations.append("Remove dynamic code execution (loadstring, eval)")

        if ExploitType.REMOTE_EXPLOIT in finding_types:
            recommendations.append("Implement comprehensive input validation for remote events")
            recommendations.append("Add rate limiting to prevent spam attacks")

        if ExploitType.PRIVILEGE_ESCALATION in finding_types:
            recommendations.append("Add proper authorization checks for privileged operations")

        if ExploitType.ENVIRONMENT_MANIPULATION in finding_types:
            recommendations.append("Avoid environment manipulation or implement proper sandboxing")

        # Recommendations based on missing practices
        if not practices.get("rate_limiting", False):
            recommendations.append("Implement rate limiting for user actions")

        if not practices.get("input_validation", False):
            recommendations.append("Add comprehensive input validation")

        if not practices.get("authentication", False):
            recommendations.append("Implement user authentication and authorization")

        if not practices.get("sanitization", False):
            recommendations.append("Sanitize user input to prevent injection attacks")

        # General recommendations
        recommendations.extend(
            [
                "Follow the principle of least privilege",
                "Regularly update and patch dependencies",
                "Implement logging and monitoring for security events",
                "Use secure coding practices and code reviews",
            ]
        )

        return list(set(recommendations))  # Remove duplicates

    def _check_compliance(
        self, findings: list[SecurityFinding], practices: dict[str, bool]
    ) -> bool:
        """Check compliance with security standards"""
        # No critical or high-risk findings
        has_serious_issues = any(
            f.threat_level in [SecurityThreat.CRITICAL, SecurityThreat.HIGH] for f in findings
        )

        # Must have basic security practices
        required_practices = ["input_validation", "rate_limiting"]
        has_required_practices = any(
            practices.get(practice, False) for practice in required_practices
        )

        return not has_serious_issues and has_required_practices

    def generate_secure_template(self, template_type: str) -> str:
        """Generate secure code templates"""
        templates = {
            "remote_event": """
-- Secure RemoteEvent Template
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local remoteEvent = Instance.new("RemoteEvent")
remoteEvent.Name = "SecureRemoteEvent"
remoteEvent.Parent = ReplicatedStorage

-- Rate limiting
local playerCooldowns = {}
local COOLDOWN_TIME = 1 -- seconds

-- Input validation
local function validateInput(input)
    if type(input) ~= "string" then
        return false
    end
    if #input > 100 then -- Max length
        return false
    end
    -- Add more validation as needed
    return true
end

-- Permission check
local function hasPermission(player, action)
    -- Implement your permission logic
    return player and player.Parent == Players
end

remoteEvent.OnServerEvent:Connect(function(player, action, data)
    -- Rate limiting
    local userId = player.UserId
    local lastTime = playerCooldowns[userId] or 0
    if tick() - lastTime < COOLDOWN_TIME then
        return -- Rate limited
    end
    playerCooldowns[userId] = tick()

    -- Input validation
    if not validateInput(action) or not validateInput(data) then
        warn("Invalid input from", player.Name)
        return
    end

    -- Permission check
    if not hasPermission(player, action) then
        warn("Unauthorized action from", player.Name)
        return
    end

    -- Process the action safely
    print(player.Name, "performed action:", action)
end)
            """,
            "data_validation": """
-- Secure Data Validation Module
local ValidationModule = {}

-- Whitelist of allowed characters
local ALLOWED_CHARS = "^[A-Za-z0-9%s%.,%!%?%-_'\"]+$"

function ValidationModule.validateString(input, maxLength)
    maxLength = maxLength or 100

    if type(input) ~= "string" then
        return false, "Input must be a string"
    end

    if #input > maxLength then
        return false, "Input too long"
    end

    if not string.match(input, ALLOWED_CHARS) then
        return false, "Input contains invalid characters"
    end

    return true
end

function ValidationModule.sanitizeString(input)
    if type(input) ~= "string" then
        return ""
    end

    -- Remove potentially dangerous patterns
    input = string.gsub(input, "<[^>]+>", "") -- HTML tags
    input = string.gsub(input, "[<>&\"']", "") -- Special chars

    return input
end

return ValidationModule
            """,
        }

        return templates.get(template_type, "# Template not found")

    def get_security_checklist(self) -> dict[str, list[str]]:
        """Get security checklist for developers"""
        return {
            "Input Validation": [
                "Validate all user inputs on the server side",
                "Use whitelists instead of blacklists when possible",
                "Limit input length and format",
                "Sanitize strings before processing",
            ],
            "Remote Events": [
                "Implement rate limiting for all remote events",
                "Add permission checks before processing requests",
                "Validate all parameters on the server",
                "Use secure patterns for client-server communication",
            ],
            "Authentication": [
                "Verify player identity for sensitive operations",
                "Implement proper authorization checks",
                "Use secure session management",
                "Log authentication attempts",
            ],
            "Code Security": [
                "Avoid dynamic code execution (loadstring)",
                "Don't use debug library in production",
                "Implement proper error handling",
                "Use secure coding practices",
            ],
            "Data Protection": [
                "Encrypt sensitive data",
                "Don't log sensitive information",
                "Implement data validation",
                "Use secure data storage practices",
            ],
        }
