from datetime import time, datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator


class AvailabilityCreate(BaseModel):
    day_of_week: Optional[str] = None
    specific_date: Optional[date] = None
    date: Optional[date] = None  # Alias for specific_date
    start_time: time
    end_time: time
    timezone: str = "UTC"
    is_active: bool = True
    all_days: bool = False  # Set to True for All-Time (Monday through Sunday)

    @model_validator(mode="after")
    def validate_date_and_day(self) -> "AvailabilityCreate":
        # Resolve date alias
        if self.date is not None and self.specific_date is None:
            self.specific_date = self.date
        elif self.specific_date is not None and self.date is None:
            self.date = self.specific_date

        # If all_days is True, normalize day_of_week
        if self.all_days:
            self.day_of_week = "All"
            return self

        # If specific_date is provided, auto-derive day_of_week if omitted
        if self.specific_date is not None and not self.day_of_week:
            self.day_of_week = self.specific_date.strftime("%A")

        if not self.day_of_week and not self.specific_date:
            raise ValueError("Either 'day_of_week' (e.g. 'Monday' or 'All'), 'all_days=True', or 'specific_date' (e.g. '2026-08-25') must be provided.")

        return self


class AllTimeAvailabilityRequest(BaseModel):
    start_time: time = time(9, 0)
    end_time: time = time(18, 0)
    timezone: str = "UTC"
    is_active: bool = True


class AvailabilityResponse(BaseModel):
    id: int
    mentor_id: int
    day_of_week: str
    specific_date: Optional[date] = None
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