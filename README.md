# ToolBoxAI Solutions

Educational Technology Platform for Roblox-based learning experiences

## Status

![CodeRabbit Pull Request Reviews](https://img.shields.io/coderabbit/prs/github/GrayGhostDev/ToolboxAI-Solutions?utm_source=oss&utm_medium=github&utm_campaign=GrayGhostDev%2FToolboxAI-Solutions&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)

## Overview

ToolBoxAI Solutions is a comprehensive educational technology platform designed to integrate with Roblox, leveraging artificial intelligence to enhance learning outcomes. This monorepo contains both frontend and backend applications built with modern web technologies.

## Project Structure

```
ToolBoxAI-Solutions/
├── apps/
│   ├── dashboard/     # React frontend application
│   └── backend/       # FastAPI Python backend
├── packages/          # Shared packages and libraries
├── infrastructure/    # Docker and deployment configurations
├── scripts/          # Utility and setup scripts
└── docs/             # Project documentation
```

## Technology Stack

- **Frontend**: React, Next.js, TypeScript, Mantine UI
- **Backend**: Python, FastAPI, Supabase
- **Package Manager**: pnpm (v9.15.0+)
- **Node.js**: >=22
- **Testing**: Playwright (E2E), Jest (Unit)
- **Deployment**: Docker, Vercel, Render

## Prerequisites

- Node.js >= 22
- pnpm >= 9.0.0
- Python 3.10+
- Docker (for containerized development)

## Getting Started

### Installation

```bash
# Install dependencies
pnpm install

# Setup environment variables
cp .env.example .env.local

# Install Playwright browsers for E2E tests
pnpm run test:e2e:install
```

### Development

```bash
# Run both frontend and backend in development mode
pnpm run dev

# Or run services individually
pnpm run dashboard:dev    # Frontend only
cd apps/backend && uvicorn main:app --reload  # Backend only
```

### Build

```bash
# Build frontend
pnpm run dashboard:build

# Build for production
pnpm run docker:build:prod
```

### Testing

```bash
# Unit tests with coverage
pnpm run test:coverage

# E2E tests
pnpm run test:e2e

# E2E tests with UI
pnpm run test:e2e:ui

# Watch mode
pnpm run test:watch
```

### Docker

```bash
# Build containers
pnpm run docker:build

# Start services
pnpm run docker:up

# View logs
pnpm run docker:logs

# Stop services
pnpm run docker:down
```

## CodeRabbit Integration

This project uses CodeRabbit for automated code reviews and AI-powered suggestions.

### Features

- Automated PR reviews on GitHub
- Local CLI code analysis
- Claude-powered AI suggestions
- Real-time code quality feedback

### Usage

**Local Code Review:**
```bash
coderabbit review --file <path/to/file>
```

**Check PR Status:**
```bash
coderabbit github review-pr --pr-number <number>
```

### Configuration

CodeRabbit is configured to review JavaScript, TypeScript, and Python files while excluding build directories and dependencies.

For more information, see [CodeRabbit Documentation](https://docs.coderabbit.ai)

## Deployment

### Frontend (Vercel)

```bash
pnpm run deploy:frontend
```

### Backend (Render)

```bash
pnpm run deploy:backend
```

### All Services

```bash
pnpm run deploy:all
```

## Environment Variables

See `.env.example` for required environment variables. Key configurations:

- Database: Supabase credentials
- Authentication: Clerk API keys
- Sentry: Error tracking and monitoring
- Render/Vercel: Deployment credentials

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Open a Pull Request

All PRs are automatically reviewed by CodeRabbit.

## License

MIT - See LICENSE file for details

## Authors

ToolBoxAI Solutions Team

## Support

For issues, questions, or contributions, please open an issue or contact the development team.

---

**Last Updated**: November 2025
