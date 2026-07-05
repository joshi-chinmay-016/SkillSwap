from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.skill import (
    SkillCreateRequest,
    SkillResponse,
    UserSkillRequest
)

from app.services.skill_service import (
    list_skills,
    create_new_skill,
    assign_skill_to_user,
    list_user_skills
)

router = APIRouter(
    prefix="/skills",
    tags=["Skills"]
)


@router.get(
    "",
    response_model=list[SkillResponse]
)
def get_skills(
    db: Session = Depends(get_db)
):

    return list_skills(
        db
    )


@router.post(
    "",
    response_model=SkillResponse
)
def create_skill(
    request: SkillCreateRequest,
    db: Session = Depends(get_db)
):

    return create_new_skill(
        db,
        request.name,
        request.category,
        request.description
    )


@router.get(
    "/me"
)
def get_my_skills(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return list_user_skills(
        db,
        current_user.id
    )


@router.get(
    "/user/{user_id}"
)
def get_user_skills_list(
    user_id: int,
    db: Session = Depends(get_db)
):

    return list_user_skills(
        db,
        user_id
    )


@router.post(
    "/me"
)
def add_my_skill(
    request: UserSkillRequest,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(get_db)
):

    return assign_skill_to_user(
        db,
        current_user.id,
        request.skill_id,
        request.type
    )