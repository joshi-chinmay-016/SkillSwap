from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import (
    get_db
)

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityResponse
)

from app.services.availability_service import (
    add_availability,
    my_availability
)

router = APIRouter(
    prefix="/availability",
    tags=["Availability"]
)


@router.post(
    "",
    response_model=AvailabilityResponse
)
def create_availability_slot(
    request: AvailabilityCreate,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return add_availability(
        db,
        current_user.id,
        request.day_of_week,
        request.start_time,
        request.end_time
    )


@router.get(
    "/me",
    response_model=list[
        AvailabilityResponse
    ]
)
def get_my_slots(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return my_availability(
        db,
        current_user.id
    )