from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class LearningActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    entity_type: str
    entity_id: int
    activity_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LearningActivityListResponse(BaseModel):
    activities: list[LearningActivityResponse]
    total: int
    page: int
    size: int
