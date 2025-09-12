# ToolBoxAI-Solutions SDKs

Official Software Development Kits (SDKs) for integrating with ToolBoxAI-Solutions platform. These SDKs provide easy-to-use interfaces for accessing all platform features including lesson management, quiz creation, progress tracking, gamification, and Roblox environment generation.

## Available SDKs

### 🌐 [JavaScript/TypeScript SDK](javascript-sdk.md)

Modern JavaScript SDK with full TypeScript support for web and Node.js applications.

**Best for:**

- React, Angular, Vue applications
- Node.js backend services
- Browser-based educational tools
- Progressive web apps

**Key Features:**

- Promise-based async/await API
- Full TypeScript definitions
- React hooks support
- WebSocket real-time updates
- Browser and Node.js compatible

**Quick Install:**

```bash
npm install @toolboxai/sdk
# or
yarn add @toolboxai/sdk
```text
---

### 🐍 [Python SDK](python-sdk.md)

Comprehensive Python SDK for server-side integrations and data analysis.

**Best for:**

- Data analysis and reporting
- Machine learning integrations
- Automated content generation
- Batch processing
- LMS integrations

**Key Features:**

- Type hints for IDE support
- Async/await support
- Pandas integration
- Context managers
- Generator support for large datasets

**Quick Install:**

```bash
pip install toolboxai-sdk
# or
poetry add toolboxai-sdk
```text
---

### 🎮 [Roblox Lua SDK](roblox-lua-sdk.md)

Native Lua SDK optimized for Roblox Studio and in-game integrations.

**Best for:**

- Roblox Studio plugins
- In-game educational experiences
- 3D environment generation
- Real-time multiplayer learning
- Interactive assessments

**Key Features:**

- Roblox-optimized networking
- Promise-like async patterns
- Event-based updates
- Studio plugin integration
- Workspace manipulation

**Quick Install:**

```lua
-- In Roblox Studio
local ToolBoxAI = require(game.ReplicatedStorage.ToolBoxAI)
```text
## Feature Comparison

| Feature               | JavaScript/TypeScript   | Python             | Roblox Lua         |
| --------------------- | ----------------------- | ------------------ | ------------------ |
| **Authentication**    | ✅ OAuth2, API Key      | ✅ OAuth2, API Key | ✅ API Key         |
| **Async Support**     | ✅ Promises/async-await | ✅ asyncio         | ✅ Promises        |
| **Type Safety**       | ✅ TypeScript           | ✅ Type hints      | ⚠️ Luau (optional) |
| **Real-time Updates** | ✅ WebSocket            | ✅ WebSocket       | ✅ Events          |
| **Batch Operations**  | ✅                      | ✅                 | ⚠️ Limited         |
| **Offline Support**   | ✅                      | ⚠️ Limited         | ❌                 |
| **File Uploads**      | ✅                      | ✅                 | ⚠️ Limited         |
| **Data Analysis**     | ⚠️ Basic                | ✅ Pandas          | ❌                 |
| **3D Manipulation**   | ❌                      | ❌                 | ✅ Native          |
| **Package Manager**   | npm/yarn                | pip/poetry         | Roblox/Wally       |

## Common Use Cases

### Educational Web Application

**Recommended SDK**: JavaScript/TypeScript

```javascript
import { ToolBoxAI } from '@toolboxai/sdk'

const client = new ToolBoxAI({ apiKey: 'your-key' })
const lessons = await client.lessons.list({ grade: 5 })
```text
### Data Analytics Dashboard

**Recommended SDK**: Python

```python
from toolboxai import ToolBoxAI
import pandas as pd

client = ToolBoxAI(api_key='your-key')
df = client.analytics.get_progress_dataframe()
```text
### Roblox Learning Game

**Recommended SDK**: Roblox Lua

```lua
local ToolBoxAI = require(script.ToolBoxAI)
local client = ToolBoxAI.new({ apiKey = 'your-key' })
client:deployEnvironment(lessonId, workspace)
```text
## API Coverage

All SDKs provide complete coverage of the ToolBoxAI-Solutions API:

### Core Features

- ✅ **Authentication**: Login, logout, token management
- ✅ **User Management**: CRUD operations, role management
- ✅ **Lesson Management**: Create, deploy, update lessons
- ✅ **Quiz System**: Create quizzes, submit attempts, view results
- ✅ **Progress Tracking**: Track student progress, generate reports
- ✅ **Gamification**: XP, achievements, leaderboards, badges
- ✅ **Content Generation**: AI-powered lesson and quiz creation
- ✅ **LMS Integration**: Canvas, Schoology, Google Classroom
- ✅ **Roblox Integration**: Environment deployment, script injection
- ✅ **Analytics**: Performance metrics, learning analytics

### Advanced Features

- ✅ **Webhooks**: Event notifications
- ✅ **Batch Operations**: Bulk create/update
- ✅ **Real-time Updates**: WebSocket/Events
- ✅ **File Management**: Upload/download resources
- ✅ **Caching**: Built-in response caching
- ✅ **Rate Limiting**: Automatic retry with backoff
- ✅ **Error Handling**: Comprehensive error types

## Getting Started

### Step 1: Choose Your SDK

Select the SDK that best matches your development environment and use case.

### Step 2: Install the SDK

Follow the installation instructions for your chosen SDK.

### Step 3: Authenticate

```javascript
// JavaScript
const client = new ToolBoxAI({ apiKey: 'your-api-key' })
```text
```python
# Python
client = ToolBoxAI(api_key='your-api-key')
```text
```lua
-- Lua
local client = ToolBoxAI.new({ apiKey = 'your-api-key' })
```text
### Step 4: Make Your First API Call

```javascript
// JavaScript
const lesson = await client.lessons.get('lesson-id')
```text
```python
# Python
lesson = client.lessons.get('lesson-id')
```text
```lua
-- Lua
client:getLesson('lesson-id'):andThen(function(lesson)
    print(lesson.title)
end)
```text
## Authentication

All SDKs support multiple authentication methods:

### API Key Authentication

Best for server-side applications and development.

### OAuth2 Authentication

Best for user-facing applications requiring user consent.

### JWT Token Authentication

Best for secure, stateless authentication.

See individual SDK documentation for implementation details.

## Error Handling

All SDKs provide consistent error handling:

```javascript
// JavaScript
try {
  const result = await client.lessons.create(data)
} catch (error) {
  if (error.code === 'INVALID_INPUT') {
    // Handle validation error
  }
}
```text
```python
# Python
from toolboxai.exceptions import InvalidInputError

try:
    result = client.lessons.create(data)
except InvalidInputError as e:
    # Handle validation error
    print(e.message)
```text
```lua
-- Lua
client:createLesson(data):catch(function(error)
    if error.code == "INVALID_INPUT" then
        -- Handle validation error
    end
end)
```text
## Rate Limiting

All SDKs handle rate limiting automatically:

- Automatic retry with exponential backoff
- Rate limit headers exposed
- Configurable retry behavior
- Queue management for batch operations

## Support and Resources

### Documentation

- [API Reference](../03-api/README.md)
- [Authentication Guide](../03-api/authentication.md)
- [Error Codes](../03-api/error-handling.md)
- [Examples](examples/)

### Community

- GitHub: [github.com/toolboxai/sdks](https://github.com/toolboxai/sdks)
- Discord: [discord.gg/toolboxai](https://discord.gg/toolboxai)
- Forum: [forum.toolboxai.com](https://forum.toolboxai.com)

### Support

- Email: sdk-support@toolboxai.com
- Documentation: [docs.toolboxai.com](https://docs.toolboxai.com)
- Issues: [GitHub Issues](https://github.com/toolboxai/sdks/issues)

## Contributing

We welcome contributions to our SDKs! See our [Contributing Guide](https://github.com/toolboxai/sdks/CONTRIBUTING.md) for:

- Development setup
- Testing requirements
- Pull request process
- Code style guidelines

## License

All ToolBoxAI SDKs are released under the MIT License. See individual SDK repositories for details.

## Versioning

SDKs follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

## Migration Guides

Upgrading? Check our migration guides:

- [JavaScript SDK Migration](javascript-sdk.md#migration)
- [Python SDK Migration](python-sdk.md#migration)
- [Roblox Lua SDK Migration](roblox-lua-sdk.md#migration)

## Performance Benchmarks

| Operation         | JavaScript | Python | Roblox Lua |
| ----------------- | ---------- | ------ | ---------- |
| Auth (avg)        | 45ms       | 52ms   | 67ms       |
| API Call (avg)    | 120ms      | 135ms  | 145ms      |
| Batch (100 items) | 1.2s       | 0.9s   | 2.1s       |
| WebSocket latency | 15ms       | 18ms   | 25ms       |

_Benchmarks based on average response times from US-East region_

---

**Choose your SDK and start building amazing educational experiences with ToolBoxAI-Solutions!**
