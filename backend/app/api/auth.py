from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from app.dependencies.current_user import (
    get_current_user
)

from sqlalchemy.orm import Session

from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse
)

from app.services.auth_service import (
    register_user,
    login_user
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


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    try:

        token = login_user(
            db,
            request.email,
            request.password
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer"
        )

    except ValueError as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.get("/me")
def get_me(
    current_user = Depends(
        get_current_user
    )
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }