from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionCreate(BaseModel):

    mentor_id: int

    skill_id: int

    scheduled_at: datetime

    meeting_link: str


class SessionResponse(BaseModel):

    id: int

    requester_id: int

    mentor_id: int

    skill_id: int

    scheduled_at: datetime

    meeting_link: str

    status: str

    mentor_name: str | None = None

    skill_name: str | None = None

    model_config = ConfigDict(from_attributes=True)