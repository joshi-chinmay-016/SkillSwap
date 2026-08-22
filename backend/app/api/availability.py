from fastapi import (
    APIRouter,
    Depends,
    Query,
    status
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.current_user import get_current_user
from app.schemas.availability import (
    AvailabilityCreate,
    AvailabilityResponse,
    AllTimeAvailabilityRequest,
    MentorAvailabilitySlotsResponse
)
from app.services.availability_service import (
    add_availability,
    add_all_time_availability,
    my_availability,
    mentor_availability_list,
    get_mentor_available_slots,
    remove_availability
)

router = APIRouter(
    prefix="/availability",
    tags=["Availability"]
)


@router.post(
    "",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED
)
def create_availability_slot(
    request: AvailabilityCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return add_availability(
        db,
        current_user.id,
        start_time=request.start_time,
        end_time=request.end_time,
        day_of_week=request.day_of_week,
        specific_date=request.specific_date,
        all_days=request.all_days,
        timezone=request.timezone,
        is_active=request.is_active
    )


@router.post(
    "/all-time",
    response_model=list[AvailabilityResponse],
    status_code=status.HTTP_201_CREATED
)
def create_all_time_slots(
    request: AllTimeAvailabilityRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sets up all-time / full-week recurring availability for the authenticated mentor across all 7 days.
    """
    return add_all_time_availability(
        db,
        current_user.id,
        start_time=request.start_time,
        end_time=request.end_time,
        timezone=request.timezone,
        is_active=request.is_active
    )


@router.get(
    "/me",
    response_model=list[AvailabilityResponse]
)
def get_my_slots(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return my_availability(
        db,
        current_user.id
    )


@router.get(
    "/mentor/{mentor_id}",
    response_model=list[AvailabilityResponse]
)
def get_mentor_slots(
    mentor_id: int,
    db: Session = Depends(get_db)
):
    """
    Public / authenticated endpoint to retrieve a mentor's configured availability windows.
    """
    return mentor_availability_list(
        db,
        mentor_id
    )


@router.get(
    "/mentor/{mentor_id}/slots",
    response_model=MentorAvailabilitySlotsResponse
)
def get_mentor_bookable_slots(
    mentor_id: int,
    date: str = Query(..., description="Target date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """
    Authoritative computation of discrete bookable 60-minute slots for a mentor on a specific date.
    """
    return get_mentor_available_slots(
        db,
        mentor_id,
        date
    )


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_200_OK
)
def delete_slot(
    slot_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an availability slot owned by the authenticated mentor.
    """
    remove_availability(
        db,
        current_user.id,
        slot_id
    )
    return {"message": "Availability slot deleted successfully"}