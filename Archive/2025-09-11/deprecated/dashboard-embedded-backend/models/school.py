"""
School Model
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class School(Base, TimestampMixin):
    """School entity for managing educational institutions"""

    __tablename__ = "schools"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    principal_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Capacity and counts
    max_students: Mapped[int] = mapped_column(Integer, default=500)
    student_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Denormalized for performance
    teacher_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Denormalized for performance
    class_count: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Denormalized for performance

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Additional metadata
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    school_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # public, private, charter
    grade_levels: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # K-5, 6-8, 9-12, etc.

    def __repr__(self):
        return f"<School(id='{self.id}', name='{self.name}', city='{self.city}')>"

    def to_dict(self):
        """Convert school to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "email": self.email,
            "principal_name": self.principal_name,
            "district": self.district,
            "max_students": self.max_students,
            "student_count": self.student_count,
            "teacher_count": self.teacher_count,
            "class_count": self.class_count,
            "is_active": self.is_active,
            "logo_url": self.logo_url,
            "website": self.website,
            "founded_year": self.founded_year,
            "school_type": self.school_type,
            "grade_levels": self.grade_levels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def update_counts(self, db):
        """Update denormalized counts from related tables"""
        from .class_model import Class
        from .user import User, UserRole

        # Update student count
        self.student_count = (
            db.query(User)
            .filter(
                User.school_id == self.id,
                User.role == UserRole.STUDENT,
                User.is_active == True,
            )
            .count()
        )

        # Update teacher count
        self.teacher_count = (
            db.query(User)
            .filter(
                User.school_id == self.id,
                User.role == UserRole.TEACHER,
                User.is_active == True,
            )
            .count()
        )

        # Update class count
        self.class_count = (
            db.query(Class)
            .filter(Class.school_id == self.id, Class.is_active == True)
            .count()
        )

        db.commit()
