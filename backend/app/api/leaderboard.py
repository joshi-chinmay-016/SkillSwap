from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.services.leaderboard_service import (
    top_rated_users
)

router = APIRouter(
    prefix="/leaderboard",
    tags=["Leaderboard"]
)


@router.get("/top-rated")
def get_top_rated(
    db: Session = Depends(get_db)
):

    return top_rated_users(db)


@router.get("/top-mentors")
def get_top_mentors(
    db: Session = Depends(get_db)
):

    return top_rated_users(db)