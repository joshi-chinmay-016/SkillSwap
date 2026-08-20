from pydantic import BaseModel, ConfigDict


class SkillCreateRequest(BaseModel):

    name: str

    category: str

    description: str | None = None


class SkillResponse(BaseModel):

    id: int

    name: str

    category: str

    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserSkillRequest(BaseModel):

    skill_id: int

    type: str


class UserSkillResponse(BaseModel):

    id: int

    user_id: int

    skill_id: int

    type: str

    verification_status: str = "CLAIMED"

    score: float | None = None

    skill: SkillResponse | None = None

    model_config = ConfigDict(from_attributes=True)