from pydantic import BaseModel


class BadgeResponse(BaseModel):

    id: int

    user_id: int

    name: str

    description: str

    class Config:
        from_attributes = True