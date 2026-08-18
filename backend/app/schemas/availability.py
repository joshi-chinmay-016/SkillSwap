from datetime import time

from pydantic import BaseModel, ConfigDict


class AvailabilityCreate(
    BaseModel
):

    day_of_week: str

    start_time: time

    end_time: time


class AvailabilityResponse(
    BaseModel
):

    id: int

    mentor_id: int

    day_of_week: str

    start_time: time

    end_time: time

    model_config = ConfigDict(from_attributes=True)