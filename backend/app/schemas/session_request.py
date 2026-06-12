from pydantic import BaseModel


class SessionRequestCreate(BaseModel):

    receiver_id: int

    skill_id: int


class SessionRequestResponse(BaseModel):

    id: int

    sender_id: int

    receiver_id: int

    skill_id: int

    status: str

    class Config:
        from_attributes = True