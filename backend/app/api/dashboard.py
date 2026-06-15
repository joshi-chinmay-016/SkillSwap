from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.dashboard import (
    DashboardResponse
)

from app.services.dashboard_service import (
    dashboard_data
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/me",
    response_model=DashboardResponse
)
def my_dashboard(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return dashboard_data(
        db,
        current_user.id
    )