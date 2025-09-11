"""
Database Models for Educational Platform
"""

from .base import Base, TimestampMixin
from .user import User, UserRole
from .school import School
from .class_model import Class, ClassEnrollment
from .lesson import Lesson, LessonProgress, LessonStatus, LessonDifficulty
from .assessment import Assessment, AssessmentSubmission, AssessmentQuestion
from .gamification import XPTransaction, Badge, UserBadge, LeaderboardEntry, XPSource, BadgeCategory, BadgeRarity
from .compliance import ConsentRecord, DataRetention, ComplianceLog, ConsentType, ComplianceStatus
from .message import Message, MessageRecipient
from .report import Report, ReportTemplate, ReportSchedule, ReportGeneration, ReportType, ReportFrequency, ReportStatus, ReportFormat

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "UserRole",
    "School",
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
    "Report",
    "ReportTemplate",
    "ReportSchedule",
    "ReportGeneration",
    "ReportType",
    "ReportFrequency",
    "ReportStatus",
    "ReportFormat",
]