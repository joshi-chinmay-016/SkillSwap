from pydantic import BaseModel


class ProfileResponse(BaseModel):

    id: int
    user_id: int

    bio: str | None = None

    department: str | None = None

    year: int | None = None

    avatar_url: str | None = None

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):

    bio: str | None = None

    department: str | None = None

    year: int | None = None

    avatar_url: str | None = None