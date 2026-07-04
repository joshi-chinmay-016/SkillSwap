from pydantic import BaseModel


class MatchResponse(BaseModel):

    user_id: int

    name: str

    department: str | None = None

    year: int | None = None

    skill: str

    type: str