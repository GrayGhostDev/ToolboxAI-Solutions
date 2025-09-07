"""
Database Models for Educational Platform
"""

from .base import Base, TimestampMixin
from .user import User, UserRole
from .class_model import Class, ClassEnrollment
from .lesson import Lesson, LessonProgress, LessonStatus, LessonDifficulty
from .assessment import Assessment, AssessmentSubmission, AssessmentQuestion
from .gamification import XPTransaction, Badge, UserBadge, LeaderboardEntry, XPSource, BadgeCategory, BadgeRarity
from .compliance import ConsentRecord, DataRetention, ComplianceLog, ConsentType, ComplianceStatus
from .message import Message, MessageRecipient

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "Class",
    "ClassEnrollment",
    "Lesson",
    "LessonProgress",
    "LessonStatus",
    "LessonDifficulty",
    "Assessment",
    "AssessmentSubmission",
    "AssessmentQuestion",
    "XPTransaction",
    "Badge",
    "UserBadge",
    "LeaderboardEntry",
    "XPSource",
    "BadgeCategory",
    "BadgeRarity",
    "ConsentRecord",
    "DataRetention", 
    "ComplianceLog",
    "ConsentType",
    "ComplianceStatus",
    "Message",
    "MessageRecipient",
]