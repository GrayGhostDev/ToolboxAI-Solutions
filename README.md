# ToolBoxAI Educational Platform

> **Complete AI-Powered Educational Platform with Roblox Integration**
> Featuring LangChain 0.3.26+ LCEL, Supabase Integration, and React 19 Frontend

## 🚀 **Overview**

ToolBoxAI is a comprehensive educational platform that combines AI-powered content generation, real-time collaboration, and immersive Roblox integration. The platform uses advanced agent systems powered by LangChain's Expression Language (LCEL) and provides robust data persistence through dual PostgreSQL + Supabase architecture.

### **🎯 Key Features**

- **🤖 AI Agent System**: 8 specialized agents using LangChain 0.3.26+ LCEL
- **📚 Educational Content**: Automated lesson, quiz, and assessment generation
- **🎮 Roblox Integration**: 3D environment generation and script optimization
- **⚡ Real-time Updates**: Supabase Realtime + Pusher Channels integration
- **⚛️ Modern Frontend**: React 19 with concurrent features and TypeScript
- **🐳 Docker Ready**: Complete containerized deployment with Supabase stack
- **🔒 Enterprise Security**: JWT authentication, RLS, and comprehensive monitoring

## 🏗️ **Architecture**

**Backend (Python 3.12)**
- **Framework**: FastAPI 0.116.1
- **AI/ML**: LangChain 0.3.26+ (LCEL), LangGraph 0.2.65+, LangSmith
- **Database**: PostgreSQL 16 + Supabase (dual strategy)
- **Cache**: Redis 7
- **Real-time**: Supabase Realtime + Pusher Channels
- **Auth**: JWT with enhanced security
- **Validation**: Pydantic v2 (2.9.0+)

**Frontend (Node.js 22)**
- **Framework**: React 19 with concurrent features
- **TypeScript**: 5.5.4 with strict mode
- **Build**: Vite 5.4.10
- **UI**: Material-UI 6.1.8 + Mantine 7.14.3
- **State**: Redux Toolkit 2.5.0
- **Real-time**: Supabase client + Pusher-js
- **Database**: Supabase client with type-safe operations

## 📋 **Development Notes**

- This repository uses Pydantic v2 and `pydantic-settings` for configuration.
- The canonical settings are in `toolboxai_settings/settings.py` with Supabase integration.
- All agents use LangChain 0.3.26+ LCEL (LangChain Expression Language) approach.

IDE setup

- Point Cursor/VS Code Python interpreter to:

  /Volumes/G-DRIVE ArmorATD/Development/Clients/ToolBoxAI-Solutions/ToolboxAI-Roblox-Environment/venv/bin/python

- Reload the window after changing the interpreter so pyright picks up installed packages.

Running tests (local)

Install dependencies into your venv and run the settings test (Python 3.11+):

```bash
python -m pip install -r ToolboxAI-Roblox-Environment/requirements.txt
python -m pytest ToolboxAI-Roblox-Environment/tests/test_settings.py
```

Compatibility

- A small compatibility adapter exists at `toolboxai_settings/compat.py` to help
  if you must run under pydantic v1; however the shared settings are v2-first.

CI

- CI runs a lightweight matrix (Python 3.11/3.12) that executes pyright and the
  `tests/test_settings.py` test.
