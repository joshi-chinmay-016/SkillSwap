from fastapi import (
    APIRouter,
    Depends,
    Query
)
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import (
    get_db
)
from app.dependencies.current_user import (
    get_optional_current_user
)
from app.models.user import User
from app.services.mentor_service import (
    discover_mentors
)

router = APIRouter(
    prefix="/mentors",
    tags=["Mentors"]
)


@router.get("")
@router.get("/")
def get_mentors(
    skill: Optional[str] = Query(
        default=None
    ),
    min_rating: Optional[float] = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1
    ),
    size: int = Query(
        default=50,
        ge=1,
        le=100
    ),
    db: Session = Depends(
        get_db
    ),
    current_user: Optional[User] = Depends(
        get_optional_current_user
    )
):
    exclude_id = current_user.id if current_user else None
    return discover_mentors(
        db,
        skill=skill,
        min_rating=min_rating,
        page=page,
        size=size,
        exclude_user_id=exclude_id
    )
