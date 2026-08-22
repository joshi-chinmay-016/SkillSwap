from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):
    mentor_id: int
    skill_id: int
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_link: str | None = None


class SessionResponse(BaseModel):
    id: int
    requester_id: int
    mentor_id: int
    skill_id: int
    scheduled_at: datetime
    duration_minutes: int = 60
    meeting_room_id: str | None = None
    meeting_link: str
    status: str
    mentor_name: str | None = None
    learner_name: str | None = None
    skill_name: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)