"""
Schools API Endpoints

Provides CRUD operations for schools management.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.backend.api.auth.auth import get_current_user
from apps.backend.models.schemas import User

router = APIRouter()


# Request/Response Models
class School(BaseModel):
    id: str | None = None
    name: str
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    is_active: bool = True


class SchoolResponse(BaseModel):
    success: bool
    data: School | None = None
    message: str | None = None


class SchoolListResponse(BaseModel):
    success: bool
    data: list[School] = []
    total: int = 0
    message: str | None = None


# Mock data for now
_mock_schools = [
    School(
        id="1",
        name="Demo School",
        address="123 Education St",
        city="Learning City",
        state="CA",
        zip_code="12345",
        country="USA",
        email="info@demoschool.edu",
        is_active=True,
    )
]


@router.get("/", response_model=SchoolListResponse)
async def get_schools(
    skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user)
):
    """
    Get list of schools
    """
    return SchoolListResponse(
        success=True, data=_mock_schools[skip : skip + limit], total=len(_mock_schools)
    )


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(school_id: str, current_user: User = Depends(get_current_user)):
    """
    Get specific school by ID
    """
    for school in _mock_schools:
        if school.id == school_id:
            return SchoolResponse(success=True, data=school)

    raise HTTPException(status_code=404, detail="School not found")


@router.post("/", response_model=SchoolResponse)
async def create_school(school: School, current_user: User = Depends(get_current_user)):
    """
    Create new school
    """
    # Only admin can create schools
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can create schools")

    # Generate ID
    school.id = str(len(_mock_schools) + 1)
    _mock_schools.append(school)

    return SchoolResponse(success=True, data=school, message="School created successfully")


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: str, school: School, current_user: User = Depends(get_current_user)
):
    """
    Update school
    """
    # Only admin can update schools
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can update schools")

    for i, existing in enumerate(_mock_schools):
        if existing.id == school_id:
            school.id = school_id
            _mock_schools[i] = school
            return SchoolResponse(success=True, data=school, message="School updated successfully")

    raise HTTPException(status_code=404, detail="School not found")


@router.delete("/{school_id}")
async def delete_school(school_id: str, current_user: User = Depends(get_current_user)):
    """
    Delete school
    """
    # Only admin can delete schools
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only administrators can delete schools")

    global _mock_schools
    _mock_schools = [s for s in _mock_schools if s.id != school_id]

    return {"success": True, "message": "School deleted successfully"}


# Export router
__all__ = ["router"]
