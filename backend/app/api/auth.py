from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
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
from app.core.rate_limiter import enforce_auth_rate_limit, get_client_ip

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
    http_request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(http_request)
    enforce_auth_rate_limit(f"{client_ip}:{request.email}")

    try:
        register_user(
            db,
            request.name,
            request.email,
            request.password,
            request.avatar_url
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
    http_request: Request,
    db: Session = Depends(get_db)
):
    client_ip = get_client_ip(http_request)
    enforce_auth_rate_limit(f"{client_ip}:{request.email}")

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
    ),
    db: Session = Depends(get_db)
):
    from app.services.profile_service import get_or_create_profile
    profile = get_or_create_profile(db, current_user.id)

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "avatar_url": profile.avatar_url if profile else None
    }