"""
Roblox Platform Compliance Checker

Validates scripts for compliance with Roblox Community Standards,
Developer Terms of Service, and platform best practices.
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum


class ComplianceLevel(Enum):
    """Compliance levels"""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL_VIOLATION = "critical_violation"


class ViolationType(Enum):
    """Types of compliance violations"""

    COMMUNITY_STANDARDS = "community_standards"
    DEVELOPER_TERMS = "developer_terms"
    PLATFORM_POLICY = "platform_policy"
    SAFETY_VIOLATION = "safety_violation"
    CONTENT_POLICY = "content_policy"
    TECHNICAL_VIOLATION = "technical_violation"


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""

    violation_type: ViolationType
    severity: ComplianceLevel
    line_number: int
    description: str
    policy_reference: str
    recommendation: str
    auto_fixable: bool = False


@dataclass
class ComplianceReport:
    """Complete compliance assessment report"""

    overall_compliance: ComplianceLevel
    violations: list[ComplianceViolation]
    compliant_areas: list[str]
    warnings: list[str]
    critical_issues: list[str]
    platform_ready: bool
    moderation_risk: str  # low, medium, high
    recommendations: list[str]


class RobloxComplianceChecker:
    """
    Comprehensive Roblox platform compliance checker
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Community Standards violations
        self.community_standards = {
            "inappropriate_content": {
                "patterns": [
                    r"\b(sex|sexual|porn|nude|naked|breast|penis|vagina)\b",
                    r"\b(kill|murder|suicide|death|die|blood|gore)\b",
                    r"\b(drug|cocaine|marijuana|weed|alcohol|beer|wine)\b",
                    r"\b(hate|racist|nazi|hitler|terrorist|bomb)\b",
                    r"\b(scam|hack|exploit|cheat|robux|money)\b",
                ],
                "severity": ComplianceLevel.CRITICAL_VIOLATION,
                "policy": "Community Standards - Inappropriate Content",
            },
            "harassment": {
                "patterns": [
                    r"\b(stupid|idiot|loser|noob|trash|garbage)\b",
                    r"\b(kill yourself|kys|die|hate you)\b",
                    r"\b(report|ban|kick|mute|block)\b.*\b(you|player)\b",
                ],
                "severity": ComplianceLevel.VIOLATION,
                "policy": "Community Standards - Harassment and Bullying",
            },
            "personal_information": {
                "patterns": [
                    r"\b\d{3}-\d{3}-\d{4}\b",  # Phone numbers
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
                    r"\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd)\b",  # Addresses
                    r'\bpassword\s*[:=]\s*["\']?\w+["\']?\b',  # Passwords
                    r"\bsocial\s*security\b|\bssn\b",  # SSN references
                ],
                "severity": ComplianceLevel.CRITICAL_VIOLATION,
                "policy": "Community Standards - Personal Information",
            },
        }

        # Developer Terms violations
        self.developer_terms = {
            "unauthorized_monetization": {
                "patterns": [
                    r"\b(paypal|venmo|cashapp|bitcoin|cryptocurrency)\b",
                    r"\b(real\s*money|irl\s*money|usd|dollars)\b",
                    r"\b(sell|buy|purchase).*\b(robux|limiteds|accounts)\b",
                ],
                "severity": ComplianceLevel.CRITICAL_VIOLATION,
                "policy": "Developer Terms - Unauthorized Monetization",
            },
            "platform_exploitation": {
                "patterns": [
                    r"getfenv|setfenv|loadstring|debug\.",
                    r"rawget|rawset.*_G",
                    r"game:HttpGet|HttpService.*evil|malicious",
                    r"require\s*\(\s*\d+\s*\)",  # Suspicious require calls with IDs
                ],
                "severity": ComplianceLevel.VIOLATION,
                "policy": "Developer Terms - Platform Exploitation",
            },
            "api_misuse": {
                "patterns": [
                    r"while\s+true\s+do\s*(?!.*wait)",  # Infinite loops
                    r"for\s+i\s*=\s*1\s*,\s*math\.huge",  # Infinite iterations
                    r"spawn\s*\(\s*function\s*\(\s*\)\s*while",  # Spawn infinite loops
                    r"HttpService:RequestAsync.*(?:1000|5000)",  # Excessive HTTP requests
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Developer Terms - API Misuse",
            },
        }

        # Safety violations
        self.safety_violations = {
            "external_links": {
                "patterns": [
                    r"https?://(?!roblox\.com|rbxcdn\.com|robloxcdn\.com)",
                    r"\b(discord|youtube|twitter|instagram|tiktok)\.com\b",
                    r"\b(join\s*my\s*discord|discord\s*server)\b",
                ],
                "severity": ComplianceLevel.VIOLATION,
                "policy": "Safety - External Links",
            },
            "social_engineering": {
                "patterns": [
                    r"\b(free\s*robux|robux\s*generator|hack\s*robux)\b",
                    r"\b(admin|owner|developer)\b.*\b(give|grant|make)\b",
                    r"\b(trust\s*me|believe\s*me|secret|special)\b",
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Safety - Social Engineering",
            },
        }

        # Technical compliance
        self.technical_compliance = {
            "performance_standards": {
                "patterns": [
                    r"while\s+true\s+do\s*(?!.*wait)",
                    r"workspace:GetDescendants\(\)",
                    r"game\.Players:GetPlayers\(\)\s*\[",
                    r"pairs\(\s*workspace\s*\)",
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Technical Standards - Performance",
            },
            "security_standards": {
                "patterns": [
                    r"RemoteEvent:FireClient\(\s*[^)]*\)\s*(?!--.*validation)",
                    r"RemoteFunction:InvokeClient\(\s*[^)]*\)\s*(?!--.*validation)",
                    r"player\s*:\s*Kick\(\s*\)(?!.*permission)",
                    r"DataStore.*:SetAsync\(\s*[^)]*\)\s*(?!--.*validation)",
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Technical Standards - Security",
            },
        }

        # Content policy
        self.content_policy = {
            "educational_appropriateness": {
                "patterns": [
                    r"\b(gambling|casino|poker|blackjack|lottery)\b",
                    r"\b(war|battle|combat|fight|violence)\b",
                    r"\b(romance|dating|love|kiss|marriage)\b",
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Content Policy - Educational Appropriateness",
            },
            "age_appropriateness": {
                "patterns": [
                    r"\b(mature|adult|18\+|nsfw)\b",
                    r"\b(scary|horror|nightmare|fear)\b",
                    r"\b(political|religion|religious)\b",
                ],
                "severity": ComplianceLevel.WARNING,
                "policy": "Content Policy - Age Appropriateness",
            },
        }

        # Approved Roblox services and APIs
        self.approved_services = {
            "workspace",
            "game",
            "Players",
            "ReplicatedStorage",
            "ReplicatedFirst",
            "ServerScriptService",
            "ServerStorage",
            "StarterGui",
            "StarterPack",
            "StarterPlayer",
            "Lighting",
            "SoundService",
            "TweenService",
            "RunService",
            "UserInputService",
            "ContextActionService",
            "GuiService",
            "PathfindingService",
            "DataStoreService",
            "HttpService",
            "TeleportService",
            "MessagingService",
            "MarketplaceService",
            "BadgeService",
            "GroupService",
            "Teams",
            "Debris",
            "Chat",
            "TextService",
            "LocalizationService",
        }

        # Restricted APIs for educational content
        self.restricted_apis = {
            "HttpService": "Use with caution - requires proper validation",
            "DataStoreService": "Ensure data validation and limits",
            "MessagingService": "Monitor for spam and abuse",
            "TeleportService": "Validate destination places",
        }

    def check_compliance(
        self,
        lua_code: str,
        script_name: str = "unknown",
        educational_context: bool = True,
    ) -> ComplianceReport:
        """
        Perform comprehensive compliance check

        Args:
            lua_code: The Lua code to check
            script_name: Name of the script
            educational_context: Whether this is for educational use

        Returns:
            ComplianceReport with compliance assessment
        """
        violations = []

        # Check community standards
        self._check_community_standards(lua_code, violations)

        # Check developer terms
        self._check_developer_terms(lua_code, violations)

        # Check safety violations
        self._check_safety_violations(lua_code, violations)

        # Check technical compliance
        self._check_technical_compliance(lua_code, violations)

        # Check content policy (especially for educational context)
        if educational_context:
            self._check_content_policy(lua_code, violations)

        # Check API usage
        self._check_api_usage(lua_code, violations)

        # Assess overall compliance
        overall_compliance = self._assess_overall_compliance(violations)

        # Categorize findings
        critical_issues = [
            v.description for v in violations if v.severity == ComplianceLevel.CRITICAL_VIOLATION
        ]
        warnings = [v.description for v in violations if v.severity == ComplianceLevel.WARNING]

        # Identify compliant areas
        compliant_areas = self._identify_compliant_areas(lua_code, violations)

        # Assess moderation risk
        moderation_risk = self._assess_moderation_risk(violations)

        # Determine if platform ready
        platform_ready = (
            overall_compliance in [ComplianceLevel.COMPLIANT, ComplianceLevel.WARNING]
            and not critical_issues
        )

        # Generate recommendations
        recommendations = self._generate_compliance_recommendations(violations, educational_context)

        return ComplianceReport(
            overall_compliance=overall_compliance,
            violations=violations,
            compliant_areas=compliant_areas,
            warnings=warnings,
            critical_issues=critical_issues,
            platform_ready=platform_ready,
            moderation_risk=moderation_risk,
            recommendations=recommendations,
        )

    def _check_community_standards(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check against Roblox Community Standards"""
        lines = lua_code.split("\n")

        for category, rules in self.community_standards.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in rules["patterns"]:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.COMMUNITY_STANDARDS,
                                severity=rules["severity"],
                                line_number=line_num,
                                description=f"Community Standards violation ({category}): {match.group()}",
                                policy_reference=rules["policy"],
                                recommendation=f"Remove or replace content that violates {category} policies",
                                auto_fixable=False,
                            )
                        )

    def _check_developer_terms(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check against Developer Terms of Service"""
        lines = lua_code.split("\n")

        for category, rules in self.developer_terms.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in rules["patterns"]:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.DEVELOPER_TERMS,
                                severity=rules["severity"],
                                line_number=line_num,
                                description=f"Developer Terms violation ({category}): {match.group()}",
                                policy_reference=rules["policy"],
                                recommendation=f"Modify code to comply with {category} requirements",
                                auto_fixable=category == "api_misuse",
                            )
                        )

    def _check_safety_violations(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check for safety violations"""
        lines = lua_code.split("\n")

        for category, rules in self.safety_violations.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in rules["patterns"]:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.SAFETY_VIOLATION,
                                severity=rules["severity"],
                                line_number=line_num,
                                description=f"Safety violation ({category}): {match.group()}",
                                policy_reference=rules["policy"],
                                recommendation=f"Address safety concerns related to {category}",
                                auto_fixable=False,
                            )
                        )

    def _check_technical_compliance(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check technical compliance standards"""
        lines = lua_code.split("\n")

        for category, rules in self.technical_compliance.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in rules["patterns"]:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.TECHNICAL_VIOLATION,
                                severity=rules["severity"],
                                line_number=line_num,
                                description=f"Technical violation ({category}): {match.group()}",
                                policy_reference=rules["policy"],
                                recommendation=f"Improve {category} compliance",
                                auto_fixable=True,
                            )
                        )

    def _check_content_policy(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check content policy compliance"""
        lines = lua_code.split("\n")

        for category, rules in self.content_policy.items():
            for line_num, line in enumerate(lines, 1):
                for pattern in rules["patterns"]:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append(
                            ComplianceViolation(
                                violation_type=ViolationType.CONTENT_POLICY,
                                severity=rules["severity"],
                                line_number=line_num,
                                description=f"Content policy issue ({category}): {match.group()}",
                                policy_reference=rules["policy"],
                                recommendation=f"Review content for {category} compliance",
                                auto_fixable=False,
                            )
                        )

    def _check_api_usage(self, lua_code: str, violations: list[ComplianceViolation]):
        """Check API usage compliance"""
        # Check for unapproved services
        service_pattern = r'game:GetService\s*\(\s*["\'](\w+)["\']\s*\)'
        matches = re.finditer(service_pattern, lua_code)

        for match in matches:
            service_name = match.group(1)
            if service_name not in self.approved_services:
                line_num = lua_code[: match.start()].count("\n") + 1
                violations.append(
                    ComplianceViolation(
                        violation_type=ViolationType.PLATFORM_POLICY,
                        severity=ComplianceLevel.VIOLATION,
                        line_number=line_num,
                        description=f"Unapproved service usage: {service_name}",
                        policy_reference="Platform Policy - API Usage",
                        recommendation=f"Use only approved Roblox services",
                        auto_fixable=False,
                    )
                )

        # Check for restricted API usage
        for api, warning in self.restricted_apis.items():
            if re.search(rf"\b{api}\b", lua_code, re.IGNORECASE):
                line_num = 1  # Could be refined to find actual line
                violations.append(
                    ComplianceViolation(
                        violation_type=ViolationType.PLATFORM_POLICY,
                        severity=ComplianceLevel.WARNING,
                        line_number=line_num,
                        description=f"Restricted API usage: {api}",
                        policy_reference="Platform Policy - Restricted APIs",
                        recommendation=warning,
                        auto_fixable=False,
                    )
                )

    def _assess_overall_compliance(self, violations: list[ComplianceViolation]) -> ComplianceLevel:
        """Assess overall compliance level"""
        if any(v.severity == ComplianceLevel.CRITICAL_VIOLATION for v in violations):
            return ComplianceLevel.CRITICAL_VIOLATION
        elif any(v.severity == ComplianceLevel.VIOLATION for v in violations):
            return ComplianceLevel.VIOLATION
        elif any(v.severity == ComplianceLevel.WARNING for v in violations):
            return ComplianceLevel.WARNING
        else:
            return ComplianceLevel.COMPLIANT

    def _identify_compliant_areas(
        self, lua_code: str, violations: list[ComplianceViolation]
    ) -> list[str]:
        """Identify areas that are compliant"""
        compliant_areas = []

        # Check for good practices
        if re.search(r"game:GetService", lua_code) and not any(
            v.description.startswith("Unapproved service") for v in violations
        ):
            compliant_areas.append("Proper service usage")

        if re.search(r"local\s+\w+\s*=", lua_code):
            compliant_areas.append("Local variable usage")

        if re.search(r"wait\s*\([0-9.]+\)", lua_code):
            compliant_areas.append("Proper wait usage")

        if not any(v.violation_type == ViolationType.COMMUNITY_STANDARDS for v in violations):
            compliant_areas.append("Community Standards compliant")

        if not any(v.violation_type == ViolationType.SAFETY_VIOLATION for v in violations):
            compliant_areas.append("Safety compliant")

        return compliant_areas

    def _assess_moderation_risk(self, violations: list[ComplianceViolation]) -> str:
        """Assess moderation risk level"""
        critical_count = sum(
            1 for v in violations if v.severity == ComplianceLevel.CRITICAL_VIOLATION
        )
        violation_count = sum(1 for v in violations if v.severity == ComplianceLevel.VIOLATION)

        if critical_count > 0:
            return "high"
        elif violation_count > 2:
            return "medium"
        else:
            return "low"

    def _generate_compliance_recommendations(
        self, violations: list[ComplianceViolation], educational_context: bool
    ) -> list[str]:
        """Generate compliance recommendations"""
        recommendations = []

        # Group violations by type
        violation_types = {}
        for v in violations:
            if v.violation_type not in violation_types:
                violation_types[v.violation_type] = []
            violation_types[v.violation_type].append(v)

        # Generate specific recommendations
        if ViolationType.COMMUNITY_STANDARDS in violation_types:
            recommendations.append(
                "Review and remove all content that violates Community Standards"
            )

        if ViolationType.SAFETY_VIOLATION in violation_types:
            recommendations.append("Implement additional safety measures and content filtering")

        if ViolationType.TECHNICAL_VIOLATION in violation_types:
            recommendations.append("Optimize code for better performance and security")

        if educational_context:
            recommendations.extend(
                [
                    "Ensure all content is age-appropriate for target audience",
                    "Implement proper moderation and reporting systems",
                    "Add clear terms of use and community guidelines",
                    "Regular compliance audits and updates",
                ]
            )

        # General recommendations
        recommendations.extend(
            [
                "Regular review of Roblox policy updates",
                "Implement automated content filtering",
                "User education on platform policies",
                "Clear escalation procedures for violations",
            ]
        )

        return list(set(recommendations))  # Remove duplicates

    def generate_compliance_template(self) -> str:
        """Generate a compliance-friendly script template"""
        return """
-- ToolBoxAI Educational Content - Compliance Template
-- This template follows Roblox Community Standards and Developer Terms

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

-- Safe remote event setup
local remoteEvent = Instance.new("RemoteEvent")
remoteEvent.Name = "EducationalRemoteEvent"
remoteEvent.Parent = ReplicatedStorage

-- Rate limiting for safety
local playerCooldowns = {}
local COOLDOWN_TIME = 1 -- seconds

-- Input validation function
local function validateInput(input)
    -- Check input type
    if type(input) ~= "string" then
        return false
    end

    -- Check input length
    if #input > 100 then
        return false
    end

    -- Check for inappropriate content
    local blockedWords = {"inappropriate", "content", "here"}
    for _, word in ipairs(blockedWords) do
        if string.find(input:lower(), word) then
            return false
        end
    end

    return true
end

-- Safe remote event handler
remoteEvent.OnServerEvent:Connect(function(player, action, data)
    -- Rate limiting
    local userId = player.UserId
    local currentTime = tick()
    local lastTime = playerCooldowns[userId] or 0

    if currentTime - lastTime < COOLDOWN_TIME then
        return -- Rate limited
    end

    playerCooldowns[userId] = currentTime

    -- Input validation
    if not validateInput(action) or not validateInput(data) then
        warn("Invalid input from player:", player.Name)
        return
    end

    -- Permission check
    if not player.Parent == Players then
        return
    end

    -- Safe processing
    print("Educational action from", player.Name, ":", action)
end)

-- Educational content example
local function createLearningActivity()
    local part = Instance.new("Part")
    part.Name = "LearningObject"
    part.Size = Vector3.new(4, 1, 2)
    part.Position = Vector3.new(0, 5, 0)
    part.BrickColor = BrickColor.new("Bright blue")
    part.Parent = workspace

    -- Safe click detection
    local clickDetector = Instance.new("ClickDetector")
    clickDetector.MaxActivationDistance = 10
    clickDetector.Parent = part

    clickDetector.MouseClick:Connect(function(player)
        if player and player.Parent == Players then
            print(player.Name, "interacted with learning object")
            -- Educational logic here
        end
    end)
end

-- Initialize educational content
createLearningActivity()

print("Educational content loaded successfully - Compliance verified")
        """

    def get_compliance_checklist(self) -> dict[str, list[str]]:
        """Get compliance checklist for developers"""
        return {
            "Community Standards": [
                "No inappropriate or offensive content",
                "No harassment or bullying language",
                "No personal information sharing",
                "No unauthorized monetization schemes",
                "Age-appropriate content only",
            ],
            "Safety Requirements": [
                "No external links or social media promotion",
                "No social engineering attempts",
                "Proper input validation and sanitization",
                "Safe communication channels only",
                "Clear reporting mechanisms",
            ],
            "Technical Standards": [
                "Proper API usage and rate limiting",
                "No performance-degrading code",
                "Secure remote event handling",
                "Memory leak prevention",
                "Error handling implementation",
            ],
            "Educational Standards": [
                "Content appropriate for target age group",
                "Clear learning objectives",
                "Safe collaborative features",
                "Proper moderation tools",
                "Accessibility considerations",
            ],
            "Developer Terms": [
                "No platform exploitation attempts",
                "Proper service usage",
                "No unauthorized API access",
                "Compliance with usage limits",
                "Regular policy review and updates",
            ],
        }
