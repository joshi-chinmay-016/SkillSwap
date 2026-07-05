from fastapi import (
    APIRouter,
    Depends
)

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest
)

from app.services.profile_service import (
    get_or_create_profile,
    update_user_profile
)

from app.core.database import get_db

from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/profiles",
    tags=["Profiles"]
)


@router.get(
    "/me",
    response_model=ProfileResponse
)
def get_my_profile(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return get_or_create_profile(
        db,
        current_user.id
    )


@router.get(
    "/{user_id}",
    response_model=ProfileResponse
)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):

    return get_or_create_profile(
        db,
        user_id
    )


@router.put(
    "/me",
    response_model=ProfileResponse
)
def update_my_profile(
    request: ProfileUpdateRequest,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return update_user_profile(
        db,
        current_user.id,
        request.bio,
        request.department,
        request.year,
        request.avatar_url
    )