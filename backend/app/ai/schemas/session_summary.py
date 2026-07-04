from typing import List

from pydantic import (
    BaseModel,
    Field
)


class SessionSummaryRequest(BaseModel):

    session_notes: str = Field(
        min_length=20
    )


class SessionSummaryResponse(BaseModel):

    summary: str

    key_points: List[str]

    action_items: List[str]

    recommended_resources: List[str]