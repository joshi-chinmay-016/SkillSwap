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
from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.mentor_analytics import (
    MentorPerformanceResponse
)

from app.services.analytics_service import (
    mentor_performance
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

@router.get(
    "/mentor-performance",
    response_model=MentorPerformanceResponse
)
def get_mentor_performance(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return mentor_performance(
        db,
        current_user.id
    )