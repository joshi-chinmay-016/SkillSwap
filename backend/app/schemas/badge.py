from pydantic import BaseModel, ConfigDict


class BadgeResponse(BaseModel):

    id: int

    user_id: int

    name: str

    description: str

    model_config = ConfigDict(from_attributes=True)