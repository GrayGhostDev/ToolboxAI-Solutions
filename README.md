# 🎓 ToolboxAI Solutions - Educational Technology Platform

<div align="center">

[![CI/CD Pipeline](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/workflows/🚀%20Continuous%20Integration/badge.svg)](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/actions/workflows/ci.yml)
[![Security Scanning](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/workflows/🔒%20Security%20Analysis/badge.svg)](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/node.js-18%2B-green.svg)](https://nodejs.org)

**🚀 Revolutionizing education through AI-powered content generation and immersive Roblox experiences**

[📚 Documentation](Documentation/) • [💬 Community](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/discussions) • [🐛 Issues](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/issues) • [🔒 Security](SECURITY.md)

</div>

---

## 🌟 What is ToolboxAI Solutions?

ToolboxAI Solutions is a cutting-edge educational technology platform that combines the power of artificial intelligence with the creativity of Roblox to create immersive, personalized learning experiences. Our platform empowers educators to generate engaging content, manage learning experiences, and connect with students in innovative ways.

### 🎯 Key Features

- **🧠 AI-Powered Content Generation** - Generate educational content with advanced AI models
- **🎮 Roblox Integration** - Seamless Roblox Studio plugin integration and interactive experiences  
- **📚 Learning Management System** - Comprehensive LMS integration (Schoology, Canvas)
- **🔐 Enterprise Security** - GDPR, COPPA, and FERPA compliant with multi-factor authentication

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.10+ (3.11 recommended)
- **Node.js**: 18+ 
- **PostgreSQL**: 15+
- **Redis**: 7+

### 🐍 Backend Setup

```bash
# 1. Clone the repository
git clone https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions.git
cd ToolboxAI-Solutions

# 2. Set up Python environment  
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r src/roblox-environment/requirements.txt

# 4. Set up database
cd database && python setup_database.py && cd ..

# 5. Start the FastAPI server
cd src/roblox-environment
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8008
```

### 🟢 Frontend Setup

```bash
# Install Node.js dependencies
npm install && npm run install:all

# Start the development dashboard
npm run dev:dashboard

# Access: http://localhost:3000
```

## 🏗️ Architecture

This is a monorepo containing multiple components:

```
ToolboxAI-Solutions/
├── src/roblox-environment/    # Main FastAPI backend (Python)
├── src/dashboard/             # React frontend dashboard
├── database/                  # PostgreSQL schemas and migrations
├── Documentation/             # Comprehensive documentation
├── .github/                   # CI/CD workflows and templates
└── scripts/                   # Setup and utility scripts
```

### Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2
- **Frontend**: React, TypeScript, Node.js 18+
- **Database**: PostgreSQL 15+, Redis 7+
- **AI/ML**: LangChain, OpenAI GPT-4, Anthropic Claude
- **DevOps**: GitHub Actions, Docker, comprehensive CI/CD

## 🧪 Testing

```bash
# Python tests
python -m pytest tests/ --cov=src

# JavaScript tests  
npm test

# Security scanning
bandit -r src/ && npm audit
```

## 📚 Documentation

- **[Getting Started](Documentation/01-overview/)** - Project overview and setup
- **[API Reference](Documentation/03-api/)** - Complete API documentation
- **[Development Guide](Documentation/04-implementation/)** - Development setup and guidelines
- **[User Guides](Documentation/06-user-guides/)** - End-user documentation
- **[Operations](Documentation/07-operations/)** - Deployment and operations

## 🤝 Contributing

We welcome contributions! Please see:

1. [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
2. [Code of Conduct](.github/CODE_OF_CONDUCT.md) - Community standards
3. [Issue Templates](.github/ISSUE_TEMPLATE/) - Bug reports and feature requests
4. [Security Policy](SECURITY.md) - Security vulnerability reporting

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`  
3. Make your changes with tests
4. Run tests: `npm test && python -m pytest`
5. Commit: `git commit -m 'feat: add amazing feature'`
6. Push and create a Pull Request

## 🛡️ Security

Security is paramount for our educational platform. We maintain:

- Multi-factor authentication and role-based access control
- Data encryption at rest and in transit (AES-256, TLS 1.3)  
- GDPR, COPPA, and FERPA compliance
- Regular security audits and automated vulnerability scanning

**Report security issues privately**: security@toolboxai.example.com or via [GitHub Security Advisory](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions/security/advisories/new)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 💻 Developer Notes

### Configuration
- Uses **Pydantic v2** and `pydantic-settings` for configuration
- Canonical settings in `toolboxai_settings/settings.py`
- Both server wrappers import the shared `settings` instance

### IDE Setup
- Point VS Code Python interpreter to your virtual environment
- Reload window after changing interpreter for pyright integration

### Testing
```bash
# Install dependencies and run tests
python -m pip install -r src/roblox-environment/requirements.txt
python -m pytest tests/test_settings.py
```

### Compatibility
- Small compatibility adapter at `toolboxai_settings/compat.py` for Pydantic v1
- Settings are v2-first with backward compatibility

### CI/CD
- Comprehensive GitHub Actions workflows for testing, security, and deployment
- Multi-Python version matrix (3.10, 3.11, 3.12)
- Automated security scanning and dependency updates

---

<div align="center">

**Made with ❤️ by the ToolboxAI Solutions Team**

*Empowering educators, inspiring students, transforming learning.*

[![GitHub Stars](https://img.shields.io/github/stars/ToolboxAI-Solutions/ToolboxAI-Solutions?style=social)](https://github.com/ToolboxAI-Solutions/ToolboxAI-Solutions)

</div>
