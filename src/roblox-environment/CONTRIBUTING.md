# Contributing to ToolboxAI Roblox Environment

Thank you for your interest in contributing to the ToolboxAI Roblox Environment! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Project Structure](#-project-structure)
- [Contributing Guidelines](#-contributing-guidelines)
- [Code Standards](#-code-standards)
- [Testing](#-testing)
- [Pull Request Process](#-pull-request-process)
- [Educational Content Guidelines](#-educational-content-guidelines)
- [Issue Templates](#-issue-templates)
- [Community](#-community)

## 📜 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@toolboxai.io](mailto:conduct@toolboxai.io).

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, sex characteristics, gender identity and expression, level of experience, education, socio-economic status, nationality, personal appearance, race, religion, or sexual identity and orientation.

## 🚀 Getting Started

### Prerequisites

Before contributing, ensure you have:

- **Python 3.11+** with virtual environment support
- **Node.js 18+** and npm
- **Roblox Studio** (latest version)
- **Git** with proper configuration
- **Docker** and **Docker Compose** (recommended)
- **API Keys** for testing (OpenAI, LMS platforms)

### Quick Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/ToolboxAI-Roblox-Environment.git
cd ToolboxAI-Roblox-Environment

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your test API keys
```

## 🛠️ Development Setup

### Environment Configuration

1. **API Keys** (for testing only - never commit real keys):
   ```bash
   export OPENAI_API_KEY="your-test-key"
   export SCHOOLOGY_KEY="test-key"
   export SCHOOLOGY_SECRET="test-secret"
   ```

2. **Database Setup**:
   ```bash
   # Using Docker (recommended)
   docker-compose up -d postgres redis
   
   # Or install locally
   # PostgreSQL 15+, Redis 7+
   ```

3. **Development Servers**:
   ```bash
   # Terminal 1: MCP Server
   python mcp/server.py
   
   # Terminal 2: FastAPI Server
   python server/main.py
   
   # Terminal 3: Flask Bridge
   python server/roblox_server.py
   
   # Terminal 4: Frontend services
   cd API/Dashboard && npm run dev
   ```

### IDE Setup

#### VS Code (Recommended)
Install recommended extensions:
- Python
- Pylance
- Black Formatter
- Ruff
- LuaFormatter
- GitHub Copilot (optional)

#### PyCharm/IntelliJ
- Configure Python interpreter to use virtual environment
- Enable code formatting with Black
- Set up Ruff for linting

## 📁 Project Structure

```
ToolboxAI-Roblox-Environment/
├── mcp/                    # Model Context Protocol (WebSocket server)
├── agents/                 # LangChain/LangGraph AI agents
├── sparc/                  # SPARC framework implementation
├── swarm/                  # Swarm intelligence coordination
├── coordinators/           # High-level system coordination
├── server/                 # FastAPI + Flask servers
├── Roblox/                 # Roblox Studio components
├── API/                    # Existing Dashboard/Ghost backend
├── tests/                  # Test suites
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── .github/               # GitHub workflows and templates
```

### Key Directories

- **`agents/`**: AI agent implementations using LangChain/LangGraph
- **`server/`**: Backend API servers (FastAPI + Flask)
- **`mcp/`**: Model Context Protocol for agent communication
- **`Roblox/`**: Lua scripts and Studio plugin components
- **`tests/`**: Comprehensive test coverage

## 🤝 Contributing Guidelines

### Types of Contributions

1. **Bug Fixes** 🐛
   - Fix identified issues
   - Improve error handling
   - Performance optimizations

2. **Feature Development** ✨
   - New AI agents
   - Educational content types
   - Roblox integrations
   - LMS platform support

3. **Documentation** 📚
   - API documentation
   - Code examples
   - Educational guides
   - Architecture diagrams

4. **Testing** 🧪
   - Unit tests
   - Integration tests
   - Performance benchmarks
   - Educational content validation

### Contribution Process

1. **Check Existing Issues**: Look for related issues or create a new one
2. **Discuss Major Changes**: Use GitHub Discussions for significant features
3. **Fork & Branch**: Create a feature branch from `main`
4. **Develop**: Follow code standards and write tests
5. **Test Thoroughly**: Run full test suite
6. **Submit PR**: Follow pull request template

## 💻 Code Standards

### Python Code Standards

#### Formatting
```bash
# Use Black for code formatting
black server/ agents/ mcp/ sparc/ swarm/ coordinators/

# Sort imports with isort
isort server/ agents/ mcp/

# Check with flake8
flake8 server/ agents/ mcp/
```

#### Type Hints
```python
# Always use type hints
def generate_content(
    subject: str,
    grade_level: int,
    objectives: List[str]
) -> Dict[str, Any]:
    """Generate educational content with proper typing."""
    pass

# Use Pydantic models for data validation
from pydantic import BaseModel

class ContentRequest(BaseModel):
    subject: str
    grade_level: int
    objectives: List[str]
```

#### Documentation
```python
def complex_function(param1: str, param2: int) -> Dict:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> result = complex_function("test", 5)
        >>> print(result["status"])
        success
    """
    pass
```

### Lua Code Standards

#### Roblox Lua Style
```lua
-- Use PascalCase for functions and variables
local function GenerateQuiz(subject, difficulty)
    -- Validate inputs
    if not subject or not difficulty then
        error("Subject and difficulty are required")
    end
    
    -- Use meaningful variable names
    local quizData = {
        Subject = subject,
        Difficulty = difficulty,
        Questions = {}
    }
    
    return quizData
end

-- Use proper service access
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

-- Error handling
local success, result = pcall(function()
    return HttpService:JSONDecode(responseBody)
end)

if not success then
    warn("Failed to decode JSON: " .. tostring(result))
    return nil
end
```

### TypeScript/JavaScript Standards

```typescript
// Use TypeScript interfaces
interface ContentRequest {
  subject: string;
  gradeLevel: number;
  objectives: string[];
}

// Use async/await
const generateContent = async (request: ContentRequest): Promise<ContentResponse> => {
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Content generation failed:', error);
    throw error;
  }
};
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                   # Unit tests for individual components
│   ├── test_agents.py
│   ├── test_server.py
│   └── test_mcp.py
├── integration/            # Integration tests between components
│   ├── test_api_integration.py
│   └── test_agent_coordination.py
├── e2e/                   # End-to-end tests
│   ├── test_content_generation.py
│   └── test_roblox_plugin.py
├── performance/           # Performance benchmarks
│   └── test_agent_performance.py
└── fixtures/              # Test data and fixtures
    ├── educational_content.json
    └── mock_responses.py
```

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ -v --cov=server --cov=agents --cov=mcp --cov-report=html

# Run specific test categories
pytest tests/unit/ -v              # Unit tests only
pytest tests/integration/ -v       # Integration tests only
pytest tests/e2e/ -v              # End-to-end tests only

# Run performance benchmarks
pytest tests/performance/ --benchmark-only

# Run tests with specific markers
pytest -m "agent" tests/           # Tests marked with @pytest.mark.agent
pytest -m "slow" tests/            # Long-running tests
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from agents.content_agent import ContentAgent

class TestContentAgent:
    @pytest.fixture
    def content_agent(self):
        return ContentAgent(model="gpt-3.5-turbo")
    
    @pytest.mark.asyncio
    async def test_generate_math_content(self, content_agent):
        """Test math content generation."""
        request = {
            "subject": "Mathematics",
            "grade_level": 5,
            "objectives": ["Addition", "Subtraction"]
        }
        
        result = await content_agent.generate_content(request)
        
        assert result["success"] is True
        assert "scripts" in result
        assert len(result["scripts"]) > 0
    
    def test_validate_request(self, content_agent):
        """Test request validation."""
        invalid_request = {"subject": ""}
        
        with pytest.raises(ValueError, match="Subject cannot be empty"):
            content_agent.validate_request(invalid_request)
```

#### Integration Test Example
```python
import pytest
import asyncio
from server.main import app
from fastapi.testclient import TestClient

class TestAPIIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_content_generation_endpoint(self, client):
        """Test full content generation workflow."""
        request_data = {
            "subject": "Science",
            "grade_level": 7,
            "learning_objectives": ["Solar System"],
            "environment_type": "space_station"
        }
        
        response = client.post("/generate_content", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["scripts"]) > 0
```

### Test Requirements

- **Coverage**: Maintain >90% code coverage
- **Performance**: Ensure tests run in <30 seconds
- **Isolation**: Tests should not depend on external services
- **Documentation**: Document test purpose and expectations
- **Fixtures**: Use fixtures for common test data

## 🔄 Pull Request Process

### Before Submitting

1. **Run Full Test Suite**:
   ```bash
   pytest tests/ -v --cov=server --cov=agents --cov=mcp
   ```

2. **Code Quality Checks**:
   ```bash
   black --check server/ agents/ mcp/
   flake8 server/ agents/ mcp/
   mypy server/ agents/ mcp/
   ```

3. **Update Documentation**:
   - Update relevant docstrings
   - Update CHANGELOG.md if applicable
   - Add examples if introducing new features

### PR Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests pass locally
- [ ] Performance impact assessed

## Educational Content
- [ ] Content follows educational best practices
- [ ] Age-appropriate for target grade level
- [ ] Aligns with learning objectives
- [ ] Includes accessibility considerations

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and quality checks
2. **Code Review**: Maintainers review code for:
   - Functionality and correctness
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Educational appropriateness
3. **Feedback Integration**: Address reviewer comments
4. **Final Approval**: Minimum 2 approvals from maintainers
5. **Merge**: Squash and merge with descriptive commit message

## 🎓 Educational Content Guidelines

### Content Standards

#### Age Appropriateness
- **K-2 (Ages 5-7)**: Simple concepts, visual learning, basic interactions
- **3-5 (Ages 8-10)**: Interactive challenges, guided discovery
- **6-8 (Ages 11-13)**: Problem-solving, collaboration features
- **9-12 (Ages 14-18)**: Complex simulations, research projects

#### Educational Best Practices
1. **Clear Learning Objectives**: Define what students should achieve
2. **Progressive Difficulty**: Start simple, build complexity
3. **Multiple Learning Styles**: Visual, auditory, kinesthetic, reading/writing
4. **Immediate Feedback**: Provide real-time feedback on actions
5. **Gamification**: Use rewards, achievements, and progress tracking
6. **Accessibility**: Support diverse learners and abilities

#### Content Creation Process
```python
# Example educational content validation
def validate_educational_content(content: Dict) -> bool:
    """Validate that content meets educational standards."""
    required_fields = [
        'learning_objectives',
        'grade_level',
        'subject',
        'difficulty_progression',
        'assessment_methods'
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in content:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate grade level appropriateness
    if not is_age_appropriate(content['content'], content['grade_level']):
        raise ValueError("Content not appropriate for grade level")
    
    return True
```

### Subject-Specific Guidelines

#### STEM Subjects
- Emphasize hands-on experimentation
- Include real-world applications
- Support collaborative problem-solving
- Provide multiple solution paths

#### Language Arts
- Include diverse perspectives and voices
- Support different reading levels
- Encourage creative expression
- Build communication skills

#### Social Studies
- Present multiple viewpoints
- Include primary source materials
- Encourage critical thinking
- Connect past to present

#### Arts Education
- Support creative exploration
- Provide examples of diverse artistic traditions
- Encourage personal expression
- Build appreciation for aesthetics

## 🐛 Issue Templates

### Bug Report Template
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. iOS]
 - Python Version: [e.g. 3.11.0]
 - Roblox Studio Version: [e.g. 0.545.0.5450000]
 - Browser [e.g. chrome, safari]

**Additional context**
Add any other context about the problem here.
```

### Feature Request Template
```markdown
**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Educational Impact**
How would this feature improve the educational experience?

**Additional context**
Add any other context or screenshots about the feature request here.
```

## 👥 Community

### Communication Channels

- **GitHub Discussions**: Project discussions and Q&A
- **GitHub Issues**: Bug reports and feature requests
- **Discord**: Real-time chat (invite link in README)
- **Email**: [team@toolboxai.io](mailto:team@toolboxai.io) for private matters

### Getting Help

1. **Check Documentation**: Start with [CLAUDE.md](CLAUDE.md) and this guide
2. **Search Issues**: Look for existing issues and solutions
3. **Ask Questions**: Use GitHub Discussions for questions
4. **Join Discord**: Connect with other contributors

### Recognition

Contributors are recognized through:
- GitHub contributor graphs and statistics
- CONTRIBUTORS.md file listing
- Special mentions in release notes
- Discord contributor roles

## 🏆 Contribution Levels

### First-Time Contributors
- Look for issues labeled `good-first-issue`
- Start with documentation improvements
- Fix small bugs or typos
- Add test cases

### Regular Contributors
- Implement new features
- Improve existing functionality
- Write comprehensive tests
- Review other contributors' PRs

### Advanced Contributors
- Design new system architectures
- Optimize performance
- Lead feature development
- Mentor new contributors

## 📞 Contact

For questions about contributing:
- **General Questions**: Use GitHub Discussions
- **Security Issues**: [security@toolboxai.io](mailto:security@toolboxai.io)
- **Code of Conduct**: [conduct@toolboxai.io](mailto:conduct@toolboxai.io)
- **Partnership Opportunities**: [partnerships@toolboxai.io](mailto:partnerships@toolboxai.io)

---

Thank you for contributing to ToolboxAI Roblox Environment! Your contributions help create better educational experiences for students worldwide. 🌟