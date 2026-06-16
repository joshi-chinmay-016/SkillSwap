from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import (
    get_db
)

from app.services.analytics_service import (
    top_teach_skills,
    top_learn_skills,
    trending_skills
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/top-teach-skills"
)
def get_top_teach(
    db: Session = Depends(
        get_db
    )
):

    return top_teach_skills(
        db
    )


@router.get(
    "/top-learn-skills"
)
def get_top_learn(
    db: Session = Depends(
        get_db
    )
):

    return top_learn_skills(
        db
    )


@router.get(
    "/trending-skills"
)
def get_trending(
    db: Session = Depends(
        get_db
    )
):

    return trending_skills(
        db
    )