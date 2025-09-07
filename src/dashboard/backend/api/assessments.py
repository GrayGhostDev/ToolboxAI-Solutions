"""
Assessments API endpoints
Handles assessments, questions, and submissions
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from api._utils import safe_json_loads
from api.auth import get_current_user
from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models.assessment import (
    Assessment,
    AssessmentSubmission,
    AssessmentType,
    QuestionType,
)
from models.class_model import Class
from models.user import User
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/assessments", tags=["assessments"])
security = HTTPBearer()

# ==================== Pydantic Models ====================


class QuestionModel(BaseModel):
    """Question model for assessments"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(
        ...,
        pattern="^(multiple_choice|true_false|short_answer|essay|matching|fill_blank|coding)$",
    )
    question: str
    options: Optional[List[str]] = None
    correct_answer: Optional[Any] = None
    points: int = Field(default=1, ge=1)
    explanation: Optional[str] = None
    required: bool = True


class AssessmentCreate(BaseModel):
    """Model for creating an assessment"""

    title: str = Field(..., min_length=1, max_length=200)
    description: str
    type: str = Field(..., pattern="^(quiz|test|assignment|project|homework|exam)$")
    class_id: str
    lesson_id: Optional[str] = None
    questions: List[QuestionModel]
    duration_minutes: Optional[int] = Field(None, ge=1)
    due_date: Optional[datetime] = None
    max_attempts: int = Field(default=1, ge=1)
    passing_score: float = Field(default=70.0, ge=0, le=100)
    randomize_questions: bool = False
    show_results: bool = True
    allow_late_submission: bool = False


class AssessmentUpdate(BaseModel):
    """Model for updating an assessment"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    questions: Optional[List[QuestionModel]] = None
    duration_minutes: Optional[int] = None
    due_date: Optional[datetime] = None
    max_attempts: Optional[int] = Field(None, ge=1)
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    is_published: Optional[bool] = None


class AssessmentResponse(BaseModel):
    """Response model for assessment"""

    id: str
    title: str
    description: str
    type: str
    class_id: str
    class_name: Optional[str] = None
    lesson_id: Optional[str] = None
    teacher_id: str
    teacher_name: Optional[str] = None
    questions: List[QuestionModel]
    duration_minutes: Optional[int]
    due_date: Optional[datetime]
    max_attempts: int
    passing_score: float
    total_points: int
    is_published: bool
    created_at: datetime
    submissions_count: int = 0
    average_score: Optional[float] = None


class SubmissionCreate(BaseModel):
    """Model for submitting assessment answers"""

    answers: Dict[str, Any]  # question_id -> answer
    time_spent_minutes: Optional[int] = None


class SubmissionResponse(BaseModel):
    """Response model for submission"""

    id: str
    assessment_id: str
    student_id: str
    student_name: Optional[str] = None
    answers: Dict[str, Any]
    score: Optional[float] = None
    percentage: Optional[float] = None
    passed: Optional[bool] = None
    feedback: Optional[Dict[str, str]] = None
    submitted_at: Optional[datetime]
    graded_at: Optional[datetime] = None
    attempt_number: int


# ==================== Helper Functions ====================


def calculate_score(
    questions: List[QuestionModel], answers: Dict[str, Any]
) -> tuple[float, float, Dict[str, bool]]:
    """Calculate score for submitted answers"""
    total_points = 0
    earned_points = 0
    results = {}

    for question in questions:
        total_points += question.points
        if question.id in answers:
            user_answer = answers[question.id]
            correct_answer = question.correct_answer

            # Compare answers based on question type
            if question.type in ["multiple_choice", "true_false", "fill_blank"]:
                is_correct = str(user_answer).lower() == str(correct_answer).lower()
            elif question.type == "matching":
                is_correct = json.dumps(user_answer, sort_keys=True) == json.dumps(
                    correct_answer, sort_keys=True
                )
            else:
                # For essay and short_answer, manual grading required
                is_correct = None

            if is_correct:
                earned_points += question.points
                results[question.id] = True
            elif is_correct is not None:
                results[question.id] = False

    return (float(earned_points), float(total_points), results)


# ==================== Endpoints ====================


@router.get("/", response_model=List[AssessmentResponse])
async def list_assessments(
    class_id: Optional[str] = Query(None),
    lesson_id: Optional[str] = Query(None),
    assessment_type: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List assessments with optional filters"""
    query = db.query(Assessment)

    # Apply filters based on user role
    if current_user["role"] == "Student":
        # Students only see published assessments for their classes
        query = query.filter(Assessment.is_published == True)
        # Filter by enrolled classes
        enrolled_class_ids = [
            c.id
            for c in db.query(Class)
            .filter(Class.students.any(id=current_user["id"]))
            .all()
        ]
        # Only apply the IN filter when there are enrolled class ids.
        # If the student is not enrolled in any classes, return empty list early.
        if enrolled_class_ids:
            query = query.filter(Assessment.class_id.in_(enrolled_class_ids))
        else:
            return []
    elif current_user["role"] == "Teacher":
        # Teachers see their own assessments
        query = query.filter(Assessment.teacher_id == current_user["id"])
    # Admins see all

    # Apply additional filters
    if class_id:
        query = query.filter(Assessment.class_id == class_id)
    if lesson_id:
        query = query.filter(Assessment.lesson_id == lesson_id)
    if assessment_type:
        query = query.filter(Assessment.type == AssessmentType[assessment_type.upper()])
    if is_published is not None:
        query = query.filter(Assessment.is_published == is_published)

    assessments = query.order_by(Assessment.created_at.desc()).all()

    # Transform to response model
    response = []
    for assessment in assessments:
        # Get submission statistics
        submissions = (
            db.query(AssessmentSubmission)
            .filter(AssessmentSubmission.assessment_id == assessment.id)
            .all()
        )

        avg_score = None
        if submissions:
            scores = [s.score for s in submissions if s.score is not None]
            if scores:
                avg_score = sum(scores) / len(scores)

        # Get class and teacher names
        class_obj = db.query(Class).filter(Class.id == assessment.class_id).first()
        teacher = db.query(User).filter(User.id == assessment.teacher_id).first()

        response.append(
            AssessmentResponse(
                id=assessment.id,
                title=assessment.title,
                description=assessment.description,
                type=assessment.type.value,
                class_id=assessment.class_id,
                class_name=class_obj.name if class_obj else None,
                lesson_id=assessment.lesson_id,
                teacher_id=assessment.teacher_id,
                teacher_name=(teacher.display_name or "") if teacher else "",
                questions=(
                    safe_json_loads(assessment.questions, [])
                    if assessment.questions
                    else []
                ),
                duration_minutes=assessment.duration_minutes,
                due_date=assessment.due_date,
                max_attempts=assessment.max_attempts,
                passing_score=assessment.passing_score,
                total_points=assessment.total_points,
                is_published=assessment.is_published,
                created_at=assessment.created_at,
                submissions_count=len(submissions),
                average_score=avg_score,
            )
        )

    return response


@router.post(
    "/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED
)
async def create_assessment(
    assessment: AssessmentCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new assessment"""
    # Check permissions
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create assessments",
        )

    # Verify class exists and user has access
    class_obj = db.query(Class).filter(Class.id == assessment.class_id).first()
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )

    if current_user["role"] == "Teacher" and class_obj.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create assessments for your own classes",
        )

    # Calculate total points
    total_points = sum(q.points for q in assessment.questions)

    # Create assessment
    new_assessment = Assessment(
        id=str(uuid.uuid4()),
        title=assessment.title,
        description=assessment.description,
        type=AssessmentType[assessment.type.upper()],
        class_id=assessment.class_id,
        lesson_id=assessment.lesson_id,
        teacher_id=current_user["id"],
        questions=cast(Any, json.dumps([q.dict() for q in assessment.questions])),
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        max_attempts=assessment.max_attempts,
        passing_score=assessment.passing_score,
        total_points=total_points,
        randomize_questions=assessment.randomize_questions,
        show_results=assessment.show_results,
        allow_late_submission=assessment.allow_late_submission,
        is_published=False,  # Start as draft
    )

    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    # Get teacher info
    teacher = db.query(User).filter(User.id == current_user["id"]).first()

    return AssessmentResponse(
        id=new_assessment.id,
        title=new_assessment.title,
        description=new_assessment.description,
        type=new_assessment.type.value,
        class_id=new_assessment.class_id,
        class_name=class_obj.name,
        lesson_id=new_assessment.lesson_id,
        teacher_id=new_assessment.teacher_id,
        teacher_name=(teacher.display_name or "") if teacher else "",
        questions=[
            QuestionModel(**q) for q in safe_json_loads(new_assessment.questions, [])
        ],
        duration_minutes=new_assessment.duration_minutes,
        due_date=new_assessment.due_date,
        max_attempts=new_assessment.max_attempts,
        passing_score=new_assessment.passing_score,
        total_points=new_assessment.total_points,
        is_published=new_assessment.is_published,
        created_at=new_assessment.created_at,
        submissions_count=0,
        average_score=None,
    )


@router.get("/{assessment_id}", response_model=AssessmentResponse)
async def get_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get assessment details"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check permissions
    if current_user["role"] == "Student":
        if not assessment.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This assessment is not yet published",
            )
        # TODO: Check if student is enrolled in the class
    elif current_user["role"] == "Teacher":
        if assessment.teacher_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own assessments",
            )

    # Get additional info
    submissions = (
        db.query(AssessmentSubmission)
        .filter(AssessmentSubmission.assessment_id == assessment_id)
        .all()
    )

    avg_score = None
    if submissions:
        scores = [s.score for s in submissions if s.score is not None]
        if scores:
            avg_score = sum(scores) / len(scores)

    class_obj = db.query(Class).filter(Class.id == assessment.class_id).first()
    teacher = db.query(User).filter(User.id == assessment.teacher_id).first()

    # For students, remove correct answers from questions
    questions = (
        safe_json_loads(assessment.questions, []) if assessment.questions else []
    )
    if current_user["role"] == "Student":
        for q in questions:
            q.pop("correct_answer", None)
            q.pop("explanation", None)

    return AssessmentResponse(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        type=assessment.type.value,
        class_id=assessment.class_id,
        class_name=class_obj.name if class_obj else None,
        lesson_id=assessment.lesson_id,
        teacher_id=assessment.teacher_id,
        teacher_name=(teacher.display_name or "") if teacher else "",
        questions=[QuestionModel(**q) for q in questions],
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        max_attempts=assessment.max_attempts,
        passing_score=assessment.passing_score,
        total_points=assessment.total_points,
        is_published=assessment.is_published,
        created_at=assessment.created_at,
        submissions_count=len(submissions),
        average_score=avg_score,
    )


@router.put("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    update_data: AssessmentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an assessment"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check permissions
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can update assessments",
        )

    if (
        current_user["role"] == "Teacher"
        and assessment.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own assessments",
        )

    # Update fields
    update_dict = update_data.dict(exclude_unset=True)

    if "questions" in update_dict:
        questions = update_dict["questions"]
        assessment.questions = cast(Any, json.dumps([q.dict() for q in questions]))
        assessment.total_points = sum(q.points for q in questions)
        del update_dict["questions"]

    for field, value in update_dict.items():
        setattr(assessment, field, value)

    assessment.updated_at = datetime.now()
    db.commit()
    db.refresh(assessment)

    # Get additional info for response
    submissions = (
        db.query(AssessmentSubmission)
        .filter(AssessmentSubmission.assessment_id == assessment_id)
        .all()
    )

    avg_score = None
    if submissions:
        scores = [s.score for s in submissions if s.score is not None]
        if scores:
            avg_score = sum(scores) / len(scores)

    class_obj = db.query(Class).filter(Class.id == assessment.class_id).first()
    teacher = db.query(User).filter(User.id == assessment.teacher_id).first()

    return AssessmentResponse(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        type=assessment.type.value,
        class_id=assessment.class_id,
        class_name=class_obj.name if class_obj else None,
        lesson_id=assessment.lesson_id,
        teacher_id=assessment.teacher_id,
        teacher_name=(teacher.display_name or "") if teacher else "",
        questions=[
            QuestionModel(**q) for q in safe_json_loads(assessment.questions, [])
        ],
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        max_attempts=assessment.max_attempts,
        passing_score=assessment.passing_score,
        total_points=assessment.total_points,
        is_published=assessment.is_published,
        created_at=assessment.created_at,
        submissions_count=len(submissions),
        average_score=avg_score,
    )


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an assessment"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check permissions
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can delete assessments",
        )

    if (
        current_user["role"] == "Teacher"
        and assessment.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own assessments",
        )

    # Check for existing submissions
    submissions = (
        db.query(AssessmentSubmission)
        .filter(AssessmentSubmission.assessment_id == assessment_id)
        .count()
    )

    if submissions > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete assessment with existing submissions",
        )

    db.delete(assessment)
    db.commit()


@router.post(
    "/{assessment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_assessment(
    assessment_id: str,
    submission: SubmissionCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit answers for an assessment"""
    # Check if student
    if current_user["role"] != "Student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assessments",
        )

    # Get assessment
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    if not assessment.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This assessment is not yet published",
        )

    # Check due date
    if assessment.due_date and datetime.now() > assessment.due_date:
        if not assessment.allow_late_submission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment submission deadline has passed",
            )

    # Check attempt limit
    existing_submissions = (
        db.query(AssessmentSubmission)
        .filter(
            and_(
                AssessmentSubmission.assessment_id == assessment_id,
                AssessmentSubmission.student_id == current_user["id"],
            )
        )
        .count()
    )

    if existing_submissions >= assessment.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum attempts ({assessment.max_attempts}) reached",
        )

    # Calculate score
    questions = [QuestionModel(**q) for q in safe_json_loads(assessment.questions, [])]
    earned_points, total_points, results = calculate_score(
        questions, submission.answers
    )

    percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    passed = percentage >= assessment.passing_score

    # Create submission
    new_submission = AssessmentSubmission(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        student_id=current_user["id"],
        answers=safe_json_loads(submission.answers, {}),
        score=earned_points,
        percentage=percentage,
        passed=passed,
        time_spent_minutes=submission.time_spent_minutes,
        attempt_number=existing_submissions + 1,
        submitted_at=datetime.now(),
    )

    # Auto-grade for objective questions
    if assessment.type in [AssessmentType.QUIZ, AssessmentType.TEST]:
        new_submission.graded_at = datetime.now()
        new_submission.auto_graded = True

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    # Get student info
    student = db.query(User).filter(User.id == current_user["id"]).first()

    # Prepare feedback if results should be shown
    feedback = {}
    if assessment.show_results:
        for question_id, is_correct in results.items():
            question = next((q for q in questions if q.id == question_id), None)
            if question and question.explanation:
                feedback[question_id] = (
                    question.explanation if not is_correct else "Correct!"
                )

    return SubmissionResponse(
        id=new_submission.id,
        assessment_id=new_submission.assessment_id,
        student_id=new_submission.student_id,
        student_name=(student.display_name or "") if student else "",
        answers=safe_json_loads(new_submission.answers, {}),
        score=new_submission.score if assessment.show_results else None,
        percentage=new_submission.percentage if assessment.show_results else None,
        passed=new_submission.passed if assessment.show_results else None,
        feedback=feedback if assessment.show_results else None,
        submitted_at=new_submission.submitted_at,
        graded_at=new_submission.graded_at,
        attempt_number=new_submission.attempt_number,
    )


@router.get("/{assessment_id}/submissions", response_model=List[SubmissionResponse])
async def get_submissions(
    assessment_id: str,
    student_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get submissions for an assessment"""
    # Get assessment
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check permissions
    if current_user["role"] == "Student":
        # Students can only see their own submissions
        student_id = current_user["id"]
    elif current_user["role"] == "Teacher":
        if assessment.teacher_id != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view submissions for your own assessments",
            )

    # Query submissions: assemble filters to avoid passing non-ClauseElements
    submission_filters = [AssessmentSubmission.assessment_id == assessment_id]
    if student_id is not None:
        student_id_attr = getattr(AssessmentSubmission, "student_id", None)
        if student_id_attr is not None:
            submission_filters.append(student_id_attr == student_id)

    submissions = (
        db.query(AssessmentSubmission)
        .filter(*submission_filters)
        .order_by(AssessmentSubmission.submitted_at.desc())
        .all()
    )

    # Transform to response
    response = []
    for submission in submissions:
        student = db.query(User).filter(User.id == submission.student_id).first()

        # Prepare response based on role
        if current_user["role"] == "Student" and not assessment.show_results:
            # Don't show scores if results are hidden
            response.append(
                SubmissionResponse(
                    id=submission.id,
                    assessment_id=submission.assessment_id,
                    student_id=submission.student_id,
                    student_name=(student.display_name or "") if student else "",
                    answers={},  # Hide answers from other students
                    score=None,
                    percentage=None,
                    passed=None,
                    feedback=None,
                    submitted_at=submission.submitted_at,
                    graded_at=submission.graded_at,
                    attempt_number=submission.attempt_number,
                )
            )
        else:
            response.append(
                SubmissionResponse(
                    id=submission.id,
                    assessment_id=submission.assessment_id,
                    student_id=submission.student_id,
                    student_name=(student.display_name or "") if student else "",
                    answers=safe_json_loads(submission.answers, {}),
                    score=submission.score,
                    percentage=submission.percentage,
                    passed=submission.passed,
                    feedback=(
                        json.loads(submission.feedback) if submission.feedback else None
                    ),
                    submitted_at=submission.submitted_at,
                    graded_at=submission.graded_at,
                    attempt_number=submission.attempt_number,
                )
            )

    return response


@router.put("/{assessment_id}/publish", response_model=AssessmentResponse)
async def publish_assessment(
    assessment_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish an assessment to make it available to students"""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found"
        )

    # Check permissions
    if current_user["role"] not in ["Teacher", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can publish assessments",
        )

    if (
        current_user["role"] == "Teacher"
        and assessment.teacher_id != current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own assessments",
        )

    assessment.is_published = True
    assessment.published_at = datetime.now()
    assessment.updated_at = datetime.now()

    db.commit()
    db.refresh(assessment)

    # Return updated assessment
    class_obj = db.query(Class).filter(Class.id == assessment.class_id).first()
    teacher = db.query(User).filter(User.id == assessment.teacher_id).first()

    return AssessmentResponse(
        id=assessment.id,
        title=assessment.title,
        description=assessment.description,
        type=assessment.type.value,
        class_id=assessment.class_id,
        class_name=class_obj.name if class_obj else None,
        lesson_id=assessment.lesson_id,
        teacher_id=assessment.teacher_id,
        teacher_name=(teacher.display_name or "") if teacher else "",
        questions=[
            QuestionModel(**q) for q in safe_json_loads(assessment.questions, [])
        ],
        duration_minutes=assessment.duration_minutes,
        due_date=assessment.due_date,
        max_attempts=assessment.max_attempts,
        passing_score=assessment.passing_score,
        total_points=assessment.total_points,
        is_published=assessment.is_published,
        created_at=assessment.created_at,
        submissions_count=0,
        average_score=None,
    )
