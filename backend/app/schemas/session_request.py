from pydantic import BaseModel, ConfigDict


class SessionRequestCreate(BaseModel):

    receiver_id: int

    skill_id: int


class SessionRequestResponse(BaseModel):

    id: int

    sender_id: int

    receiver_id: int

    skill_id: int

    status: str

    model_config = ConfigDict(from_attributes=True)