from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.services.recommendation_service import (
    get_recommendations
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)


@router.get("/me")
def my_recommendations(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return get_recommendations(
        db,
        current_user.id
    )