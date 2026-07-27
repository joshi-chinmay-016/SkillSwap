from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class BadgeDTO(BaseModel):
    name: str
    icon: str
    tier: str

    model_config = ConfigDict(from_attributes=True)


class AchievementResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    badge: BadgeDTO
    icon: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None
    xp_reward: int = 50
    current_value: int = 0
    target_value: int = 1
    progress_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class LevelResponse(BaseModel):
    current_level: int = 1
    current_xp: int = 0
    next_level: int = 2
    xp_to_next_level: int = 100
    progress_percentage: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class AchievementProgressResponse(BaseModel):
    level: LevelResponse
    unlocked_count: int = 0
    total_count: int = 0
    achievements: List[AchievementResponse] = []

    model_config = ConfigDict(from_attributes=True)
