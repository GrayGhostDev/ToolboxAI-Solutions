"""
RobloxSecurityValidatorAgent - Validates scripts for security vulnerabilities

This agent checks for exploits, validates RemoteEvent/RemoteFunction security,
and implements anti-cheat measures.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..base_agent import BaseAgent


class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityIssue:
    level: SecurityLevel
    description: str
    location: str
    recommendation: str


class RobloxSecurityValidatorAgent(BaseAgent):
    """
    Agent responsible for validating Roblox scripts for security vulnerabilities
    and implementing security best practices.
    """
    
    def __init__(self):
        super().__init__({
            "name": "RobloxSecurityValidatorAgent",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000
        })
        
        self.name = "RobloxSecurityValidatorAgent"
        self.description = "Validates scripts for security vulnerabilities"
        
        # Security patterns to check
        self.vulnerability_patterns = {
            r"loadstring\s*\(": "Loadstring can execute arbitrary code",
            r"getfenv\s*\(": "Environment manipulation detected",
            r"setfenv\s*\(": "Environment manipulation detected",
            r"rawset\s*\(": "Raw table manipulation detected",
            r"rawget\s*\(": "Raw table access detected",
            r"debug\.": "Debug library usage detected",
            r"while\s+true\s+do\s*$": "Potential infinite loop without yield",
            r"RemoteEvent.*FireClient\(": "Unvalidated RemoteEvent detected",
            r"RemoteFunction.*InvokeClient\(": "Unvalidated RemoteFunction detected"
        }
        
        self.secure_patterns = {
            "rate_limiting": r"local\s+lastAction.*tick\(\)",
            "input_validation": r"if\s+type\(.*\)\s*==",
            "permission_check": r"if.*player.*UserId.*then",
            "sanity_check": r"if.*and.*<.*then"
        }
    
    async def validate_script(self, script_code: str) -> dict[str, Any]:
        """Validate a Roblox script for security issues"""
        issues = []
        
        # Check for vulnerabilities
        for pattern, description in self.vulnerability_patterns.items():
            import re
            if re.search(pattern, script_code):
                issues.append(SecurityIssue(
                    level=SecurityLevel.HIGH,
                    description=description,
                    location=pattern,
                    recommendation=self._get_recommendation(pattern)
                ))
        
        # Check for missing security measures
        has_rate_limiting = any(re.search(p, script_code) for p in self.secure_patterns.values())
        if not has_rate_limiting and "RemoteEvent" in script_code:
            issues.append(SecurityIssue(
                level=SecurityLevel.MEDIUM,
                description="Missing rate limiting for remote events",
                location="RemoteEvent handlers",
                recommendation="Add rate limiting to prevent spam"
            ))
        
        # Calculate security score
        score = 100
        for issue in issues:
            if issue.level == SecurityLevel.CRITICAL:
                score -= 25
            elif issue.level == SecurityLevel.HIGH:
                score -= 15
            elif issue.level == SecurityLevel.MEDIUM:
                score -= 10
            else:
                score -= 5
        
        return {
            "success": True,
            "score": max(0, score),
            "issues": [{"level": i.level.value, "description": i.description, 
                       "recommendation": i.recommendation} for i in issues],
            "passed": score >= 70
        }
    
    def _get_recommendation(self, pattern: str) -> str:
        """Get security recommendation for a pattern"""
        recommendations = {
            "loadstring": "Remove loadstring usage or use pre-compiled functions",
            "getfenv": "Avoid environment manipulation",
            "setfenv": "Use module pattern instead of environment manipulation",
            "while true": "Add wait() or task.wait() in infinite loops",
            "RemoteEvent": "Validate all RemoteEvent inputs on server",
            "RemoteFunction": "Add permission checks before invoking"
        }
        
        for key, rec in recommendations.items():
            if key in pattern:
                return rec
        return "Review and secure this code section"
    
    def generate_secure_remote(self, remote_type: str, name: str) -> str:
        """Generate secure RemoteEvent/RemoteFunction code"""
        if remote_type == "RemoteEvent":
            return f"""-- Secure RemoteEvent: {name}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remoteEvent = Instance.new("RemoteEvent")
remoteEvent.Name = "{name}"
remoteEvent.Parent = ReplicatedStorage

-- Rate limiting
local playerCooldowns = {{}}
local COOLDOWN_TIME = 1 -- seconds

remoteEvent.OnServerEvent:Connect(function(player, ...)
    -- Rate limiting
    local lastTime = playerCooldowns[player.UserId] or 0
    if tick() - lastTime < COOLDOWN_TIME then
        return -- Too many requests
    end
    playerCooldowns[player.UserId] = tick()
    
    -- Input validation
    local args = {{...}}
    for i, arg in ipairs(args) do
        if type(arg) ~= "string" and type(arg) ~= "number" then
            warn("Invalid argument type from", player.Name)
            return
        end
    end
    
    -- Permission check
    if not player.Character or not player.Character:FindFirstChild("Humanoid") then
        return
    end
    
    -- Process request
    print(player.Name, "triggered", "{name}")
end)
"""
        else:
            return f"""-- Secure RemoteFunction: {name}
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local remoteFunction = Instance.new("RemoteFunction")
remoteFunction.Name = "{name}"
remoteFunction.Parent = ReplicatedStorage

-- Rate limiting
local playerCooldowns = {{}}
local COOLDOWN_TIME = 2 -- seconds

remoteFunction.OnServerInvoke = function(player, ...)
    -- Rate limiting
    local lastTime = playerCooldowns[player.UserId] or 0
    if tick() - lastTime < COOLDOWN_TIME then
        return false, "Rate limited"
    end
    playerCooldowns[player.UserId] = tick()
    
    -- Input validation
    local args = {{...}}
    for i, arg in ipairs(args) do
        if type(arg) ~= "string" and type(arg) ~= "number" and type(arg) ~= "boolean" then
            return false, "Invalid argument"
        end
    end
    
    -- Process and return
    return true, "Success"
end
"""
    
    async def execute_task(self, task: str) -> dict[str, Any]:
        """Execute security validation task"""
        if "validate" in task.lower():
            # Extract code from task and validate
            return await self.validate_script(task)
        elif "secure remote" in task.lower():
            code = self.generate_secure_remote("RemoteEvent", "SecureEvent")
            return {"success": True, "code": code}
        else:
            return {"success": False, "error": "Unknown security task"}