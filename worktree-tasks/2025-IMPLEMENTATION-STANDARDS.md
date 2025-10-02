# 2025 Implementation Standards for All Worktrees

**MANDATORY**: All code implementations MUST use current 2025 official methods and best practices.

---

## 🚨 Critical Requirements

### 1. Use ONLY Official 2025 Documentation

All implementations must reference and use:
- ✅ **Official documentation** from primary sources
- ✅ **Current LTS/Stable versions** (2025)
- ✅ **Modern syntax and patterns** (2025)
- ❌ **NO outdated tutorials** or deprecated methods
- ❌ **NO legacy patterns** from pre-2024

### 2. Auto-Accept Configuration

All worktree sessions have **auto-accept enabled** for:
- ✅ Corrections and improvements
- ✅ Security fixes
- ✅ Refactoring suggestions
- ✅ Modern pattern upgrades

---

## 📚 Official Sources by Technology

### Frontend (React 19.1.0)

**Official Source**: https://react.dev/

**Required Patterns (2025)**:
```typescript
// ✅ CORRECT - React 19 functional components with hooks
import { useState, useEffect } from 'react';

export function MyComponent() {
  const [state, setState] = useState<string>('');

  useEffect(() => {
    // Modern effect pattern
  }, []);

  return <div>{state}</div>;
}

// ❌ WRONG - Class components (deprecated)
class MyComponent extends React.Component {
  // This is legacy - DO NOT USE
}
```

**Server Components (2025)**:
```typescript
// ✅ Use Server Components where appropriate
async function ServerComponent() {
  const data = await fetchData();
  return <div>{data}</div>;
}
```

**Deprecated**:
- Class components
- Legacy context API
- Old lifecycle methods
- PropTypes (use TypeScript instead)

---

### TypeScript (5.9.2)

**Official Source**: https://www.typescriptlang.org/

**Required Patterns (2025)**:
```typescript
// ✅ CORRECT - Strict types with modern syntax
interface User {
  id: string;
  name: string;
  email: string;
}

function getUser(id: string): Promise<User> {
  return fetch(`/api/users/${id}`).then(r => r.json());
}

// ✅ Modern decorators (Stage 3)
class MyClass {
  @logged
  method() {}
}

// ❌ WRONG - Any types
function getData(): any { } // DO NOT USE

// ❌ WRONG - Old namespace imports
namespace MyNamespace { } // DO NOT USE
```

**Deprecated**:
- `any` types (use `unknown` or proper types)
- Namespace imports (use ES modules)
- Old decorator syntax
- Non-strict mode

---

### Python (3.12)

**Official Source**: https://docs.python.org/3.12/

**Required Patterns (2025)**:
```python
# ✅ CORRECT - Modern Python 3.12 with type hints
from typing import Optional
from pydantic import BaseModel, Field

class User(BaseModel):
    id: str
    name: str
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

async def get_user(user_id: str) -> Optional[User]:
    """Fetch user with type safety."""
    # Modern async/await pattern
    return await database.fetch_one(...)

# ✅ Pattern matching (Python 3.10+)
match status:
    case 200:
        return "OK"
    case 404:
        return "Not Found"
    case _:
        return "Error"

# ❌ WRONG - Old string formatting
name = "User %s" % user_id  # DO NOT USE

# ❌ WRONG - Missing type hints
def get_data(id):  # DO NOT USE - missing types
    pass
```

**Deprecated**:
- Python 2 syntax
- Old string formatting (`%s`, `.format()`)
- Missing type hints
- Synchronous-only code

---

### FastAPI (Latest 2025)

**Official Source**: https://fastapi.tiangolo.com/

**Required Patterns (2025)**:
```python
# ✅ CORRECT - Modern FastAPI with Pydantic v2
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, ConfigDict

app = FastAPI()

class UserCreate(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    email: str

@app.post("/users/", response_model=User)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Create user with dependency injection."""
    return await user_service.create(db, user)

# ❌ WRONG - Sync-only endpoints
@app.get("/users/")
def get_users():  # DO NOT USE - should be async
    return users
```

**Deprecated**:
- Sync-only routes (use async)
- Manual validation (use Pydantic)
- Old Pydantic v1 patterns
- Missing response models

---

### Pydantic v2

**Official Source**: https://docs.pydantic.dev/latest/

**Required Patterns (2025)**:
```python
# ✅ CORRECT - Pydantic v2 modern patterns
from pydantic import BaseModel, ConfigDict, field_validator

class User(BaseModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True
    )

    name: str
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if '@' not in v:
            raise ValueError('Invalid email')
        return v.lower()

# ❌ WRONG - Pydantic v1 patterns
class OldUser(BaseModel):
    class Config:  # DO NOT USE - v1 pattern
        frozen = True

    @validator('email')  # DO NOT USE - use field_validator
    def check_email(cls, v):
        return v
```

**Deprecated**:
- `class Config` (use `model_config = ConfigDict()`)
- `@validator` decorator (use `@field_validator`)
- `@root_validator` (use `@model_validator`)
- Direct field assignment without validation

---

### Vite (6.0.1)

**Official Source**: https://vite.dev/

**Required Patterns (2025)**:
```typescript
// vite.config.ts - ✅ CORRECT
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    proxy: {
      '/api': {
        target: 'http://localhost:8009',
        changeOrigin: true
      }
    }
  },
  optimizeDeps: {
    include: ['react', 'react-dom']
  }
})

// ❌ WRONG - Webpack config in Vite project
module.exports = { } // DO NOT USE
```

**Deprecated**:
- Webpack configurations
- CommonJS exclusive patterns
- Non-ESM modules

---

### Database (PostgreSQL + SQLAlchemy 2.0)

**Official Source**: https://docs.sqlalchemy.org/en/20/

**Required Patterns (2025)**:
```python
# ✅ CORRECT - SQLAlchemy 2.0 async patterns
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)

# Modern async query
async def get_user(session: AsyncSession, user_id: int):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

# ❌ WRONG - Old SQLAlchemy 1.x patterns
class OldUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)  # DO NOT USE
```

**Deprecated**:
- `Column()` syntax (use `Mapped` and `mapped_column`)
- Synchronous-only sessions
- Old query API (use `select()`)

---

## 🔒 Security Standards (2025)

### Environment Variables
```python
# ✅ CORRECT - Secure environment handling
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    database_url: str
    secret_key: str = Field(..., min_length=32)

# ❌ WRONG - Direct environment access
import os
SECRET_KEY = os.getenv('SECRET_KEY')  # Use Settings instead
```

### Password Hashing
```python
# ✅ CORRECT - Modern password hashing (2025)
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],  # Use Argon2 in 2025
    deprecated="auto"
)

hashed = pwd_context.hash(password)

# ❌ WRONG - Weak hashing
import hashlib
hashed = hashlib.md5(password.encode()).hexdigest()  # DO NOT USE
```

---

## 📝 Testing Standards (2025)

### Frontend (Vitest 3.2.4)
```typescript
// ✅ CORRECT - Modern Vitest patterns
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### Backend (Pytest)
```python
# ✅ CORRECT - Async pytest patterns
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/users/", json={
        "name": "Test",
        "email": "test@example.com"
    })
    assert response.status_code == 201
```

---

## ✅ Verification Checklist

Before submitting any code, verify:

- [ ] All dependencies are 2025 versions
- [ ] Official documentation referenced in comments
- [ ] No deprecated patterns used
- [ ] Type hints/types on all functions
- [ ] Modern async/await where applicable
- [ ] Security best practices followed
- [ ] Tests written using 2025 frameworks
- [ ] ESLint/Pyright passes with no warnings

---

## 🚫 Blocked Deprecated Patterns

The following will be **automatically rejected**:

- Python 2 syntax
- React class components
- Pydantic v1 patterns
- SQLAlchemy 1.x syntax
- Webpack configurations in Vite projects
- Any `any` types in TypeScript
- Missing type hints in Python
- Synchronous database queries
- Old password hashing (MD5, SHA1)
- Direct `os.getenv()` for secrets

---

## 📖 Additional Resources

- React 19: https://react.dev/blog/2024/12/05/react-19
- TypeScript 5.9: https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-9.html
- Python 3.12: https://docs.python.org/3/whatsnew/3.12.html
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic v2: https://docs.pydantic.dev/latest/migration/
- Vite 6: https://vite.dev/guide/migration.html

---

**REMEMBER**: When in doubt, check the OFFICIAL 2025 documentation. NO legacy patterns allowed!
