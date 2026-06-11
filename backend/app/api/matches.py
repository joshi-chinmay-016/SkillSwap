from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.services.match_service import (
    find_teachers,
    find_learners,
    get_my_matches
)

router = APIRouter(
    prefix="/matches",
    tags=["Matches"]
)


@router.get("/teachers/{skill_id}")
def teachers(
    skill_id: int,
    db: Session = Depends(get_db)
):

    return find_teachers(
        db,
        skill_id
    )


@router.get("/learners/{skill_id}")
def learners(
    skill_id: int,
    db: Session = Depends(get_db)
):

    return find_learners(
        db,
        skill_id
    )


@router.get("/me")
def my_matches(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return get_my_matches(
        db,
        current_user.id
    )