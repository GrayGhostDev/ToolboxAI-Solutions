# Data Models Documentation

## Overview

This directory contains comprehensive documentation for all data models used in ToolBoxAI-Solutions. The models are organized by functional domain and include both database schemas and API data transfer objects (DTOs).

## Model Categories

### [User Models](user-models.md)
User account management and authentication:
- User profiles and settings
- Role definitions and permissions
- Authentication tokens
- User preferences

### [Lesson Models](lesson-models.md)
Educational content structures:
- Lesson definitions
- Content sections
- Media attachments
- Curriculum mapping

### [Progress Models](progress-models.md)
Student progress and performance tracking:
- Course progress
- Activity logs
- Learning analytics
- Performance reports

### [Quiz Models](quiz-models.md)
Assessment and evaluation:
- Quiz definitions
- Question types
- Quiz attempts
- Scoring and feedback

### [Analytics Models](analytics-models.md)
Analytics and reporting:
- Aggregated metrics
- Performance indicators
- Engagement tracking
- Predictive analytics

## Data Model Conventions

### Naming Conventions
- **Tables**: snake_case (e.g., `student_progress`)
- **Columns**: snake_case (e.g., `created_at`)
- **Models**: PascalCase (e.g., `StudentProgress`)
- **Enums**: UPPER_SNAKE_CASE (e.g., `USER_ROLE`)

### Common Fields
All models include these standard fields unless specified otherwise:
```lua
{
    id = string,           -- UUID primary key
    created_at = DateTime, -- Creation timestamp
    updated_at = DateTime, -- Last modification timestamp
    created_by = string,   -- User ID who created the record
    updated_by = string    -- User ID who last updated the record
}
```

### Data Types

#### Lua Notation (for Roblox)
```lua
string    -- Text data
number    -- Numeric values (integers or floats)
boolean   -- True/false values
DateTime  -- ISO 8601 timestamp strings
table     -- Nested objects or arrays
any       -- Variable type
```

#### Database Types (PostgreSQL)
```sql
UUID          -- Unique identifiers
VARCHAR(n)    -- Variable-length strings
TEXT          -- Unlimited text
INTEGER       -- Whole numbers
DECIMAL(p,s)  -- Precise decimal numbers
TIMESTAMP     -- Date and time
JSONB         -- JSON data with indexing
BOOLEAN       -- True/false values
```

### Relationships

#### One-to-Many
```lua
-- Parent model
Course = {
    id = string,
    lessons = {Lesson} -- Array of related lessons
}

-- Child model
Lesson = {
    id = string,
    course_id = string -- Foreign key reference
}
```

#### Many-to-Many
```lua
-- Junction table approach
StudentCourse = {
    student_id = string,
    course_id = string,
    enrolled_at = DateTime
}
```

### Validation Rules

Common validation patterns used across models:

```lua
-- Required fields
required = {"id", "title", "created_at"}

-- String length constraints
title = {min = 1, max = 255}

-- Numeric ranges
score = {min = 0, max = 100}

-- Enum values
status = {"active", "inactive", "pending"}

-- Format patterns
email = "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
```

## Database Schema

### Entity Relationship Overview
```
Users ──┬──< StudentProgress >──┬── Lessons
        │                        │
        ├──< QuizAttempts >──────┤
        │                        │
        └──< ActivityLogs        └── Courses
```

### Indexing Strategy

Primary indexes on:
- All `id` fields (primary keys)
- Foreign key relationships
- Frequently queried fields (`user_id`, `lesson_id`, `created_at`)

Composite indexes for:
- Common query patterns
- Reporting aggregations
- Search operations

### Data Retention

| Model Type | Retention Period | Archive Strategy |
|------------|-----------------|------------------|
| User Data | Account lifetime + 1 year | Soft delete, then archive |
| Progress Data | 3 years active, then archive | Move to cold storage |
| Activity Logs | 1 year active, then aggregate | Aggregate to analytics |
| Quiz Attempts | 2 years | Archive with course data |
| Analytics | Indefinite (aggregated) | No deletion |

## API Data Transfer

### Request DTOs
Used for incoming data from clients:
```python
class CreateLessonRequest:
    title: str
    content: str
    grade_level: int
    subject: str
```

### Response DTOs
Used for sending data to clients:
```python
class LessonResponse:
    id: str
    title: str
    content: str
    created_at: datetime
    author: UserSummary
```

### Transformation
```python
def to_response(model: Lesson) -> LessonResponse:
    """Transform database model to API response"""
    return LessonResponse(
        id=model.id,
        title=model.title,
        # ... field mapping
    )
```

## Privacy and Security

### PII Handling
Fields containing Personally Identifiable Information (PII):
- User email addresses
- Student names
- IP addresses
- Location data

These fields require:
- Encryption at rest
- Audit logging for access
- Compliance with COPPA/FERPA/GDPR

### Data Masking
Sensitive fields in non-production environments:
```python
def mask_pii(data: dict) -> dict:
    data['email'] = 'user***@example.com'
    data['ip_address'] = '***.***.***.**'
    return data
```

## Migration Strategy

### Schema Versioning
- Use semantic versioning for schema changes
- Maintain backward compatibility for 2 major versions
- Document all breaking changes

### Migration Scripts
```sql
-- Example migration
ALTER TABLE lessons 
ADD COLUMN difficulty_level INTEGER DEFAULT 1;

-- Rollback script
ALTER TABLE lessons 
DROP COLUMN difficulty_level;
```

## Best Practices

1. **Normalization**: Follow 3NF for transactional data
2. **Denormalization**: Strategic denormalization for read-heavy operations
3. **Consistency**: Use transactions for related updates
4. **Validation**: Validate at both application and database levels
5. **Documentation**: Keep model documentation synchronized with code

## Tools and Utilities

### Model Generation
```bash
# Generate TypeScript interfaces from models
npm run generate:types

# Generate database migrations
npm run generate:migration

# Validate model consistency
npm run validate:models
```

### Documentation Generation
```bash
# Generate model documentation
npm run docs:models

# Generate ER diagrams
npm run generate:erd
```

---

*For implementation details, see [System Design](../system-design.md). For API usage, see [API Documentation](../../03-api/).*