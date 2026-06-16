from pydantic import BaseModel


class SkillAnalyticsResponse(
    BaseModel
):

    skill_id: int

    skill_name: str

    count: int