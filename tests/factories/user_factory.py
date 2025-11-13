"""User-related test data factories."""

import hashlib
from datetime import datetime, timedelta, timezone

import factory
from factory import fuzzy
from faker import Faker

from .base_factory import AsyncMixin, DictFactory

fake = Faker()


class UserFactory(DictFactory, AsyncMixin):
    """Factory for generating user test data."""

    id = factory.LazyFunction(lambda: fake.uuid4())
    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    full_name = factory.LazyFunction(lambda: fake.name())
    role = fuzzy.FuzzyChoice(["student", "teacher", "admin"])
    is_active = True
    is_verified = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())

    # Profile fields
    avatar_url = factory.LazyFunction(lambda: fake.image_url())
    bio = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    phone_number = factory.LazyFunction(lambda: fake.phone_number())
    date_of_birth = factory.LazyFunction(
        lambda: fake.date_of_birth(minimum_age=13, maximum_age=80).isoformat()
    )

    # Preferences
    preferences = factory.LazyFunction(
        lambda: {
            "theme": fake.random_element(["light", "dark", "auto"]),
            "language": fake.random_element(["en", "es", "fr", "de"]),
            "notifications": {
                "email": fake.boolean(),
                "push": fake.boolean(),
                "sms": fake.boolean(),
            },
            "timezone": fake.timezone(),
        }
    )

    # Statistics
    stats = factory.LazyFunction(
        lambda: {
            "total_sessions": fake.random_int(0, 1000),
            "total_hours": fake.random_int(0, 500),
            "courses_completed": fake.random_int(0, 50),
            "assessments_taken": fake.random_int(0, 100),
            "average_score": fake.random_int(60, 100),
            "last_login": fake.date_time_this_month().isoformat(),
        }
    )

    @classmethod
    def with_password(cls, password: str | None = None, **kwargs):
        """Create user with hashed password."""
        if password is None:
            password = fake.password(length=12, special_chars=True, digits=True)

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return cls.create(hashed_password=hashed_password, **kwargs)

    @classmethod
    def with_auth_tokens(cls, **kwargs):
        """Create user with authentication tokens."""
        user = cls.create(**kwargs)
        user["access_token"] = fake.sha256()
        user["refresh_token"] = fake.sha256()
        user["token_expires_at"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        return user


class TeacherFactory(UserFactory):
    """Factory for teacher users."""

    role = "teacher"

    # Teacher-specific fields
    subjects = factory.LazyFunction(
        lambda: fake.random_elements(
            [
                "Mathematics",
                "Science",
                "English",
                "History",
                "Art",
                "Music",
                "Physical Education",
                "Computer Science",
            ],
            length=fake.random_int(1, 3),
        )
    )

    qualifications = factory.LazyFunction(
        lambda: [
            {
                "degree": fake.random_element(["B.Ed", "M.Ed", "PhD", "BA", "BS", "MS"]),
                "institution": fake.company(),
                "year": fake.year(),
            }
            for _ in range(fake.random_int(1, 3))
        ]
    )

    years_of_experience = factory.LazyFunction(lambda: fake.random_int(1, 30))

    # Classes assigned
    classes = factory.LazyFunction(
        lambda: [
            {
                "id": fake.uuid4(),
                "name": f"Class {fake.random_int(1, 12)}{fake.random_element(['A', 'B', 'C'])}",
                "subject": fake.random_element(["Math", "Science", "English"]),
                "student_count": fake.random_int(10, 30),
            }
            for _ in range(fake.random_int(1, 5))
        ]
    )


class StudentFactory(UserFactory):
    """Factory for student users."""

    role = "student"

    # Student-specific fields
    grade_level = factory.LazyFunction(lambda: fake.random_int(1, 12))

    enrollment_date = factory.LazyFunction(
        lambda: fake.date_between(start_date="-3y", end_date="today").isoformat()
    )

    parent_contact = factory.LazyFunction(
        lambda: {
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "relationship": fake.random_element(["Mother", "Father", "Guardian"]),
        }
    )

    # Academic performance
    academic_record = factory.LazyFunction(
        lambda: {
            "gpa": round(fake.random.uniform(2.0, 4.0), 2),
            "attendance_rate": fake.random_int(85, 100),
            "behavior_score": fake.random_int(70, 100),
            "awards": fake.random_elements(
                [
                    "Honor Roll",
                    "Perfect Attendance",
                    "Math Olympiad",
                    "Science Fair Winner",
                    "Student of the Month",
                ],
                length=fake.random_int(0, 3),
            ),
        }
    )

    # Enrolled courses
    enrolled_courses = factory.LazyFunction(
        lambda: [
            {
                "id": fake.uuid4(),
                "name": fake.random_element(
                    [
                        "Algebra I",
                        "Biology",
                        "English Literature",
                        "World History",
                        "Chemistry",
                        "Physics",
                        "Art Fundamentals",
                        "Computer Science",
                    ]
                ),
                "progress": fake.random_int(0, 100),
                "current_grade": fake.random_element(["A", "B", "C", "D", "F"]),
            }
            for _ in range(fake.random_int(3, 7))
        ]
    )


class AdminFactory(UserFactory):
    """Factory for admin users."""

    role = "admin"

    # Admin-specific fields
    permissions = factory.LazyFunction(
        lambda: [
            "user.create",
            "user.read",
            "user.update",
            "user.delete",
            "content.create",
            "content.read",
            "content.update",
            "content.delete",
            "system.config",
            "system.monitor",
            "system.backup",
            "reports.view",
            "reports.generate",
            "reports.export",
        ]
    )

    department = factory.LazyFunction(
        lambda: fake.random_element(["IT", "Academic Affairs", "Student Services", "Operations"])
    )

    access_level = factory.LazyFunction(
        lambda: fake.random_element(["super_admin", "admin", "moderator"])
    )

    # Audit trail
    last_actions = factory.LazyFunction(
        lambda: [
            {
                "action": fake.random_element(
                    ["created_user", "updated_content", "deleted_post", "modified_settings"]
                ),
                "timestamp": fake.date_time_this_week().isoformat(),
                "target": fake.uuid4(),
                "details": fake.sentence(),
            }
            for _ in range(fake.random_int(5, 15))
        ]
    )

    # System access
    system_access = factory.LazyFunction(
        lambda: {
            "dashboard": True,
            "analytics": True,
            "user_management": True,
            "content_management": True,
            "system_settings": True,
            "api_keys": fake.boolean(),
            "billing": fake.boolean(),
        }
    )
