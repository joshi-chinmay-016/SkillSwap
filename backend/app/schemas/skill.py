from pydantic import BaseModel


class SkillCreateRequest(BaseModel):

    name: str

    category: str

    description: str | None = None


class SkillResponse(BaseModel):

    id: int

    name: str

    category: str

    description: str | None = None

    class Config:
        from_attributes = True


class UserSkillRequest(BaseModel):

    skill_id: int

    type: str