import urllib.parse
from typing import Optional, Dict, Any
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    Query
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies.current_user import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    OAuthExchangeRequest,
    OAuthExchangeResponse,
)
from app.services.auth_service import (
    register_user,
    login_user
)
from app.services.oauth_service import (
    create_oauth_state,
    verify_and_consume_oauth_state,
    get_google_auth_url,
    get_github_auth_url,
    exchange_google_code,
    exchange_github_code,
    authenticate_or_link_oauth_user,
    create_oauth_handoff_ticket,
    consume_oauth_handoff_ticket,
    get_oauth_setting,
)
from app.infrastructure.redis import (
    enforce_auth_rate_limit,
    enforce_action_rate_limit,
    get_client_ip,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================================
# 1. Standard Email & Password Authentication
# =========================================================================
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
    current_user = Depends(get_current_user),
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


# =========================================================================
# 2. Google OAuth 2.0 Endpoints
# =========================================================================
@router.get("/google")
def initiate_google_oauth(http_request: Request):
    """
    Initiates Google OAuth flow by generating a secure Redis-backed state token
    and redirecting to Google's consent screen.
    """
    client_ip = get_client_ip(http_request)
    enforce_action_rate_limit("oauth_initiate_google", client_ip, limit=30, window_seconds=60)

    client_id = get_oauth_setting("GOOGLE_CLIENT_ID")
    if not client_id:
        frontend_callback = get_oauth_setting("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth/callback")
        err_url = f"{frontend_callback}?error={urllib.parse.quote('Google OAuth is not configured on this server.')}"
        return RedirectResponse(url=err_url)

    state = create_oauth_state("google")
    auth_url = get_google_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handles redirect from Google with authorization code.
    Validates state token, exchanges code for identity, links/creates user,
    and redirects to frontend with a temporary one-time ticket.
    """
    frontend_callback = getattr(settings, "FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth/callback")

    if error:
        err_url = f"{frontend_callback}?error={urllib.parse.quote(f'Google authorization denied: {error}')}"
        return RedirectResponse(url=err_url)

    if not code or not state:
        err_url = f"{frontend_callback}?error={urllib.parse.quote('Missing authorization code or state from Google.')}"
        return RedirectResponse(url=err_url)

    # 1. Validate & consume one-time CSRF state
    if not verify_and_consume_oauth_state(state, "google"):
        err_url = f"{frontend_callback}?error={urllib.parse.quote('Invalid or expired OAuth state. Please try signing in again.')}"
        return RedirectResponse(url=err_url)

    try:
        # 2. Server-side token exchange and userinfo fetch
        user_info = await exchange_google_code(code)

        # 3. Authenticate or link user
        user = authenticate_or_link_oauth_user(
            db=db,
            provider="google",
            provider_user_id=user_info["provider_user_id"],
            email=user_info["email"],
            name=user_info["name"],
            avatar_url=user_info.get("avatar_url"),
        )

        # 4. Generate access token
        access_token = create_access_token({"sub": str(user.id)})

        from app.services.profile_service import get_or_create_profile
        profile = get_or_create_profile(db, user.id)

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": profile.avatar_url if profile else None,
        }

        # 5. Create short-lived handoff ticket in Redis (60s TTL)
        ticket = create_oauth_handoff_ticket(access_token, user_data)
        success_url = f"{frontend_callback}?ticket={ticket}"
        return RedirectResponse(url=success_url)

    except HTTPException as http_exc:
        err_url = f"{frontend_callback}?error={urllib.parse.quote(str(http_exc.detail))}"
        return RedirectResponse(url=err_url)
    except Exception as exc:
        err_url = f"{frontend_callback}?error={urllib.parse.quote('An unexpected error occurred during Google sign in.')}"
        return RedirectResponse(url=err_url)


# =========================================================================
# 3. GitHub OAuth Endpoints
# =========================================================================
@router.get("/github")
def initiate_github_oauth(http_request: Request):
    """
    Initiates GitHub OAuth flow with a secure Redis-backed state token.
    """
    client_ip = get_client_ip(http_request)
    enforce_action_rate_limit("oauth_initiate_github", client_ip, limit=30, window_seconds=60)

    client_id = get_oauth_setting("GITHUB_CLIENT_ID")
    if not client_id:
        frontend_callback = get_oauth_setting("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth/callback")
        err_url = f"{frontend_callback}?error={urllib.parse.quote('GitHub OAuth is not configured on this server.')}"
        return RedirectResponse(url=err_url)

    state = create_oauth_state("github")
    auth_url = get_github_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handles redirect from GitHub with authorization code.
    """
    frontend_callback = getattr(settings, "FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth/callback")

    if error:
        err_url = f"{frontend_callback}?error={urllib.parse.quote(f'GitHub authorization denied: {error}')}"
        return RedirectResponse(url=err_url)

    if not code or not state:
        err_url = f"{frontend_callback}?error={urllib.parse.quote('Missing authorization code or state from GitHub.')}"
        return RedirectResponse(url=err_url)

    # 1. Validate & consume one-time state
    if not verify_and_consume_oauth_state(state, "github"):
        err_url = f"{frontend_callback}?error={urllib.parse.quote('Invalid or expired OAuth state. Please try signing in again.')}"
        return RedirectResponse(url=err_url)

    try:
        # 2. Server-side token exchange
        user_info = await exchange_github_code(code)

        # 3. Authenticate or link user
        user = authenticate_or_link_oauth_user(
            db=db,
            provider="github",
            provider_user_id=user_info["provider_user_id"],
            email=user_info["email"],
            name=user_info["name"],
            avatar_url=user_info.get("avatar_url"),
        )

        # 4. Generate access token
        access_token = create_access_token({"sub": str(user.id)})

        from app.services.profile_service import get_or_create_profile
        profile = get_or_create_profile(db, user.id)

        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": profile.avatar_url if profile else None,
        }

        # 5. Create short-lived handoff ticket in Redis
        ticket = create_oauth_handoff_ticket(access_token, user_data)
        success_url = f"{frontend_callback}?ticket={ticket}"
        return RedirectResponse(url=success_url)

    except HTTPException as http_exc:
        err_url = f"{frontend_callback}?error={urllib.parse.quote(str(http_exc.detail))}"
        return RedirectResponse(url=err_url)
    except Exception as exc:
        err_url = f"{frontend_callback}?error={urllib.parse.quote('An unexpected error occurred during GitHub sign in.')}"
        return RedirectResponse(url=err_url)


# =========================================================================
# 4. Frontend OAuth Handoff Ticket Exchange
# =========================================================================
@router.post("/oauth/exchange", response_model=OAuthExchangeResponse)
def exchange_oauth_ticket(
    request: OAuthExchangeRequest,
    http_request: Request
):
    """
    Exchanges a one-time short-lived ticket (from OAuth redirect) for the authenticated JWT.
    """
    client_ip = get_client_ip(http_request)
    enforce_action_rate_limit("oauth_ticket_exchange", client_ip, limit=60, window_seconds=60)

    data = consume_oauth_handoff_ticket(request.ticket)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The OAuth authentication ticket is invalid or has expired. Please sign in again."
        )

    return OAuthExchangeResponse(
        access_token=data["access_token"],
        token_type=data.get("token_type", "bearer"),
        user=data["user"]
    )