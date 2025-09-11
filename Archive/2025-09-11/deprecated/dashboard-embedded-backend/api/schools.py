"""
Schools Management API Endpoints
"""

import uuid
from datetime import datetime
from typing import List, Optional

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import School, User, UserRole
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ._utils import now
from .auth import decode_token

# ==================== Router Setup ====================
router = APIRouter(prefix="/api/v1/schools", tags=["schools"])
security = HTTPBearer()

# ==================== Pydantic Schemas ====================


class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=50)
    zip_code: str = Field(..., min_length=5, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    principal_name: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=200)
    max_students: int = Field(500, ge=1, le=10000)
    is_active: bool = True


class SchoolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = Field(None, min_length=1, max_length=500)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=10)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    principal_name: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=200)
    max_students: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: Optional[str]
    email: Optional[str]
    principal_name: Optional[str]
    district: Optional[str]
    student_count: int
    teacher_count: int
    class_count: int
    max_students: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Authentication ====================


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Verify JWT token and return current user"""
    try:
        payload = decode_token(credentials.credentials)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role for access"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return current_user


# ==================== Endpoints ====================


@router.get("/", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all schools with optional filtering"""
    query = db.query(School)

    if is_active is not None:
        query = query.filter(School.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (School.name.ilike(search_term))
            | (School.city.ilike(search_term))
            | (School.district.ilike(search_term))
        )

    schools = query.offset(skip).limit(limit).all()

    # Convert to response model with counts
    response = []
    for school in schools:
        school_dict = {
            "id": school.id,
            "name": school.name,
            "address": school.address,
            "city": school.city,
            "state": school.state,
            "zip_code": school.zip_code,
            "phone": school.phone,
            "email": school.email,
            "principal_name": school.principal_name,
            "district": school.district,
            "student_count": (
                school.student_count if hasattr(school, "student_count") else 0
            ),
            "teacher_count": (
                school.teacher_count if hasattr(school, "teacher_count") else 0
            ),
            "class_count": school.class_count if hasattr(school, "class_count") else 0,
            "max_students": school.max_students,
            "is_active": school.is_active,
            "created_at": school.created_at,
            "updated_at": school.updated_at or school.created_at,
        }
        response.append(SchoolResponse(**school_dict))

    return response


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific school by ID"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    return SchoolResponse(
        id=school.id,
        name=school.name,
        address=school.address,
        city=school.city,
        state=school.state,
        zip_code=school.zip_code,
        phone=school.phone,
        email=school.email,
        principal_name=school.principal_name,
        district=school.district,
        student_count=school.student_count if hasattr(school, "student_count") else 0,
        teacher_count=school.teacher_count if hasattr(school, "teacher_count") else 0,
        class_count=school.class_count if hasattr(school, "class_count") else 0,
        max_students=school.max_students,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at or school.created_at,
    )


@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new school (Admin only)"""
    # Check if school with same name and city already exists
    existing = (
        db.query(School)
        .filter(School.name == school_data.name, School.city == school_data.city)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School with this name already exists in this city",
        )

    # Create new school
    school = School(
        id=str(uuid.uuid4()),
        name=school_data.name,
        address=school_data.address,
        city=school_data.city,
        state=school_data.state,
        zip_code=school_data.zip_code,
        phone=school_data.phone,
        email=school_data.email,
        principal_name=school_data.principal_name,
        district=school_data.district,
        max_students=school_data.max_students,
        is_active=school_data.is_active,
        created_at=now(),
        updated_at=now(),
    )

    db.add(school)
    db.commit()
    db.refresh(school)

    return SchoolResponse(
        id=school.id,
        name=school.name,
        address=school.address,
        city=school.city,
        state=school.state,
        zip_code=school.zip_code,
        phone=school.phone,
        email=school.email,
        principal_name=school.principal_name,
        district=school.district,
        student_count=0,
        teacher_count=0,
        class_count=0,
        max_students=school.max_students,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at or school.created_at,
    )


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: str,
    school_data: SchoolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update a school (Admin only)"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Update fields if provided
    update_data = school_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)

    school.updated_at = now()
    db.commit()
    db.refresh(school)

    return SchoolResponse(
        id=school.id,
        name=school.name,
        address=school.address,
        city=school.city,
        state=school.state,
        zip_code=school.zip_code,
        phone=school.phone,
        email=school.email,
        principal_name=school.principal_name,
        district=school.district,
        student_count=school.student_count if hasattr(school, "student_count") else 0,
        teacher_count=school.teacher_count if hasattr(school, "teacher_count") else 0,
        class_count=school.class_count if hasattr(school, "class_count") else 0,
        max_students=school.max_students,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at,
    )


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete a school (Admin only)"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Check if there are active classes or users associated
    # In production, you'd want to check for dependencies
    # For now, we'll do a soft delete by setting is_active = False
    school.is_active = False
    school.updated_at = now()
    db.commit()

    return None


@router.post("/{school_id}/activate", response_model=SchoolResponse)
async def activate_school(
    school_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reactivate a deactivated school (Admin only)"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    school.is_active = True
    school.updated_at = now()
    db.commit()
    db.refresh(school)

    return SchoolResponse(
        id=school.id,
        name=school.name,
        address=school.address,
        city=school.city,
        state=school.state,
        zip_code=school.zip_code,
        phone=school.phone,
        email=school.email,
        principal_name=school.principal_name,
        district=school.district,
        student_count=school.student_count if hasattr(school, "student_count") else 0,
        teacher_count=school.teacher_count if hasattr(school, "teacher_count") else 0,
        class_count=school.class_count if hasattr(school, "class_count") else 0,
        max_students=school.max_students,
        is_active=school.is_active,
        created_at=school.created_at,
        updated_at=school.updated_at,
    )


@router.get("/{school_id}/stats")
async def get_school_stats(
    school_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get statistics for a specific school"""
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
        )

    # Get counts from database
    student_count = (
        db.query(User)
        .filter(User.school_id == school_id, User.role == UserRole.STUDENT)
        .count()
    )

    teacher_count = (
        db.query(User)
        .filter(User.school_id == school_id, User.role == UserRole.TEACHER)
        .count()
    )

    # Return statistics
    return {
        "school_id": school_id,
        "school_name": school.name,
        "total_students": student_count,
        "total_teachers": teacher_count,
        "total_classes": 0,  # TODO: Implement when Class model is available
        "max_capacity": school.max_students,
        "capacity_percentage": (
            (student_count / school.max_students * 100)
            if school.max_students > 0
            else 0
        ),
        "is_active": school.is_active,
    }
