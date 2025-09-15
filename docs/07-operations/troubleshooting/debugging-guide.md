# Debugging Guide for ToolBoxAI Solutions

This comprehensive guide covers debugging and testing configurations for the ToolBoxAI Solutions project.

## Table of Contents

1. [Overview](#overview)
2. [Python Backend Debugging](#python-backend-debugging)
3. [React Frontend Debugging](#react-frontend-debugging)
4. [Testing Debugging](#testing-debugging)
5. [Performance Profiling](#performance-profiling)
6. [Memory Profiling](#memory-profiling)
7. [Database Debugging](#database-debugging)
8. [API Debugging](#api-debugging)
9. [WebSocket Debugging](#websocket-debugging)
10. [Troubleshooting](#troubleshooting)

## Overview

The ToolBoxAI Solutions project includes comprehensive debugging and testing configurations for both Python backend and React frontend components. All debugging tools are properly organized in the project structure:

```
config/
├── development/
│   └── debug-config.py          # Debug configuration
├── ide/
│   └── debug-settings.json      # IDE debugging settings
└── testing/
    └── pytest-debug.ini         # Debug-specific pytest config

scripts/
├── debug_server.py              # Debug server script
└── debug_utils.py               # Debug utilities

.vscode/
└── launch.json                  # VS Code debug configurations

apps/dashboard/
├── vitest.config.ts             # Frontend test debugging config
└── src/test/setup.ts            # Frontend test setup
```

## Python Backend Debugging

### VS Code Debug Configurations

The project includes comprehensive VS Code debugging configurations in `.vscode/launch.json`:

#### Available Configurations

1. **Python: FastAPI Backend (Debug)**
   - Debug the main FastAPI application
   - Uses debugpy for remote debugging
   - Port: 8008, Debug port: 5678

2. **Python: Flask Bridge (Debug)**
   - Debug the Flask bridge server
   - Uses debugpy for remote debugging
   - Port: 8008, Debug port: 5678

3. **Python: MCP Server (Debug)**
   - Debug the MCP server
   - Uses debugpy for remote debugging
   - Port: 8008, Debug port: 5678

4. **Python: Run Tests (Debug)**
   - Debug all tests
   - Uses debugpy with pytest
   - Includes comprehensive logging

5. **Python: Run Unit Tests (Debug)**
   - Debug unit tests only
   - Uses debugpy with pytest
   - Focused on unit test debugging

6. **Python: Run Integration Tests (Debug)**
   - Debug integration tests only
   - Uses debugpy with pytest
   - Includes external service debugging

7. **Python: Debug Specific Test**
   - Debug a specific test file
   - Interactive test selection
   - Detailed test debugging

8. **Python: Debug Current File**
   - Debug the currently open file
   - Quick debugging for any Python file

9. **Python: Debug with Profiling**
   - Debug with performance profiling
   - Includes memory and performance monitoring

10. **Attach to Python Process**
    - Attach to running Python process
    - Remote debugging support

### Debug Server Script

Use the debug server script for comprehensive debugging:

```bash
# Debug FastAPI backend
python scripts/debug_server.py --service fastapi --debug

# Debug Flask bridge with profiling
python scripts/debug_server.py --service flask --debug --profile

# Debug MCP server with memory profiling
python scripts/debug_server.py --service mcp --debug --memory

# Debug with custom port
python scripts/debug_server.py --service fastapi --debug --port 9000
```

### Debug Utilities

The `scripts/debug_utils.py` module provides comprehensive debugging utilities:

```python
from scripts.debug_utils import DebugUtils, profile_function, debug_test

# Create debug instance
debug = DebugUtils()

# Profile function performance
@profile_function
def my_function():
    # Your code here
    pass

# Debug test execution
@debug_test
def test_my_function():
    # Your test code here
    pass

# Memory usage monitoring
debug.log_memory_usage("After operation")

# System information
debug.log_system_info()

# Create debug report
debug.create_debug_report("debug_report.txt")
```

## React Frontend Debugging

### VS Code Debug Configurations

1. **React: Debug Frontend**
   - Debug the Vite development server
   - Port: 5179
   - Includes hot reload debugging

2. **React: Debug Tests**
   - Debug Vitest test runner
   - Includes UI debugging
   - Port: 5179

3. **React: Debug Specific Test**
   - Debug specific test files
   - Interactive test selection

4. **Attach to Node Process**
   - Attach to running Node.js process
   - Remote debugging support

### Frontend Test Configuration

The frontend includes comprehensive test debugging configuration in `apps/dashboard/vitest.config.ts`:

- **Debug Settings**: Enhanced logging and error reporting
- **Coverage**: Comprehensive code coverage reporting
- **Performance**: Memory usage monitoring
- **Isolation**: Proper test isolation
- **Reporting**: HTML and JSON test reports

### Frontend Test Setup

The `apps/dashboard/src/test/setup.ts` file provides:

- Enhanced error logging
- Mock utilities
- Debug helpers
- Test environment setup
- Global test utilities

## Testing Debugging

### Pytest Debug Configuration

The project includes debug-specific pytest configuration in `config/testing/pytest-debug.ini`:

- **Debug Logging**: Comprehensive test logging
- **Interactive Debugging**: PDB integration with debugpy
- **Timeout Handling**: Proper timeout management
- **Coverage**: Debug-specific coverage settings
- **Markers**: Custom test markers for debugging

### Running Debug Tests

```bash
# Run all tests with debugging
pytest --config-file=config/testing/pytest-debug.ini

# Run specific test with debugging
pytest tests/unit/test_example.py --config-file=config/testing/pytest-debug.ini

# Run tests with coverage and debugging
pytest --config-file=config/testing/pytest-debug.ini --cov=apps.backend --cov-report=html

# Run tests with profiling
pytest --config-file=config/testing/pytest-debug.ini --profile
```

### Test Debugging Utilities

```python
from scripts.debug_utils import debug_test, debug_async_test

# Debug synchronous test
@debug_test
def test_my_function():
    # Your test code here
    pass

# Debug asynchronous test
@debug_async_test
async def test_async_function():
    # Your async test code here
    pass
```

## Performance Profiling

### Backend Profiling

```python
from scripts.debug_utils import profile_function, profile_async_function

# Profile synchronous function
@profile_function
def my_function():
    # Your code here
    pass

# Profile asynchronous function
@profile_async_function
async def my_async_function():
    # Your async code here
    pass
```

### Frontend Profiling

The frontend includes built-in performance monitoring:

```typescript
// Profile component rendering
import { debugTestUtils } from './test/setup'

const MyComponent = () => {
  debugTestUtils.debugRender(MyComponent, { prop1: 'value' })
  // Component code
}
```

## Memory Profiling

### Backend Memory Profiling

```python
from scripts.debug_utils import DebugUtils

debug = DebugUtils()

# Log memory usage
debug.log_memory_usage("Before operation")

# Get detailed memory info
memory_info = debug.memory_usage()
print(f"Memory usage: {memory_info['rss']:.2f}MB")

# Force garbage collection
debug.force_garbage_collection()
```

### Frontend Memory Profiling

The frontend test configuration includes memory usage monitoring:

```typescript
// Enable memory profiling in tests
const config = {
  test: {
    logHeapUsage: true,
    // ... other config
  }
}
```

## Database Debugging

### Enable Database Query Logging

```python
from scripts.debug_utils import DebugUtils

debug = DebugUtils()

# Enable database query debugging
debug.debug_database_queries(engine)
```

### Database Debug Configuration

The debug configuration includes database debugging settings:

```python
# In config/development/debug-config.py
DB_ECHO = True
DB_ECHO_POOL = True
DB_POOL_PRE_PING = True
```

## API Debugging

### Enable API Request/Response Logging

```python
from scripts.debug_utils import DebugUtils

debug = DebugUtils()

# Enable API debugging
debug.debug_api_requests(app)
```

### API Debug Configuration

```python
# In config/development/debug-config.py
API_DEBUG = True
API_LOG_REQUESTS = True
API_LOG_RESPONSES = True
```

## WebSocket Debugging

### Enable WebSocket Message Logging

```python
from scripts.debug_utils import DebugUtils

debug = DebugUtils()

# Enable WebSocket debugging
websocket = debug.debug_websocket_messages(websocket)
```

### WebSocket Debug Configuration

```python
# In config/development/debug-config.py
WS_DEBUG = True
WS_LOG_MESSAGES = True
```

## Troubleshooting

### Common Issues

1. **Debugpy Connection Issues**
   - Ensure debugpy is installed: `pip install debugpy`
   - Check port availability (default: 5678)
   - Verify firewall settings

2. **Test Timeout Issues**
   - Increase timeout in pytest configuration
   - Check for infinite loops in tests
   - Verify async test setup

3. **Memory Issues**
   - Use memory profiling to identify leaks
   - Check for circular references
   - Monitor garbage collection

4. **Coverage Issues**
   - Verify source paths in coverage configuration
   - Check exclude patterns
   - Ensure tests are running

### Debug Commands

```bash
# Check debugpy installation
python -c "import debugpy; print('debugpy installed')"

# Run debug server
python scripts/debug_server.py --service fastapi --debug

# Run tests with debugging
pytest --config-file=config/testing/pytest-debug.ini

# Check memory usage
python -c "from scripts.debug_utils import DebugUtils; DebugUtils().log_memory_usage()"

# Generate debug report
python -c "from scripts.debug_utils import DebugUtils; DebugUtils().create_debug_report()"
```

### Debug Logs

Debug logs are stored in:
- `logs/debug.log` - General debug logs
- `debug-reports/` - Debug reports and profiles
- `test-reports/` - Test reports and coverage

### Support

For debugging support:
1. Check the debug logs
2. Review the debug report
3. Use the debug utilities
4. Consult the troubleshooting section
5. Check the project documentation

## Best Practices

1. **Use Debug Configurations**: Always use the provided debug configurations
2. **Enable Logging**: Use comprehensive logging for debugging
3. **Profile Performance**: Use profiling tools to identify bottlenecks
4. **Monitor Memory**: Use memory profiling to prevent leaks
5. **Test Isolation**: Ensure proper test isolation
6. **Clean Up**: Always clean up after debugging sessions
7. **Document Issues**: Document debugging solutions for future reference

This debugging guide provides comprehensive coverage of all debugging and testing capabilities in the ToolBoxAI Solutions project. Use it as a reference for debugging issues and setting up debugging environments.
