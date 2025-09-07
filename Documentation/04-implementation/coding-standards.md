# Coding Standards

This document outlines the coding standards and best practices for developers working on the Educational Platform. Following these standards ensures code consistency, maintainability, and quality across the project.

## Table of Contents

1. [General Principles](#general-principles)
2. [File Organization](#file-organization)
3. [JavaScript/TypeScript Standards](#javascripttypescript-standards)
4. [Lua Standards](#lua-standards)
5. [CSS/SCSS Standards](#cssscss-standards)
6. [HTML Standards](#html-standards)
7. [Database Access](#database-access)
8. [API Development](#api-development)
9. [Documentation Standards](#documentation-standards)
10. [Version Control Practices](#version-control-practices)
11. [Code Review Process](#code-review-process)

## General Principles

### Readability and Maintainability

- Write code that is easy to read, understand, and maintain
- Prioritize clarity over cleverness or brevity
- Follow the principle of least surprise; code should behave as expected
- Write self-documenting code with meaningful variable and function names

### Consistency

- Follow established patterns and conventions within the codebase
- Use the same style throughout a file and across related files
- When modifying existing code, match the style of surrounding code

### Performance

- Consider performance implications, especially for frequently executed code
- Optimize for readability first, then for performance when necessary
- Document performance considerations for complex operations

### Security

- Follow secure coding practices
- Never trust user input without validation
- Avoid exposing sensitive information in client-side code
- Use parameterized queries for database operations

## File Organization

### Project Structure

The project follows this high-level structure:

```
educational-platform/
├── api/                  # Backend API services
│   ├── controllers/      # API endpoint handlers
│   ├── models/           # Data models
│   ├── routes/           # Route definitions
│   ├── middleware/       # Express middleware
│   ├── services/         # Business logic
│   └── utils/            # Helper functions
├── client/               # Frontend application
│   ├── components/       # React components
│   ├── hooks/            # Custom React hooks
│   ├── pages/            # Page components
│   ├── context/          # React context providers
│   ├── styles/           # Global styles
│   └── utils/            # Helper functions
├── lua/                  # Roblox Lua scripts
│   ├── controllers/      # UI controllers
│   ├── models/           # Data models
│   ├── services/         # Service modules
│   └── utils/            # Helper functions
├── shared/               # Shared code between client and server
│   ├── constants/        # Shared constants
│   ├── types/            # TypeScript type definitions
│   └── utils/            # Shared utility functions
└── tests/                # Test files
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

### File Naming

- Use descriptive, meaningful names that reflect the file's purpose
- Follow consistent naming patterns:
  - `kebab-case` for directories and files in the web client
  - `PascalCase` for React components and their files
  - `camelCase` for JavaScript/TypeScript utility files
  - `snake_case` for Lua files

### File Organization

- Each file should have a single responsibility
- Limit file size to 400 lines where possible; split larger files into modules
- Order imports, constants, functions, and exports in a consistent manner
- Group related functionality together

## JavaScript/TypeScript Standards

### Language Version

- Use TypeScript for all new code
- Target ECMAScript 2020 features for compatibility

### TypeScript Configuration

- Use strict mode in TypeScript
- Explicitly define types; minimize use of `any`
- Use interfaces for object shapes and class contracts
- Prefer type aliases for unions, intersections, and function types

### Formatting

- Use 2 spaces for indentation
- Maximum line length of 100 characters
- Use semicolons to terminate statements
- Use single quotes for string literals
- Always use curly braces for control structures, even for single-line blocks
- Place opening braces on the same line as the statement

```typescript
// Good
if (condition) {
  doSomething();
}

// Avoid
if (condition) doSomething();
```

### Naming Conventions

- Use `camelCase` for variables, functions, and methods
- Use `PascalCase` for classes, interfaces, types, and React components
- Use `ALL_CAPS` for constants
- Use descriptive names that indicate purpose or behavior

```typescript
// Good
const maxRetryAttempts = 3;
function calculateTotalScore(scores: number[]): number { ... }
class UserAuthentication { ... }
interface CourseProperties { ... }
```

### Functional Programming

- Prefer pure functions where appropriate
- Use array methods like `map`, `filter`, and `reduce` instead of loops
- Avoid mutating function parameters
- Use the spread operator for creating new objects/arrays instead of mutation

```typescript
// Good
const newArray = originalArray.map(item => transformItem(item));

// Avoid
const newArray = [];
for (let i = 0; i < originalArray.length; i++) {
  newArray.push(transformItem(originalArray[i]));
}
```

### Asynchronous Code

- Prefer async/await over Promise chains for readability
- Handle errors with try/catch blocks
- Always return or await Promises to ensure proper error propagation

```typescript
// Good
async function fetchUserData(userId: string): Promise<UserData> {
  try {
    const response = await api.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch user data', { userId, error });
    throw new Error('Failed to fetch user data');
  }
}
```

### React-Specific Standards

- Use functional components with hooks instead of class components
- Use named exports for components
- Destructure props in function parameters
- Follow component file structure:
  1. Imports
  2. Types/Interfaces
  3. Constants
  4. Helper functions
  5. Component definition
  6. Export statement

```typescript
// Component.tsx
import React, { useState, useEffect } from 'react';
import { SomeType } from '../types';
import { someUtil } from '../utils';

interface ComponentProps {
  title: string;
  items: SomeType[];
  onSelect: (item: SomeType) => void;
}

const ITEM_LIMIT = 10;

function filterItems(items: SomeType[]): SomeType[] {
  return items.filter(item => item.isActive);
}

export function Component({ title, items, onSelect }: ComponentProps): JSX.Element {
  const [selectedItem, setSelectedItem] = useState<SomeType | null>(null);

  useEffect(() => {
    // Effect logic
  }, [items]);

  return (
    <div>
      {/* Component JSX */}
    </div>
  );
}
```

## Lua Standards

### Language Features

- Target Lua 5.1 for Roblox compatibility
- Use Roblox's Luau features where appropriate
- Follow object-oriented patterns using metatables

### Formatting

- Use 2 spaces for indentation
- Maximum line length of 100 characters
- Place opening braces on the same line as the statement
- Use spaces around operators and after commas

```lua
-- Good
local function calculateDistance(pointA, pointB)
  local xDiff = pointA.X - pointB.X
  local yDiff = pointA.Y - pointB.Y
  return math.sqrt(xDiff * xDiff + yDiff * yDiff)
end
```

### Naming Conventions

- Use `PascalCase` for classes/modules
- Use `camelCase` for variables and functions
- Use `ALL_CAPS` for constants
- Prefix private functions and variables with an underscore

```lua
-- Good
local DEFAULT_SPEED = 16

local function _privateHelper()
  -- Implementation
end

local function calculateVelocity(direction, speed)
  -- Implementation
end

local PlayerController = {}
PlayerController.__index = PlayerController

function PlayerController.new()
  local self = setmetatable({}, PlayerController)
  self._speed = DEFAULT_SPEED
  return self
end

function PlayerController:move(direction)
  local velocity = calculateVelocity(direction, self._speed)
  -- Implementation
end
```

### Module Structure

- Use the module pattern for all Lua modules
- Export a module table with public functions
- Keep module implementations encapsulated
- Follow consistent module structure:
  1. Module dependencies
  2. Private constants
  3. Private functions
  4. Module table definition
  5. Constructor (if applicable)
  6. Public methods
  7. Return statement

```lua
-- Module structure example
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SomeOtherModule = require(ReplicatedStorage.Modules.SomeOtherModule)

-- Private constants
local DEFAULT_VALUE = 10

-- Private functions
local function _privateFunction()
  -- Implementation
end

-- Module definition
local MyModule = {}
MyModule.__index = MyModule

-- Constructor
function MyModule.new()
  local self = setmetatable({}, MyModule)
  self._privateValue = DEFAULT_VALUE
  return self
end

-- Public methods
function MyModule:publicMethod()
  return _privateFunction() + self._privateValue
end

-- Return the module
return MyModule
```

### Best Practices

- Initialize all variables to avoid nil errors
- Use local variables whenever possible
- Cache references to frequently accessed values
- Avoid global variables
- Use proper error handling with pcall/xpcall

## CSS/SCSS Standards

### Organization

- Use SCSS for styling
- Organize styles using a methodology like BEM or component-based CSS
- Split styles into logical files by component or feature
- Use variables for colors, spacing, fonts, and other design constants

### Formatting

- Use 2 spaces for indentation
- Place opening braces on the same line as the selector
- Use one selector per line in multi-selector rulesets
- Include a space before the opening brace
- Place closing braces on a new line
- Include a space after the colon of a declaration
- End all declarations with a semicolon
- Use lowercase and shorthand hex values, e.g., `#fff`
- Use single quotes for attribute values, e.g., `input[type='checkbox']`

```scss
// Good
.component,
.component-child {
  display: block;
  margin: 0;
  color: #fff;
}
```

### Naming Conventions

- Use descriptive class names that reflect purpose, not presentation
- Follow BEM methodology for naming: `block__element--modifier`
- Use kebab-case for class names and custom properties

```scss
// Good
.user-profile {
  &__avatar {
    border-radius: 50%;

    &--large {
      width: 150px;
      height: 150px;
    }
  }
}
```

### Best Practices

- Use CSS variables for theming and reusable values
- Avoid overly specific selectors
- Minimize use of !important
- Use flexbox and grid for layouts
- Ensure designs are responsive and accessible
- Comment complex or non-obvious CSS

## HTML Standards

### Formatting

- Use 2 spaces for indentation
- Use lowercase element names, attributes, and values
- Use double quotes for attribute values
- Close all HTML elements, including self-closing tags
- Omit the `type` attribute for stylesheets and scripts

```html
<!-- Good -->
<section class="content-section">
  <h2 class="content-section__title">Section Title</h2>
  <img src="image.jpg" alt="Descriptive text" />
</section>
```

### Semantic HTML

- Use semantic HTML elements (`<article>`, `<section>`, `<nav>`, etc.)
- Use appropriate heading levels (`<h1>` through `<h6>`)
- Use `<button>` for interactive controls, not `<div>` or `<span>`
- Use `<a>` only for navigation to a URL

### Accessibility

- Include appropriate ARIA attributes when necessary
- Ensure all interactive elements are keyboard accessible
- Provide `alt` text for images
- Maintain proper heading hierarchy
- Use labels for form controls

```html
<!-- Good -->
<button
  type="button"
  aria-pressed="false"
  class="toggle-button"
>
  Toggle Feature
</button>

<img src="chart.png" alt="Chart showing user growth over time" />

<label for="username">Username</label>
<input type="text" id="username" name="username" />
```

## Database Access

### Query Standards

- Use parameterized queries to prevent SQL injection
- Avoid raw SQL in application code; use ORMs or query builders
- Keep queries simple and focused on a single responsibility
- Use explicit column names in SELECT statements, avoid SELECT *
- Include appropriate indexes for frequently queried fields

```typescript
// Good - using query builder
const users = await db
  .select('id', 'username', 'created_at')
  .from('users')
  .where('status', 'active')
  .orderBy('created_at', 'desc')
  .limit(10);

// Avoid - raw SQL
const users = await db.raw(`SELECT * FROM users WHERE status = 'active' ORDER BY created_at DESC LIMIT 10`);
```

### Database Access Layer

- Encapsulate database operations in service or repository modules
- Include appropriate error handling for database operations
- Use transactions for operations that require atomicity
- Implement retry logic for transient failures

```typescript
// Service example
export class UserService {
  constructor(private db: Database) {}

  async getUserById(id: string): Promise<User | null> {
    try {
      return await this.db.users.findUnique({ where: { id } });
    } catch (error) {
      logger.error('Database error when fetching user', { userId: id, error });
      throw new DatabaseError('Failed to fetch user');
    }
  }

  async createUser(userData: UserCreateData): Promise<User> {
    return this.db.$transaction(async (tx) => {
      const user = await tx.users.create({ data: userData });
      await tx.userPreferences.create({
        data: {
          userId: user.id,
          // Default preferences
        }
      });
      return user;
    });
  }
}
```

## API Development

### RESTful API Design

- Follow RESTful principles for API endpoints
- Use nouns for resource names, not verbs
- Use HTTP methods appropriately (GET, POST, PUT, PATCH, DELETE)
- Use plural resource names for consistency
- Structure URLs hierarchically

```
# Good
GET    /api/courses                 # List courses
POST   /api/courses                 # Create a course
GET    /api/courses/{id}            # Get a course
PUT    /api/courses/{id}            # Update a course
DELETE /api/courses/{id}            # Delete a course
GET    /api/courses/{id}/lessons    # List lessons for a course
```

### Response Format

- Use consistent response formats across all endpoints
- Include appropriate HTTP status codes
- Provide meaningful error messages

```json
// Success response
{
  "success": true,
  "data": {
    "id": "course-123",
    "title": "Introduction to Programming",
    "description": "Learn the basics of programming",
    "createdAt": "2023-01-15T08:30:00Z"
  }
}

// Error response
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested course was not found",
    "details": {
      "courseId": "course-123"
    }
  }
}
```

### API Documentation

- Document all API endpoints using OpenAPI/Swagger
- Include:
  - URL and HTTP method
  - Request parameters and body schema
  - Response schema for success and error cases
  - Authentication requirements
  - Example requests and responses

### Authentication and Authorization

- Use appropriate authentication mechanisms (JWT, OAuth)
- Implement proper authorization checks for protected resources
- Document authentication requirements clearly
- Rate limit APIs to prevent abuse

## Documentation Standards

### Code Comments

- Use JSDoc or TSDoc comments for functions, classes, and interfaces
- Comment complex algorithms and non-obvious code
- Avoid comments that simply restate what the code does
- Keep comments up-to-date when modifying code

```typescript
/**
 * Calculates the average score from a collection of student quiz results.
 * Filters out incomplete submissions before calculating.
 *
 * @param submissions - Array of quiz submissions to process
 * @returns The average score as a percentage (0-100)
 * @throws {Error} If no valid submissions are found
 */
function calculateAverageScore(submissions: QuizSubmission[]): number {
  const validSubmissions = submissions.filter(sub => sub.status === 'completed');

  if (validSubmissions.length === 0) {
    throw new Error('No valid submissions found');
  }

  const totalScore = validSubmissions.reduce((sum, sub) => sum + sub.score, 0);
  return (totalScore / validSubmissions.length) * 100;
}
```

### Documentation Files

- Maintain up-to-date README files in each major directory
- Provide comprehensive module documentation
- Include usage examples for public APIs and components
- Document known limitations and edge cases

### Architecture Documentation

- Document the overall system architecture
- Include component diagrams and data flow diagrams
- Keep architecture documentation updated as the system evolves

## Version Control Practices

### Branching Strategy

- Use a Git Flow branching model:
  - `main` - Production code
  - `develop` - Integration branch for feature development
  - `feature/*` - New features
  - `bugfix/*` - Bug fixes
  - `release/*` - Release preparation
  - `hotfix/*` - Production hotfixes

### Commit Messages

- Write clear, descriptive commit messages
- Follow the conventional commits format:
  - `feat:` - A new feature
  - `fix:` - A bug fix
  - `docs:` - Documentation changes
  - `style:` - Code style changes (formatting, etc.)
  - `refactor:` - Code changes that neither fix bugs nor add features
  - `perf:` - Performance improvements
  - `test:` - Adding or correcting tests
  - `chore:` - Changes to the build process or auxiliary tools

```
feat(course): add pagination to course listing

Add pagination support to the course listing API and UI to improve
performance with large course catalogs.

Includes:
- API changes to support limit/offset parameters
- UI updates to show pagination controls
- Unit tests for pagination logic

Fixes #123
```

### Pull Requests

- Create descriptive pull request titles
- Include a detailed description of changes
- Reference related issues
- Keep pull requests focused on a single responsibility
- Include screenshots or videos for UI changes
- Make sure all tests pass before requesting review

## Code Review Process

### Review Checklist

Before submitting code for review, ensure:

- Code follows all project standards
- Tests are included and passing
- Documentation is updated
- No debugging code remains
- No unnecessary dependencies are added
- Performance considerations are addressed
- Security best practices are followed

### Review Guidelines

When reviewing others' code:

- Be respectful and constructive
- Focus on the code, not the person
- Provide specific, actionable feedback
- Explain reasoning behind suggestions
- Consider alternatives before suggesting changes
- Approve once all critical issues are addressed

### Tooling

The following tools are configured to enforce standards:

- ESLint for JavaScript/TypeScript linting
- Prettier for code formatting
- Stylelint for CSS/SCSS linting
- Luacheck for Lua linting
- Husky for pre-commit hooks
- Jest for JavaScript testing
- Playwright for end-to-end testing

Configure your editor to use these tools for the best development experience.

---

These coding standards are a living document. If you have suggestions for improvements, please discuss them with the team.
