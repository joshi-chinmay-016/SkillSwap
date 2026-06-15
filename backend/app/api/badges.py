from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.badge import (
    BadgeResponse
)

from app.services.badge_service import (
    award_badges,
    my_badges
)

router = APIRouter(
    prefix="/badges",
    tags=["Badges"]
)


@router.post(
    "/check",
    response_model=list[
        BadgeResponse
    ]
)
def check_badges(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return award_badges(
        db,
        current_user.id
    )


@router.get(
    "/me",
    response_model=list[
        BadgeResponse
    ]
)
def get_my_badges(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return my_badges(
        db,
        current_user.id
    )