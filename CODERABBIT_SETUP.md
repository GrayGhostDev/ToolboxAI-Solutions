# CodeRabbit Setup Guide

This document provides instructions for using CodeRabbit with the ToolBoxAI-Solutions project.

## Current Configuration Status

✅ **API Key Stored in Keychain**: `coderabbit-api-key`
✅ **Environment Variable Set**: `CODERABBIT_API_KEY` in `~/.zshrc`
✅ **Project Configuration**: `.coderabbit.yml` configured for automated reviews
✅ **Badge Added**: README.md includes CodeRabbit PR review status

## Verification

### Check API Key in Keychain

```bash
# Verify the key is stored in macOS Keychain
security find-generic-password -s "coderabbit-api-key" -w | head -c 10
# Should output: cr-fa9ce67...
```

### Check Environment Variable

```bash
# Verify the environment variable is set
source ~/.zshrc
echo $CODERABBIT_API_KEY
# Should output: cr-fa9ce6760cc6aba3b96ebcfd59144d0cc45c53fc17b9fe1fdbf08bd264
```

### View Configuration

```bash
# Display the current CodeRabbit configuration
cat .coderabbit.yml
```

## GitHub Integration Setup

### Option 1: Install GitHub App (Recommended)

1. Visit https://github.com/apps/coderabbit-ai
2. Click "Install" 
3. Select "GrayGhostDev/ToolboxAI-Solutions" repository
4. Click "Authorize"
5. Grant necessary permissions

Once installed, CodeRabbit will:
- Automatically review all new Pull Requests
- Comment on changes with suggestions
- Provide real-time code quality feedback using Claude AI

### Option 2: Manual API Configuration

If you prefer API-based setup:

```bash
# The API key is already configured in your environment
# CodeRabbit will use it automatically when enabled via GitHub App
```

## Configuration Details

### Reviewed File Types

CodeRabbit reviews the following file types:
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- JSX (.jsx)
- Python (.py)
- JSON (.json)
- YAML (.yaml, .yml)
- Markdown (.md)

### Excluded Directories

These directories are automatically excluded from review:
- `node_modules/`
- `dist/`, `build/`, `.next/`
- `__pycache__/`, `.venv/`, `venv/`
- `.git/`, `.github/`
- Build caches and coverage reports

### AI Model

- **Provider**: Claude AI
- **Model**: Claude 3.5 Sonnet (latest)
- **Max Tokens**: 4096 per review
- **Integration**: Real-time suggestions enabled

### Review Focus Areas

CodeRabbit analyzes:
- Code quality
- Security issues
- Performance optimizations
- Best practices
- Error handling

## Usage

### How It Works

1. **Create a Pull Request** on the GrayGhostDev/ToolboxAI-Solutions repository
2. **CodeRabbit reviews** automatically within seconds
3. **Comments appear** on changed files with suggestions
4. **Status badge** updates showing review metrics

### Reading Reviews

When CodeRabbit posts a review:
- Look for comments on specific lines of changed code
- Check the PR conversation tab for summary comments
- Review suggestions are categorized by severity
- Click "Show resolved" to see resolved issues

### Common Review Categories

- 🔒 **Security**: Potential vulnerabilities
- ⚡ **Performance**: Optimization opportunities
- 📋 **Style**: Code formatting and consistency
- 🐛 **Bug**: Potential logic errors
- 💡 **Suggestion**: Best practice recommendations

## Disabling Reviews

If you need to disable CodeRabbit reviews temporarily:

1. Go to https://github.com/apps/coderabbit-ai
2. Click "Settings"
3. Uncheck the repository
4. Or use the disable command in PR (if available)

## Re-enabling Reviews

To re-enable reviews:

1. Visit https://github.com/apps/coderabbit-ai
2. Check the repository again
3. Create a new PR to trigger reviews

## Troubleshooting

### Reviews Not Appearing

1. Verify the GitHub App is installed: https://github.com/settings/installations
2. Confirm repository is selected in app permissions
3. Check PR for any error messages from CodeRabbit
4. Try triggering a new review with a small commit

### Configuration Issues

```bash
# Verify all environment variables are set
env | grep CODERABBIT

# Check the configuration file syntax
cat .coderabbit.yml
```

### API Key Issues

```bash
# Verify Keychain entry exists
security find-generic-password -s "coderabbit-api-key" -p

# Verify environment variable is accessible
source ~/.zshrc
echo $CODERABBIT_API_KEY
```

## Documentation

- [CodeRabbit Official Docs](https://docs.coderabbit.ai)
- [Claude Code Integration Guide](https://docs.coderabbit.ai/cli/claude-code-integration)
- [GitHub App Documentation](https://docs.coderabbit.ai/github-app)

## Support

For issues or questions:
1. Check the [CodeRabbit documentation](https://docs.coderabbit.ai)
2. Review PR comments from CodeRabbit for specific feedback
3. Check GitHub app permissions and installation status

---

**Last Updated**: November 2025
**Configuration Version**: 1.0
