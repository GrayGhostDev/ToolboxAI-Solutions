from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    display_name = Column(String)
    avatar_url = Column(String)
    role = Column(String, default="teacher")
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    school_id = Column(String, ForeignKey("schools.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RobloxEnvironment(Base):
    __tablename__ = "roblox_environments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    theme = Column(String)
    map_type = Column(String, nullable=False)
    spec = Column(JSON, nullable=False)
    status = Column(String, default="draft")  # draft, generating, ready, deployed, error
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    conversation_id = Column(String, unique=True)
    download_url = Column(String)
    preview_url = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    generation_started_at = Column(DateTime)
    generated_at = Column(DateTime)
    deployed_at = Column(DateTime)

    # Relationship
    user = relationship("User", back_populates="roblox_environments")


# Add back_populates to User
User.roblox_environments = relationship("RobloxEnvironment", back_populates="user")
