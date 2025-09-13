# Debugpy 2025 Integration Guide

This document outlines the modern debugpy integration patterns for VS Code 2025, following the latest Microsoft Python Debugger extension standards.

## Key Changes in 2025

### 1. Debugger Type Transition
- **Deprecated**: `"type": "python"`
- **Current**: `"type": "debugpy"`
- **Reason**: Enhanced debugging capabilities and future compatibility

### 2. No-Config Debugging
VS Code 2025 introduced no-configuration debugging:
```bash
# Run any Python script with debugpy prefix
debugpy <script.py>

# Run pytest with debugpy
debugpy -m pytest tests/
```

### 3. Enhanced Properties
New properties available in 2025:
- `"subProcess": true` - Debug subprocesses
- `"noDebug": false` - Control debug mode
- `"logToFile": true` - Enhanced logging

## Current Configuration Status

✅ **All configurations updated to use `"type": "debugpy"`**
✅ **Console property properly configured for all Python configurations**
✅ **Modern pytest integration with debugpy**
✅ **2025-specific features implemented**

## Available Debug Configurations

### Backend Services
1. **Python: FastAPI Backend (Debug)** - Main FastAPI server
2. **Python: Flask Bridge (Debug)** - Flask bridge server
3. **Python: MCP Server (Debug)** - MCP WebSocket server
4. **Python: Debug Main Entry Point** - Direct main.py debugging
5. **Python: Debug Flask Server Entry Point** - Direct Flask entry point

### Testing
1. **Python: Run Tests (Debug)** - All tests with debugpy
2. **Python: Run Unit Tests (Debug)** - Unit tests only
3. **Python: Run Integration Tests (Debug)** - Integration tests only
4. **Python: Debug Specific Test** - Specific test file
5. **Python: Debug Current Test File** - Current test file
6. **Python: Debug Pytest (Official Pattern)** - Standard pytest pattern
7. **Python: Debug Pytest (2025 Enhanced)** - Enhanced 2025 features

### Modern Features
1. **Python: Debug Current File (Modern)** - Modern file debugging
2. **Python: Debug with No-Config (2025 Feature)** - No-config debugging
3. **Python: Debug with Enhanced Logging** - Enhanced logging support
4. **Python: Debug with Profiling** - Performance profiling

### Remote Debugging
1. **Attach to Python Process** - Remote process attachment
2. **Python: Debug Tests (Remote Attach)** - Remote test debugging

## Pytest Integration

### Configuration
```ini
# pytest.ini
[pytest]
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --timeout=5
    --timeout-method=thread
    --asyncio-mode=auto
    -p no:unraisableexception
    --pdbcls=debugpy._vendored.force_pydevd.PyDB
```

### VS Code Integration
```json
{
  "name": "Python: Debug Pytest (2025 Enhanced)",
  "type": "debugpy",
  "request": "launch",
  "module": "pytest",
  "args": [
    "${file}",
    "-v",
    "--tb=short",
    "--capture=no",
    "-s"
  ],
  "console": "integratedTerminal",
  "justMyCode": false,
  "subProcess": true
}
```

## Best Practices for 2025

### 1. Use Modern Type
Always use `"type": "debugpy"` instead of the deprecated `"python"` type.

### 2. Enable Subprocess Debugging
For complex applications, enable subprocess debugging:
```json
"subProcess": true
```

### 3. Enhanced Logging
For troubleshooting, enable file logging:
```json
"logToFile": true
```

### 4. Console Integration
Always use integrated terminal for better debugging experience:
```json
"console": "integratedTerminal"
```

### 5. Environment Variables
Set proper environment variables for debugging:
```json
"env": {
  "PYTHONPATH": "${workspaceFolder}:${workspaceFolder}/src/shared",
  "ENVIRONMENT": "development",
  "DEBUG": "true"
}
```

## Troubleshooting

### Common Issues
1. **Type not recognized**: Ensure VS Code Python Debugger extension is installed
2. **Subprocess not debugging**: Enable `"subProcess": true`
3. **Console not working**: Verify `"console": "integratedTerminal"` is set
4. **Pytest not debugging**: Check `--pdbcls=debugpy._vendored.force_pydevd.PyDB` in pytest.ini

### Debug Commands
```bash
# Check debugpy installation
python -c "import debugpy; print('debugpy installed')"

# Run with debugpy prefix (2025 feature)
debugpy -m pytest tests/unit/
debugpy apps/backend/main.py

# Check VS Code Python extension
code --list-extensions | grep python
```

## Migration from Python Type

If migrating from `"type": "python"`:

1. Replace all `"type": "python"` with `"type": "debugpy"`
2. Ensure `"console": "integratedTerminal"` is present
3. Add `"subProcess": true` for complex applications
4. Update pytest integration to use `debugpy._vendored.force_pydevd.PyDB`

## Future Compatibility

This configuration follows the 2025 VS Code Python Debugger extension standards and is designed to be compatible with future updates. The use of `"type": "debugpy"` ensures long-term support and access to the latest debugging features.

## Resources

- [VS Code Python Debugger Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy)
- [Microsoft Python in VS Code Blog](https://devblogs.microsoft.com/python/)
- [Debugpy Documentation](https://github.com/microsoft/debugpy)
- [VS Code Python Debugging Guide](https://code.visualstudio.com/docs/python/debugging)
