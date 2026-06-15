from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import (
    get_dashboard_stats
)


def dashboard_data(
    db: Session,
    user_id: int
):

    return get_dashboard_stats(
        db,
        user_id
    )