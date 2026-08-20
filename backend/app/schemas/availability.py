from datetime import time, datetime
from pydantic import BaseModel, ConfigDict


class AvailabilityCreate(BaseModel):
    day_of_week: str
    start_time: time
    end_time: time
    timezone: str = "UTC"
    is_active: bool = True


class AvailabilityResponse(BaseModel):
    id: int
    mentor_id: int
    day_of_week: str
    start_time: time
    end_time: time
    timezone: str = "UTC"
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class BookableSlot(BaseModel):
    slot_start: datetime
    slot_end: datetime
    duration_minutes: int = 60
    formatted_time: str
    is_available: bool = True


class MentorAvailabilitySlotsResponse(BaseModel):
    mentor_id: int
    date: str
    day_of_week: str
    timezone: str = "UTC"
    slots: list[BookableSlot]