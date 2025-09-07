"""
Student Progress API endpoints
Aggregates progress data from multiple sources
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from api.auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.assessment import Assessment, AssessmentSubmission
from models.class_model import Class, ClassEnrollment
from models.gamification import Badge, UserBadge, XPSource, XPTransaction
from models.lesson import Lesson, LessonProgress
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from ._utils import now

router = APIRouter(prefix="/api/v1/progress", tags=["progress"])
security = HTTPBearer()

# ==================== Pydantic Models ====================


class ProgressMetrics(BaseModel):
    """Overall progress metrics for a student"""

    total_xp: int
    current_level: int
    xp_to_next_level: int
    lessons_completed: int
    lessons_in_progress: int
    assessments_taken: int
    average_score: float
    badges_earned: int
    streak_days: int
    time_spent_minutes: int
    last_active: datetime


class LessonProgressDetail(BaseModel):
    """Detailed progress for a specific lesson"""

    lesson_id: str
    lesson_title: str
    subject: str
    started_at: datetime
    completed_at: Optional[datetime]
    progress_percentage: int
    time_spent_minutes: int
    score: Optional[int]
    attempts: int
    xp_earned: int
    is_completed: bool


class AssessmentProgressDetail(BaseModel):
    """Assessment performance details"""

    assessment_id: str
    assessment_title: str
    assessment_type: str
    submitted_at: datetime
    score: float
    percentage: float
    passed: bool
    attempt_number: int
    time_spent_minutes: Optional[int]


class SkillMastery(BaseModel):
    """Skill mastery level"""

    skill_name: str
    mastery_level: int  # 0-100
    lessons_completed: int
    assessments_passed: int
    last_practiced: datetime


class StudentProgressReport(BaseModel):
    """Comprehensive progress report for a student"""

    student_id: str
    student_name: str
    metrics: ProgressMetrics
    recent_lessons: List[LessonProgressDetail]
    recent_assessments: List[AssessmentProgressDetail]
    skill_mastery: List[SkillMastery]
    badges: List[Dict[str, Any]]
    xp_history: List[Dict[str, Any]]
    learning_streak: Dict[str, Any]


class ClassProgressSummary(BaseModel):
    """Progress summary for a class"""

    class_id: str
    class_name: str
    total_students: int
    active_students: int
    average_xp: float
    average_completion_rate: float
    top_performers: List[Dict[str, Any]]
    struggling_students: List[Dict[str, Any]]
    lesson_completion_rates: Dict[str, float]
    assessment_performance: Dict[str, float]


class LessonAnalytics(BaseModel):
    """Analytics for a specific lesson"""

    lesson_id: str
    lesson_title: str
    total_enrolled: int
    total_started: int
    total_completed: int
    completion_rate: float
    average_time_minutes: float
    average_score: float
    average_attempts: float
    difficulty_rating: str  # "Easy", "Medium", "Hard"


# ==================== Helper Functions ====================


def calculate_level(xp: int) -> int:
    """Calculate level based on XP"""
    # Simple level calculation: level = sqrt(xp / 100)
    import math

    return int(math.sqrt(xp / 100)) + 1


def calculate_xp_to_next_level(current_xp: int) -> int:
    """Calculate XP needed for next level"""
    current_level = calculate_level(current_xp)
    next_level_xp = (current_level**2) * 100
    return max(0, next_level_xp - current_xp)


def calculate_streak(user_id: str, db: Session) -> int:
    """Calculate current learning streak in days"""
    # Get all dates with activity
    activities = (
        db.query(func.date(LessonProgress.last_accessed_at).label("activity_date"))
        .filter(LessonProgress.user_id == user_id)
        .group_by("activity_date")
        .order_by("activity_date")
        .all()
    )

    if not activities:
        return 0

    # Calculate consecutive days
    streak = 0
    today = datetime.now().date()
    current_date = today

    for activity in reversed([a.activity_date for a in activities]):
        if activity == current_date:
            streak += 1
            current_date = current_date - timedelta(days=1)
        elif activity < current_date:
            break

    return streak


def get_skill_mastery(user_id: str, db: Session) -> List[SkillMastery]:
    """Calculate skill mastery levels based on lesson and assessment performance"""
    # Group by subject to calculate mastery
    subjects = (
        db.query(
            Lesson.subject,
            func.count(LessonProgress.id).label("lessons_completed"),
            func.avg(LessonProgress.score).label("avg_score"),
        )
        .join(LessonProgress, Lesson.id == LessonProgress.lesson_id)
        .filter(
            and_(LessonProgress.user_id == user_id, LessonProgress.is_completed == True)
        )
        .group_by(Lesson.subject)
        .all()
    )

    mastery_list = []
    for subject in subjects:
        # Get assessment performance for this subject
        # Assemble filters safely to avoid passing bool/Unknown into SQLAlchemy
        assessment_filters = [Lesson.subject == subject.subject]
        student_attr = getattr(AssessmentSubmission, "student_id", None)
        if student_attr is not None:
            assessment_filters.append(student_attr == user_id)
        passed_attr = getattr(AssessmentSubmission, "passed", None)
        if passed_attr is not None:
            assessment_filters.append(passed_attr == True)

        assessments = (
            db.query(func.count(AssessmentSubmission.id).label("assessments_passed"))
            .join(Assessment, AssessmentSubmission.assessment_id == Assessment.id)
            .join(Lesson, Assessment.lesson_id == Lesson.id)
            .filter(and_(*assessment_filters))
            .first()
        )

        # Calculate mastery level (0-100)
        mastery_level = min(
            100,
            int(
                (subject.lessons_completed * 10)  # Each lesson adds 10 points
                + (
                    assessments.assessments_passed * 15 if assessments else 0
                )  # Each assessment adds 15
                + (subject.avg_score or 0)
                * 0.5  # Average score contributes up to 50 points
            ),
        )

        # Get last practiced date
        last_practiced = (
            db.query(func.max(LessonProgress.last_accessed_at))
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .filter(
                and_(
                    Lesson.subject == subject.subject, LessonProgress.user_id == user_id
                )
            )
            .scalar()
        )

        mastery_list.append(
            SkillMastery(
                skill_name=subject.subject,
                mastery_level=mastery_level,
                lessons_completed=subject.lessons_completed,
                assessments_passed=assessments.assessments_passed if assessments else 0,
                last_practiced=last_practiced or datetime.now(),
            )
        )

    return mastery_list


# ==================== Endpoints ====================


def _check_student_permissions(current_user: dict, student_id: str) -> None:
    """Check if user has permission to view student progress"""
    if current_user["role"] == "Student" and current_user["id"] != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only view their own progress",
        )


def _get_student_metrics(student_id: str, db: Session) -> tuple:
    """Get basic student metrics"""
    total_xp = (
        db.query(func.sum(XPTransaction.amount))
        .filter(XPTransaction.user_id == student_id)
        .scalar() or 0
    )
    
    lesson_progress = (
        db.query(LessonProgress).filter(LessonProgress.user_id == student_id).all()
    )
    
    lessons_completed = sum(1 for lp in lesson_progress if lp.is_completed)
    lessons_in_progress = sum(1 for lp in lesson_progress if not lp.is_completed)
    total_time_spent = sum(lp.time_spent_minutes for lp in lesson_progress)
    
    last_activity = (
        db.query(func.max(LessonProgress.last_accessed_at))
        .filter(LessonProgress.user_id == student_id)
        .scalar() or datetime.now()
    )
    
    return total_xp, lesson_progress, lessons_completed, lessons_in_progress, total_time_spent, last_activity


def _get_student_assessments(student_id: str, db: Session) -> tuple:
    """Get student assessment data"""
    assessments_q = db.query(AssessmentSubmission)
    assessment_student_attr = getattr(AssessmentSubmission, "student_id", None)
    if assessment_student_attr is not None:
        assessments_q = assessments_q.filter(assessment_student_attr == student_id)
    assessments = assessments_q.all()
    
    avg_score = 0
    if assessments:
        scores = [a.score for a in assessments if a.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
    
    return assessments, avg_score


def _build_recent_lessons(lesson_progress: list, db: Session) -> List[LessonProgressDetail]:
    """Build recent lessons list"""
    recent_lessons = []
    for lp in sorted(
        lesson_progress, key=lambda x: x.last_accessed_at or datetime.min, reverse=True
    )[:10]:
        lesson = db.query(Lesson).filter(Lesson.id == lp.lesson_id).first()
        if lesson:
            recent_lessons.append(
                LessonProgressDetail(
                    lesson_id=lp.lesson_id,
                    lesson_title=lesson.title,
                    subject=getattr(lesson.subject, "value", lesson.subject),
                    started_at=lp.started_at,
                    completed_at=lp.completed_at,
                    progress_percentage=lp.progress_percentage,
                    time_spent_minutes=lp.time_spent_minutes,
                    score=lp.score,
                    attempts=lp.attempts,
                    xp_earned=lp.xp_earned,
                    is_completed=lp.is_completed,
                )
            )
    return recent_lessons


def _build_recent_assessments(assessments: list, db: Session) -> List[AssessmentProgressDetail]:
    """Build recent assessments list"""
    recent_assessments = []
    for sub in sorted(
        assessments, key=lambda x: x.submitted_at or datetime.min, reverse=True
    )[:10]:
        assessment = (
            db.query(Assessment).filter(Assessment.id == sub.assessment_id).first()
        )
        if assessment:
            recent_assessments.append(
                AssessmentProgressDetail(
                    assessment_id=sub.assessment_id,
                    assessment_title=assessment.title,
                    assessment_type=str(
                        getattr(assessment.type, "value", assessment.type)
                    ),
                    submitted_at=sub.submitted_at or datetime.min,
                    score=float(sub.score or 0),
                    percentage=float(sub.percentage or 0),
                    passed=bool(sub.passed),
                    attempt_number=sub.attempt_number,
                    time_spent_minutes=sub.time_spent_minutes,
                )
            )
    return recent_assessments


def _build_badges_list(user_badges: list, db: Session) -> List[Dict[str, Any]]:
    """Build badges list with details"""
    badges_list = []
    for ub in user_badges:
        badge = db.query(Badge).filter(Badge.id == ub.badge_id).first()
        if badge:
            badges_list.append(
                {
                    "id": badge.id,
                    "name": badge.name,
                    "description": badge.description,
                    "image_url": badge.image_url,
                    "earned_at": ub.earned_at.isoformat() if ub.earned_at else None,
                    "category": getattr(badge.category, "value", badge.category),
                    "rarity": getattr(badge.rarity, "value", badge.rarity),
                }
            )
    return badges_list


def _get_xp_history(student_id: str, start_date: datetime, db: Session) -> List[Dict[str, Any]]:
    """Get XP transaction history"""
    xp_transactions = (
        db.query(XPTransaction)
        .filter(
            and_(
                XPTransaction.user_id == student_id,
                XPTransaction.created_at >= start_date,
            )
        )
        .order_by(XPTransaction.created_at.desc())
        .limit(20)
        .all()
    )
    
    return [
        {
            "id": tx.id,
            "amount": tx.amount,
            "reason": tx.reason,
            "source": getattr(tx.source, "value", tx.source),
            "timestamp": tx.created_at.isoformat(),
        }
        for tx in xp_transactions
    ]


@router.get("/student/{student_id}", response_model=StudentProgressReport)
async def get_student_progress(
    student_id: str,
    days_back: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get comprehensive progress report for a student"""
    _check_student_permissions(current_user, student_id)
    
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    total_xp, lesson_progress, lessons_completed, lessons_in_progress, total_time_spent, last_activity = _get_student_metrics(student_id, db)
    assessments, avg_score = _get_student_assessments(student_id, db)
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == student_id).all()
    streak = calculate_streak(student_id, db)
    
    metrics = ProgressMetrics(
        total_xp=total_xp,
        current_level=calculate_level(total_xp),
        xp_to_next_level=calculate_xp_to_next_level(total_xp),
        lessons_completed=lessons_completed,
        lessons_in_progress=lessons_in_progress,
        assessments_taken=len(assessments),
        average_score=avg_score,
        badges_earned=len(user_badges),
        streak_days=streak,
        time_spent_minutes=total_time_spent,
        last_active=last_activity,
    )
    
    recent_lessons = _build_recent_lessons(lesson_progress, db)
    recent_assessments = _build_recent_assessments(assessments, db)
    skill_mastery = get_skill_mastery(student_id, db)
    badges_list = _build_badges_list(user_badges, db)
    xp_history = _get_xp_history(student_id, start_date, db)
    
    learning_streak = {
        "current_streak": streak,
        "longest_streak": streak,
        "last_activity": last_activity.isoformat(),
    }
    
    return StudentProgressReport(
        student_id=student_id,
        student_name=(student.display_name or "") if student else "",
        metrics=metrics,
        recent_lessons=recent_lessons,
        recent_assessments=recent_assessments,
        skill_mastery=skill_mastery,
        badges=badges_list,
        xp_history=xp_history,
        learning_streak=learning_streak,
    )


@router.get("/class/{class_id}", response_model=ClassProgressSummary)
async def get_class_progress(
    class_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get progress summary for an entire class"""
    # Check permissions
    class_obj = db.query(Class).filter(Class.id == class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if current_user["role"] == "Teacher" and class_obj.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view progress for your own classes",
        )
    
    if current_user["role"] == "Student":
        # Check if student is enrolled
        enrollment = (
            db.query(ClassEnrollment)
            .filter(
                and_(
                    ClassEnrollment.class_id == class_id,
                    ClassEnrollment.student_id == current_user["id"],
                )
            )
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this class",
            )

    # Get enrolled students
    enrollments = (
        db.query(ClassEnrollment).filter(ClassEnrollment.class_id == class_id).all()
    )

    student_ids = [e.student_id for e in enrollments]
    total_students = len(student_ids)

    # Calculate active students (activity in last 7 days)
    active_cutoff = datetime.now() - timedelta(days=7)
    # If there are no students enrolled, avoid IN queries with empty lists.
    if not student_ids:
        active_students = 0
    else:
        active_students = (
            db.query(func.count(func.distinct(LessonProgress.user_id)))
            .filter(
                and_(
                    LessonProgress.user_id.in_(student_ids),
                    LessonProgress.last_accessed_at >= active_cutoff,
                )
            )
            .scalar()
            or 0
        )

    # Calculate average XP
    avg_xp_result = (
        db.query(func.avg(func.coalesce(func.sum(XPTransaction.amount), 0)))
        .filter(XPTransaction.user_id.in_(student_ids))
        .group_by(XPTransaction.user_id)
        .scalar()
        or 0
    )

    # Calculate average completion rate
    completion_rates = []
    for student_id in student_ids:
        # Build join safely: only use Lesson.id.in_(Class.lesson_ids) when available
        total_lessons_q = db.query(func.count(Lesson.id))
        class_lesson_ids = getattr(Class, "lesson_ids", None)
        if class_lesson_ids is not None and hasattr(class_lesson_ids, "in_"):
            total_lessons_q = total_lessons_q.join(
                Class, Lesson.id.in_(class_lesson_ids)
            )
        else:
            total_lessons_q = total_lessons_q.join(Class)

        total_lessons = total_lessons_q.filter(Class.id == class_id).scalar() or 1

        completed_lessons = (
            db.query(func.count(LessonProgress.id))
            .filter(
                and_(
                    LessonProgress.user_id == student_id,
                    LessonProgress.is_completed == True,
                    LessonProgress.class_id == class_id,
                )
            )
            .scalar()
            or 0
        )

        completion_rates.append(
            (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        )

    avg_completion_rate = (
        sum(completion_rates) / len(completion_rates) if completion_rates else 0
    )

    # Get top performers (by XP)
    top_performers = (
        db.query(
            User.id, User.display_name, func.sum(XPTransaction.amount).label("total_xp")
        )
        .join(XPTransaction, User.id == XPTransaction.user_id)
        .filter(User.id.in_(student_ids))
        .group_by(User.id, User.display_name)
        .order_by(func.sum(XPTransaction.amount).desc())
        .limit(5)
        .all()
    )

    top_performers_list = [
        {
            "student_id": p.id,
            "student_name": p.display_name,
            "total_xp": p.total_xp or 0,
        }
        for p in top_performers
    ]

    # Identify struggling students (low completion rate)
    struggling = []
    for student_id in student_ids:
        student = db.query(User).filter(User.id == student_id).first()
        if not student:
            continue

        progress = (
            db.query(LessonProgress)
            .filter(
                and_(
                    LessonProgress.user_id == student_id,
                    LessonProgress.class_id == class_id,
                )
            )
            .all()
        )

        if progress:
            completion_rate = (
                sum(1 for p in progress if p.is_completed) / len(progress) * 100
            )
            if completion_rate < 50:  # Less than 50% completion
                struggling.append(
                    {
                        "student_id": student_id,
                        "student_name": (student.display_name or "") if student else "",
                        "completion_rate": completion_rate,
                    }
                )

    struggling_students = sorted(struggling, key=lambda x: x["completion_rate"])[:5]

    # Calculate lesson completion rates
    # Build filters list to avoid passing Python booleans into SQLAlchemy ClauseElements
    lesson_filters = []
    class_ids_attr = getattr(Lesson, "class_ids", None)
    if class_ids_attr is not None:
        lesson_filters.append(class_ids_attr.contains([class_id]))

    lessons_q = db.query(Lesson)
    if lesson_filters:
        lessons_q = lessons_q.filter(*lesson_filters)

    lessons = lessons_q.all()

    lesson_completion_rates = {}
    for lesson in lessons[:10]:  # Limit to 10 most recent lessons
        completions = (
            db.query(func.count(LessonProgress.id))
            .filter(
                and_(
                    LessonProgress.lesson_id == lesson.id,
                    LessonProgress.user_id.in_(student_ids),
                    LessonProgress.is_completed == True,
                )
            )
            .scalar()
            or 0
        )

        lesson_completion_rates[lesson.title] = (
            (completions / total_students * 100) if total_students > 0 else 0
        )

    # Calculate assessment performance
    assessments = db.query(Assessment).filter(Assessment.class_id == class_id).all()

    assessment_performance = {}
    for assessment in assessments[:10]:  # Limit to 10 most recent assessments
        submission_filters = [AssessmentSubmission.assessment_id == assessment.id]
        student_id_attr = getattr(AssessmentSubmission, "student_id", None)
        if student_id_attr is not None and hasattr(student_id_attr, "in_"):
            submission_filters.append(student_id_attr.in_(student_ids))

        submissions = (
            db.query(AssessmentSubmission).filter(and_(*submission_filters)).all()
        )

        if submissions:
            avg_score = sum(s.percentage for s in submissions if s.percentage) / len(
                submissions
            )
            assessment_performance[assessment.title] = avg_score

    return ClassProgressSummary(
        class_id=class_id,
        class_name=class_obj.name,
        total_students=total_students,
        active_students=active_students,
        average_xp=float(avg_xp_result),
        average_completion_rate=avg_completion_rate,
        top_performers=top_performers_list,
        struggling_students=struggling_students,
        lesson_completion_rates=lesson_completion_rates,
        assessment_performance=assessment_performance,
    )


@router.get("/lesson/{lesson_id}", response_model=LessonAnalytics)
async def get_lesson_analytics(
    lesson_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get analytics for a specific lesson"""
    # Check permissions (teachers and admins only)
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can view lesson analytics",
        )

    # Get lesson
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    if current_user["role"] == "Teacher" and lesson.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view analytics for your own lessons",
        )

    # Get all progress records for this lesson
    progress_records = (
        db.query(LessonProgress).filter(LessonProgress.lesson_id == lesson_id).all()
    )

    total_enrolled = len(progress_records)
    total_started = sum(1 for p in progress_records if p.progress_percentage > 0)
    total_completed = sum(1 for p in progress_records if p.is_completed)

    completion_rate = (
        (total_completed / total_enrolled * 100) if total_enrolled > 0 else 0
    )

    # Calculate averages
    if progress_records:
        avg_time = sum(p.time_spent_minutes for p in progress_records) / len(
            progress_records
        )
        scores = [p.score for p in progress_records if p.score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_attempts = sum(p.attempts for p in progress_records) / len(progress_records)
    else:
        avg_time = 0
        avg_score = 0
        avg_attempts = 0

    # Determine difficulty rating based on completion rate and average score
    if completion_rate > 80 and avg_score > 80:
        difficulty = "Easy"
    elif completion_rate < 50 or avg_score < 60:
        difficulty = "Hard"
    else:
        difficulty = "Medium"

    return LessonAnalytics(
        lesson_id=lesson_id,
        lesson_title=lesson.title,
        total_enrolled=total_enrolled,
        total_started=total_started,
        total_completed=total_completed,
        completion_rate=completion_rate,
        average_time_minutes=avg_time,
        average_score=avg_score,
        average_attempts=avg_attempts,
        difficulty_rating=difficulty,
    )


@router.post("/update")
async def update_progress(
    lesson_id: str,
    progress_percentage: int = Query(..., ge=0, le=100),
    time_spent_minutes: int = Query(..., ge=0),
    score: Optional[int] = Query(None, ge=0, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update progress for a lesson"""
    # Only students can update their own progress
    if current_user["role"] != "Student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update progress",
        )

    # Check if lesson exists
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found"
        )

    # Get or create progress record
    progress = (
        db.query(LessonProgress)
        .filter(
            and_(
                LessonProgress.lesson_id == lesson_id,
                LessonProgress.user_id == current_user["id"],
            )
        )
        .first()
    )

    if not progress:
        progress = LessonProgress(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            lesson_id=lesson_id,
            started_at=now(),
            last_accessed_at=now(),
            progress_percentage=0,
            time_spent_minutes=0,
            attempts=1,
            is_completed=False,
            xp_earned=0,
        )
        db.add(progress)

    # Update progress
    progress.progress_percentage = max(
        progress.progress_percentage, progress_percentage
    )
    progress.time_spent_minutes += time_spent_minutes
    progress.last_accessed_at = now()

    if score is not None:
        progress.score = max(progress.score or 0, score)

    # Check if completed
    if progress_percentage >= 100 and not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = now()

        # Award XP for completion
        xp_amount = 50  # Base XP for lesson completion
        if score:
            xp_amount += int(score / 2)  # Bonus XP based on score

        xp_transaction = XPTransaction(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            amount=xp_amount,
            source=XPSource.LESSON,
            reason=f"Completed lesson: {lesson.title}",
            lesson_id=lesson_id,
            total_xp_after=0,  # Will be calculated
            level_after=0,  # Will be calculated
        )
        db.add(xp_transaction)

        progress.xp_earned = xp_amount

    db.commit()

    return {
        "message": "Progress updated successfully",
        "progress": progress_percentage,
        "is_completed": progress.is_completed,
        "xp_earned": progress.xp_earned,
    }


@router.get("/analytics")
async def get_progress_analytics(
    student_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get detailed analytics and trends"""
    # Build query based on filters
    query = db.query(LessonProgress).join(Lesson, LessonProgress.lesson_id == Lesson.id)

    # Apply filters
    if student_id:
        # Check permissions
        if current_user["role"] == "Student" and current_user["id"] != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only view their own analytics",
            )
        query = query.filter(LessonProgress.user_id == student_id)

    if class_id:
        query = query.filter(LessonProgress.class_id == class_id)

    if subject:
        query = query.filter(Lesson.subject == subject)

    if date_from:
        query = query.filter(LessonProgress.started_at >= date_from)

    if date_to:
        query = query.filter(LessonProgress.started_at <= date_to)

    # Get progress records
    progress_records = query.all()

    # Calculate analytics
    total_time = sum(p.time_spent_minutes for p in progress_records)
    total_lessons = len(set(p.lesson_id for p in progress_records))
    completed_lessons = sum(1 for p in progress_records if p.is_completed)

    # Daily activity
    daily_activity = defaultdict(int)
    for p in progress_records:
        date_key = p.last_accessed_at.date().isoformat()
        daily_activity[date_key] += p.time_spent_minutes

    # Subject distribution
    subject_distribution = defaultdict(lambda: {"count": 0, "time": 0})
    for p in progress_records:
        lesson = db.query(Lesson).filter(Lesson.id == p.lesson_id).first()
        if lesson:
            subject = getattr(lesson.subject, "value", lesson.subject)
            subject_distribution[subject]["count"] += 1
            subject_distribution[subject]["time"] += p.time_spent_minutes

    # XP trends
    xp_query = db.query(XPTransaction)
    if student_id:
        xp_query = xp_query.filter(XPTransaction.user_id == student_id)
    if date_from:
        xp_query = xp_query.filter(XPTransaction.created_at >= date_from)
    if date_to:
        xp_query = xp_query.filter(XPTransaction.created_at <= date_to)

    xp_transactions = xp_query.order_by(XPTransaction.created_at).all()

    cumulative_xp = 0
    xp_trend = []
    for tx in xp_transactions:
        cumulative_xp += tx.amount
        xp_trend.append(
            {
                "date": tx.created_at.isoformat(),
                "xp_gained": tx.amount,
                "cumulative_xp": cumulative_xp,
            }
        )

    return {
        "summary": {
            "total_time_minutes": total_time,
            "total_lessons_accessed": total_lessons,
            "lessons_completed": completed_lessons,
            "completion_rate": (
                (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
            ),
            "total_xp_gained": sum(tx.amount for tx in xp_transactions),
        },
        "daily_activity": dict(daily_activity),
        "subject_distribution": dict(subject_distribution),
        "xp_trend": xp_trend,
    }
