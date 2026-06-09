from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse
)

from app.services.auth_service import (
    register_user
)

from app.core.database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=RegisterResponse
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    try:

        register_user(
            db,
            request.name,
            request.email,
            request.password
        )

        return RegisterResponse(
            message="User created successfully"
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )