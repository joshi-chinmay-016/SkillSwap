from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):

    id: int
    user_id: int

    bio: str | None = None

    department: str | None = None

    year: int | None = None

    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdateRequest(BaseModel):

    bio: str | None = None

    department: str | None = None

    year: int | None = None

    avatar_url: str | None = None