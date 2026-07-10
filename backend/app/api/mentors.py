from fastapi import (
    APIRouter,
    Depends,
    Query
)

from sqlalchemy.orm import Session

from app.core.database import (
    get_db
)

from app.services.mentor_service import (
    discover_mentors
)

router = APIRouter(
    prefix="/mentors",
    tags=["Mentors"]
)


@router.get("/")
def get_mentors(
    skill: str = Query(
        default=None
    ),
    min_rating: float = Query(
        default=None
    ),
    page: int = Query(
        default=1
    ),
    size: int = Query(
        default=10
    ),
    db: Session = Depends(
        get_db
    )
):

    return discover_mentors(
        db,
        skill,
        min_rating,
        page,
        size
    )
