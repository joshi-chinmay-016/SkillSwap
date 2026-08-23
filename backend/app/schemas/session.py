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
    started_at: datetime | None = None
    completed_at: datetime | None = None
    actual_duration_minutes: int | None = None
    mentor_name: str | None = None
    learner_name: str | None = None
    skill_name: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class SessionPresenceResponse(BaseModel):
    session_id: int
    mentor_id: int
    mentor_present: bool
    learner_id: int
    learner_present: bool
    both_present: bool

    model_config = ConfigDict(from_attributes=True)


class SessionTimelineItem(BaseModel):
    id: str
    timestamp: datetime
    type: str  # "session_booked", "session_started", "topic_added", "note_saved", "action_item_created", "action_item_completed", "feedback_submitted", "session_completed"
    title: str
    description: str | None = None
    actor_id: int | None = None
    actor_name: str | None = None
    actor_role: str | None = None  # "mentor", "learner", "system"
    metadata: dict = {}

    model_config = ConfigDict(from_attributes=True)


class SessionTimelineResponse(BaseModel):
    session_id: int
    status: str
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_minutes: int
    actual_duration_minutes: int | None = None
    events: list[SessionTimelineItem]

    model_config = ConfigDict(from_attributes=True)