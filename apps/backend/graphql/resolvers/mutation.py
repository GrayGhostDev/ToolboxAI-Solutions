"""
GraphQL Mutation resolvers
"""

import uuid
from typing import Dict, Any
from datetime import datetime, timezone

from ariadne import MutationType
from sqlalchemy import select
from passlib.context import CryptContext

from database.models import User, Course, Enrollment
from apps.backend.api.auth.auth import create_access_token

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create Mutation type
mutation = MutationType()


# Authentication mutations
@mutation.field("login")
async def resolve_login(obj, info, input: Dict[str, Any]) -> Dict[str, Any]:
    """User login mutation"""

    db = info.context["db"]
    identifier = input["identifier"]
    password = input["password"]

    # Find user by email or username
    stmt = select(User).where((User.email == identifier) | (User.username == identifier))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return {
            "success": False,
            "errors": [{"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}],
            "message": "Invalid email/username or password",
        }

    # Verify password
    if not pwd_context.verify(password, user.password_hash):
        return {
            "success": False,
            "errors": [{"code": "INVALID_CREDENTIALS", "message": "Invalid credentials"}],
            "message": "Invalid email/username or password",
        }

    # Check if user is active
    if not user.is_active:
        return {
            "success": False,
            "errors": [{"code": "ACCOUNT_INACTIVE", "message": "Account is inactive"}],
            "message": "Your account is inactive",
        }

    # Create access token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return {"success": True, "message": "Login successful", "token": token, "user": user}


@mutation.field("signup")
async def resolve_signup(obj, info, input: Dict[str, Any]) -> Dict[str, Any]:
    """User signup mutation"""

    db = info.context["db"]

    # Check if user exists
    stmt = select(User).where((User.email == input["email"]) | (User.username == input["username"]))
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "success": False,
            "errors": [{"code": "USER_EXISTS", "message": "User already exists"}],
            "message": "Email or username already taken",
        }

    # Create new user
    user = User(
        id=uuid.uuid4(),
        email=input["email"],
        username=input["username"],
        password_hash=pwd_context.hash(input["password"]),
        role=input["role"],
        first_name=input.get("firstName"),
        last_name=input.get("lastName"),
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    await db.commit()

    # Create access token
    token = create_access_token(data={"sub": str(user.id), "username": user.username})

    return {"success": True, "message": "Signup successful", "token": token, "user": user}


@mutation.field("logout")
async def resolve_logout(obj, info) -> Dict[str, Any]:
    """User logout mutation"""

    user = info.context.get("user")
    if not user:
        return {
            "success": False,
            "errors": [{"code": "NOT_AUTHENTICATED", "message": "Not authenticated"}],
            "message": "Not authenticated",
        }

    # In a real implementation, you might want to blacklist the token
    # or clear session data

    return {"success": True, "message": "Logged out successfully"}


# Course mutations
@mutation.field("createCourse")
async def resolve_create_course(obj, info, input: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new course"""

    db = info.context["db"]
    user = info.context["user"]

    if not user:
        return {
            "success": False,
            "errors": [{"code": "NOT_AUTHENTICATED", "message": "Not authenticated"}],
            "message": "Authentication required",
        }

    # Create new course
    course = Course(
        id=uuid.uuid4(),
        title=input["title"],
        code=input["code"],
        description=input["description"],
        subject=input["subject"],
        difficulty=input["difficulty"],
        teacher_id=user.id,
        status="DRAFT",
        max_students=input.get("maxStudents", 30),
        created_at=datetime.now(timezone.utc),
    )

    db.add(course)
    await db.commit()

    return {"success": True, "message": "Course created successfully", "course": course}


@mutation.field("enrollInCourse")
async def resolve_enroll_in_course(
    obj, info, courseId: str, enrollmentCode: str = None
) -> Dict[str, Any]:
    """Enroll in a course"""

    db = info.context["db"]
    user = info.context["user"]

    if not user:
        return {
            "success": False,
            "errors": [{"code": "NOT_AUTHENTICATED", "message": "Not authenticated"}],
            "message": "Authentication required",
        }

    course_id = uuid.UUID(courseId)

    # Check if course exists
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalar_one_or_none()

    if not course:
        return {
            "success": False,
            "errors": [{"code": "NOT_FOUND", "message": "Course not found"}],
            "message": "Course not found",
        }

    # Check if already enrolled
    stmt = select(Enrollment).where(
        (Enrollment.student_id == user.id) & (Enrollment.course_id == course_id)
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        return {
            "success": False,
            "errors": [{"code": "ALREADY_ENROLLED", "message": "Already enrolled"}],
            "message": "You are already enrolled in this course",
        }

    # Create enrollment
    enrollment = Enrollment(
        id=uuid.uuid4(),
        student_id=user.id,
        course_id=course_id,
        status="ACTIVE",
        enrolled_at=datetime.now(timezone.utc),
        progress=0.0,
    )

    db.add(enrollment)
    await db.commit()

    return {"success": True, "message": "Successfully enrolled in course", "enrollment": enrollment}


@mutation.field("updateProfile")
async def resolve_update_profile(obj, info, input: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile"""

    db = info.context["db"]
    user = info.context["user"]

    if not user:
        return {
            "success": False,
            "errors": [{"code": "NOT_AUTHENTICATED", "message": "Not authenticated"}],
            "message": "Authentication required",
        }

    # Update profile fields
    if input.get("firstName"):
        user.first_name = input["firstName"]
    if input.get("lastName"):
        user.last_name = input["lastName"]
    if input.get("displayName"):
        user.display_name = input["displayName"]
    if input.get("bio"):
        user.bio = input["bio"]
    if input.get("avatar"):
        user.avatar_url = input["avatar"]

    await db.commit()

    return {"success": True, "message": "Profile updated successfully", "user": user}
