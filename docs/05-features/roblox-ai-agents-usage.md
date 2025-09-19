# 🤖 Roblox AI Agents - Usage Guide

## Overview

The Roblox AI Agent Suite provides powerful AI-driven capabilities for educational content creation, script optimization, and security validation in Roblox games. This guide covers how to use these agents through the REST API.

## Table of Contents

1. [API Endpoints](#api-endpoints)
2. [Authentication](#authentication)
3. [Content Generation](#content-generation)
4. [Script Optimization](#script-optimization)
5. [Security Validation](#security-validation)
6. [Batch Processing](#batch-processing)
7. [Python Client Examples](#python-client-examples)
8. [Dashboard Integration](#dashboard-integration)
9. [Best Practices](#best-practices)

---

## API Endpoints

Base URL: `http://localhost:8008/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/roblox-agents/status` | GET | Check agent availability |
| `/roblox-agents/generate-content` | POST | Generate educational content |
| `/roblox-agents/optimize-script` | POST | Optimize Luau scripts |
| `/roblox-agents/validate-security` | POST | Validate script security |
| `/roblox-agents/batch-validate` | POST | Batch validate multiple scripts |
| `/roblox-agents/templates` | GET | Get available templates |

---

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer YOUR_JWT_TOKEN
```

To obtain a token:

```bash
curl -X POST http://localhost:8008/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

---

## Content Generation

### Generate Math Quiz

```bash
curl -X POST http://localhost:8008/api/v1/roblox-agents/generate-content \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Mathematics",
    "topic": "Fractions",
    "grade_level": 5,
    "activity_type": "quiz",
    "num_questions": 10,
    "accessibility_features": ["text-to-speech", "high-contrast"]
  }'
```

**Response:**
```json
{
  "success": true,
  "content_id": "content_20250919_120000",
  "subject": "Mathematics",
  "topic": "Fractions",
  "grade_level": 5,
  "scripts": {
    "MainController": "-- Main game controller Luau code...",
    "QuizSystem": "-- Quiz system Luau code...",
    "ProgressTracker": "-- Progress tracking Luau code...",
    "AccessibilityController": "-- Accessibility features Luau code..."
  },
  "assets": [
    {
      "type": "Model",
      "name": "FractionVisualizer",
      "description": "3D fraction visualization model"
    }
  ],
  "accessibility_features": ["text-to-speech", "high-contrast"],
  "generation_time": 2.35
}
```

### Generate Science Experiment

```bash
curl -X POST http://localhost:8008/api/v1/roblox-agents/generate-content \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Science",
    "topic": "Solar System",
    "grade_level": 7,
    "activity_type": "experiment",
    "accessibility_features": ["subtitles", "colorblind-mode"]
  }'
```

---

## Script Optimization

### Optimize Performance

```bash
curl -X POST http://localhost:8008/api/v1/roblox-agents/optimize-script \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_code": "while true do\n    wait()\n    for i = 1, #players do\n        local player = players[i]\n        updatePlayer(player)\n    end\nend",
    "optimization_level": "balanced",
    "preserve_comments": true,
    "script_type": "ServerScript"
  }'
```

**Response:**
```json
{
  "success": true,
  "original_lines": 7,
  "optimized_lines": 10,
  "original_code": "...",
  "optimized_code": "-- Optimized code\nlocal RunService = game:GetService(\"RunService\")\nlocal players_len = #players\n\nRunService.Heartbeat:Connect(function()\n    for i = 1, players_len do\n        local player = players[i]\n        updatePlayer(player)\n    end\nend)",
  "issues_found": [
    {
      "severity": "critical",
      "location": "Line 1",
      "type": "Inefficient loop",
      "description": "Using wait() in while loop",
      "suggestion": "Use RunService.Heartbeat instead",
      "impact": "20-30% performance improvement"
    }
  ],
  "optimization_level": "balanced",
  "performance_gain": "15-25%",
  "compatibility_notes": ["Requires modern Roblox engine"]
}
```

---

## Security Validation

### Validate Script Security

```bash
curl -X POST http://localhost:8008/api/v1/roblox-agents/validate-security \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "script_code": "local password = \"admin123\"\nloadstring(userInput)()",
    "script_type": "ServerScript",
    "strict_mode": true
  }'
```

**Response:**
```json
{
  "success": true,
  "scan_id": "scan_a1b2c3d4",
  "risk_score": 9.5,
  "vulnerabilities": [
    {
      "threat_level": "critical",
      "type": "code_injection",
      "location": "Line 2",
      "description": "Use of dangerous function 'loadstring'",
      "impact": "Allows arbitrary code execution",
      "remediation": "Replace with TemplateExecutor pattern",
      "cvss_score": 9.8,
      "exploitable": true
    },
    {
      "threat_level": "high",
      "type": "data_exposure",
      "location": "Line 1",
      "description": "Hardcoded password",
      "impact": "Credentials exposed in code",
      "remediation": "Use SecureConfigurationManager",
      "cvss_score": 7.5,
      "exploitable": true
    }
  ],
  "compliance_status": {
    "no_dangerous_functions": false,
    "input_validation": false,
    "no_hardcoded_credentials": false,
    "rate_limiting": false,
    "roblox_tos_compliant": false
  },
  "recommendations": [
    "🔴 CRITICAL: Address critical security vulnerabilities immediately",
    "  - Replace loadstring with template-based execution",
    "  - Remove hardcoded password",
    "✅ Use secure configuration management",
    "📊 Total issues found: 2"
  ],
  "blocked_patterns": ["loadstring"],
  "safe_patterns": [],
  "report_markdown": "# 🔒 Security Validation Report\n\n..."
}
```

---

## Batch Processing

### Validate Multiple Scripts

```bash
curl -X POST http://localhost:8008/api/v1/roblox-agents/batch-validate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scripts": [
      {
        "script_code": "-- Script 1 code",
        "script_type": "ServerScript",
        "strict_mode": true
      },
      {
        "script_code": "-- Script 2 code",
        "script_type": "LocalScript",
        "strict_mode": true
      }
    ]
  }'
```

---

## Python Client Examples

### Complete Python Client

```python
import requests
import json
from typing import Dict, Any, Optional

class RobloxAgentsClient:
    """Client for Roblox AI Agents API"""

    def __init__(self, base_url: str = "http://localhost:8008", token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def login(self, username: str, password: str) -> str:
        """Authenticate and get JWT token"""
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        self.token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        return token

    def generate_content(
        self,
        subject: str,
        topic: str,
        grade_level: int,
        activity_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate educational content"""
        payload = {
            "subject": subject,
            "topic": topic,
            "grade_level": grade_level,
            "activity_type": activity_type,
            **kwargs
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/roblox-agents/generate-content",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def optimize_script(
        self,
        script_code: str,
        optimization_level: str = "balanced"
    ) -> Dict[str, Any]:
        """Optimize Luau script"""
        payload = {
            "script_code": script_code,
            "optimization_level": optimization_level,
            "preserve_comments": True,
            "script_type": "ServerScript"
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/roblox-agents/optimize-script",
            json=payload
        )
        response.raise_for_status()
        return response.json()

    def validate_security(
        self,
        script_code: str,
        script_type: str = "ServerScript"
    ) -> Dict[str, Any]:
        """Validate script security"""
        payload = {
            "script_code": script_code,
            "script_type": script_type,
            "strict_mode": True
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/roblox-agents/validate-security",
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    # Initialize client
    client = RobloxAgentsClient()

    # Authenticate
    client.login("teacher@example.com", "password123")

    # Generate math quiz
    content = client.generate_content(
        subject="Mathematics",
        topic="Multiplication Tables",
        grade_level=3,
        activity_type="quiz",
        num_questions=10,
        accessibility_features=["text-to-speech", "high-contrast"]
    )

    print(f"Generated content ID: {content['content_id']}")
    print(f"Scripts generated: {list(content['scripts'].keys())}")

    # Save scripts to files
    for script_name, script_code in content['scripts'].items():
        with open(f"{script_name}.lua", "w") as f:
            f.write(script_code)

    # Optimize a script
    with open("MainController.lua", "r") as f:
        original_code = f.read()

    optimization = client.optimize_script(original_code)
    print(f"Performance gain: {optimization['performance_gain']}")
    print(f"Issues found: {len(optimization['issues_found'])}")

    # Validate security
    security = client.validate_security(optimization['optimized_code'])
    print(f"Risk score: {security['risk_score']}/10")
    print(f"Is compliant: {security['compliance_status']['roblox_tos_compliant']}")
```

---

## Dashboard Integration

### React Component Example

```typescript
import React, { useState } from 'react';
import { api } from '@/services/api';

const RobloxContentGenerator: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState(null);

  const generateContent = async () => {
    setLoading(true);
    try {
      const response = await api.post('/roblox-agents/generate-content', {
        subject: 'Mathematics',
        topic: 'Geometry',
        grade_level: 6,
        activity_type: 'interactive',
        accessibility_features: ['text-to-speech', 'high-contrast']
      });

      setContent(response.data);

      // Download scripts as files
      Object.entries(response.data.scripts).forEach(([name, code]) => {
        const blob = new Blob([code as string], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${name}.lua`;
        a.click();
      });
    } catch (error) {
      console.error('Generation failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={generateContent} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Educational Content'}
      </button>

      {content && (
        <div>
          <h3>Generated Content</h3>
          <p>Subject: {content.subject}</p>
          <p>Topic: {content.topic}</p>
          <p>Scripts: {Object.keys(content.scripts).join(', ')}</p>
        </div>
      )}
    </div>
  );
};
```

---

## Best Practices

### 1. Content Generation

- **Be Specific**: Provide detailed topics for better content
- **Grade-Appropriate**: Always specify the correct grade level
- **Accessibility First**: Include accessibility features by default
- **Test Generated Content**: Always test in Roblox Studio before deployment

### 2. Script Optimization

- **Start Conservative**: Begin with conservative optimization level
- **Test Performance**: Benchmark before and after optimization
- **Preserve Comments**: Keep comments for documentation
- **Review Changes**: Manually review optimized code

### 3. Security Validation

- **Regular Scans**: Validate scripts before every deployment
- **Fix Critical Issues**: Address critical vulnerabilities immediately
- **Use Templates**: Replace dangerous patterns with secure templates
- **Follow Recommendations**: Implement all security recommendations

### 4. API Usage

- **Rate Limiting**: Respect rate limits (100 requests/minute)
- **Batch Operations**: Use batch endpoints for multiple scripts
- **Cache Results**: Cache generated content and validation reports
- **Error Handling**: Implement proper error handling

### 5. Integration Tips

```python
# Error handling example
import time
from typing import Optional

def retry_request(func, max_retries: int = 3, delay: float = 1.0):
    """Retry failed requests with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
    return None

# Cache example
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_templates(client):
    """Cache template responses"""
    return client.session.get(
        f"{client.base_url}/api/v1/roblox-agents/templates"
    ).json()
```

---

## Troubleshooting

### Common Issues

1. **Agent Not Available (503)**
   - Ensure all dependencies are installed
   - Check if LangChain and OpenAI API keys are configured
   - Verify agents are properly imported

2. **Authentication Failed (401)**
   - Token may be expired, re-authenticate
   - Check user permissions

3. **Content Generation Timeout**
   - Complex content may take longer
   - Consider reducing complexity or number of questions

4. **Optimization Changes Behavior**
   - Review optimization level
   - Use conservative mode for critical scripts

5. **Security False Positives**
   - Review context of flagged patterns
   - Some patterns may be safe in specific contexts

---

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review agent logs in backend console
- Contact support with scan_id for security issues

---

*Last Updated: September 19, 2025*
*Version: 1.0.0*