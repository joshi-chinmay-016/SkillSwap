from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str = "GENERAL"
    title: str | None = None
    message: str
    related_session_id: int | None = None
    is_read: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)