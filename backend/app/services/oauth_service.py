"""
SkillSwap Arena — Production OAuth Service (Phase 7)

Implements server-side Google and GitHub OAuth 2.0 flows, secure Redis-backed
one-time state tokens (CSRF protection), multi-provider account linking,
and short-lived ticket handoff to frontend.
"""
import time
import secrets
import logging
import urllib.parse
from typing import Any, Dict, Optional
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.profile import Profile
from app.models.oauth_identity import OAuthIdentity
from app.repositories.user_repository import get_user_by_email, create_user
from app.repositories.profile_repository import create_profile
from app.services.wallet_service import grant_welcome_bonus
from app.infrastructure.redis import (
    get_json,
    set_json,
    delete_keys,
    oauth_state_key,
    oauth_ticket_key,
)

logger = logging.getLogger("skillswap.oauth")


# =========================================================================
# 1. Secure State Generation & One-Time Validation (CSRF Defense)
# =========================================================================
def create_oauth_state(provider: str) -> str:
    """
    Generates a cryptographically random state token and stores it in Redis with TTL.
    """
    state = secrets.token_urlsafe(32)
    key = oauth_state_key(state)
    payload = {
        "provider": provider,
        "created_at": time.time(),
    }
    ttl = getattr(settings, "OAUTH_STATE_TTL_SECONDS", 600)
    set_json(key, payload, ttl=ttl)
    return state


def verify_and_consume_oauth_state(state: str, expected_provider: str) -> bool:
    """
    Validates the state token and atomically deletes it to prevent replay attacks.
    """
    if not state:
        return False

    key = oauth_state_key(state)
    data = get_json(key)
    if not data:
        return False

    # One-time consumption: delete immediately
    delete_keys(key)

    if data.get("provider") != expected_provider:
        logger.warning(f"OAuth state provider mismatch: expected {expected_provider}, got {data.get('provider')}")
        return False

    return True


import os

def get_oauth_setting(name: str, default: str = "") -> str:
    """Dynamically reads from os.environ, .env, or Settings."""
    val = os.getenv(name)
    if val:
        return val.strip()
    return getattr(settings, name, default) or default


# =========================================================================
# 2. Authorization URL Generators
# =========================================================================
def get_google_auth_url(state: str) -> str:
    """Constructs Google OAuth 2.0 authorization endpoint URL."""
    client_id = get_oauth_setting("GOOGLE_CLIENT_ID")
    redirect_uri = get_oauth_setting("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def get_github_auth_url(state: str) -> str:
    """Constructs GitHub OAuth authorization endpoint URL."""
    client_id = get_oauth_setting("GITHUB_CLIENT_ID")
    redirect_uri = get_oauth_setting("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user:email read:user",
        "state": state,
    }
    return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"


# =========================================================================
# 3. Server-Side Token Exchange & Identity Extraction
# =========================================================================
async def exchange_google_code(code: str) -> Dict[str, Any]:
    """
    Exchanges authorization code for Google access token and fetches user info.
    """
    client_id = get_oauth_setting("GOOGLE_CLIENT_ID")
    client_secret = get_oauth_setting("GOOGLE_CLIENT_SECRET")
    redirect_uri = get_oauth_setting("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(token_url, data=token_data)
        if token_resp.status_code != 200:
            logger.error(f"Google token exchange failed: {token_resp.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code with Google."
            )

        token_json = token_resp.json()
        access_token = token_json.get("access_token")

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_resp.status_code != 200:
            logger.error(f"Google userinfo request failed: {userinfo_resp.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from Google."
            )

        userinfo = userinfo_resp.json()
        sub = userinfo.get("sub")
        email = userinfo.get("email")
        name = userinfo.get("name") or (email.split("@")[0] if email else "Google User")
        avatar_url = userinfo.get("picture")

        if not sub or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user profile received from Google."
            )

        return {
            "provider_user_id": str(sub),
            "email": email.lower().strip(),
            "name": name.strip(),
            "avatar_url": avatar_url,
        }


async def exchange_github_code(code: str) -> Dict[str, Any]:
    """
    Exchanges authorization code for GitHub access token and fetches user info.
    """
    client_id = get_oauth_setting("GITHUB_CLIENT_ID")
    client_secret = get_oauth_setting("GITHUB_CLIENT_SECRET")
    redirect_uri = get_oauth_setting("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

    token_url = "https://github.com/login/oauth/access_token"
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        token_resp = await client.post(
            token_url,
            data=token_data,
            headers={"Accept": "application/json"}
        )
        if token_resp.status_code != 200:
            logger.error(f"GitHub token exchange failed: {token_resp.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code with GitHub."
            )

        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            logger.error(f"GitHub token error: {token_json}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code or GitHub OAuth configuration."
            )

        # 1. Fetch public profile
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SkillSwap-Arena-OAuth",
        }
        user_resp = await client.get("https://api.github.com/user", headers=headers)
        if user_resp.status_code != 200:
            logger.error(f"GitHub user request failed: {user_resp.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch user profile from GitHub."
            )

        gh_user = user_resp.json()
        gh_id = gh_user.get("id")
        gh_login = gh_user.get("login")
        name = gh_user.get("name") or gh_login or "GitHub User"
        avatar_url = gh_user.get("avatar_url")
        email = gh_user.get("email")

        # 2. Fetch email list if private
        if not email:
            emails_resp = await client.get("https://api.github.com/user/emails", headers=headers)
            if emails_resp.status_code == 200:
                emails_list = emails_resp.json()
                for em in emails_list:
                    if em.get("primary") and em.get("verified"):
                        email = em.get("email")
                        break
                if not email and emails_list:
                    email = emails_list[0].get("email")

        if not email:
            email = f"{gh_login}@users.noreply.github.com"

        return {
            "provider_user_id": str(gh_id),
            "email": email.lower().strip(),
            "name": name.strip(),
            "avatar_url": avatar_url,
        }


# =========================================================================
# 4. Multi-Provider Account Linking & Identity Resolution
# =========================================================================
def authenticate_or_link_oauth_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str,
    name: str,
    avatar_url: Optional[str] = None
) -> User:
    """
    Safely resolves or links user identity:
    1. Checks if (provider, provider_user_id) is already linked to a User.
    2. If not, checks if a User exists with the given email and links the provider.
    3. If no user exists, creates a new User, Profile, OAuthIdentity, and grants Welcome Bonus.
    """
    clean_email = email.lower().strip()

    # 1. Search existing OAuth identity
    existing_identity = (
        db.query(OAuthIdentity)
        .filter(
            OAuthIdentity.provider == provider,
            OAuthIdentity.provider_user_id == provider_user_id
        )
        .first()
    )

    if existing_identity:
        user = existing_identity.user
        if not user:
            user = db.query(User).filter(User.id == existing_identity.user_id).first()
        return user

    # 2. Search existing user by email (Account Linking)
    existing_user = get_user_by_email(db, clean_email)
    if existing_user:
        new_identity = OAuthIdentity(
            user_id=existing_user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=clean_email
        )
        db.add(new_identity)
        db.commit()
        db.refresh(existing_user)
        logger.info(f"Linked {provider} OAuth identity to existing user ID {existing_user.id} ({clean_email})")
        return existing_user

    # 3. Create brand new User with OAuth Identity
    try:
        random_pwd = "oauth_" + secrets.token_hex(24)
        user = User(
            name=name,
            email=clean_email,
            password_hash=random_pwd,
            oauth_provider=provider
        )
        user = create_user(db, user)

        safe_seed = urllib.parse.quote(name.strip().replace(" ", ""))
        final_avatar_url = avatar_url or f"https://api.dicebear.com/7.x/adventurer/svg?seed={safe_seed}"

        profile = Profile(
            user_id=user.id,
            avatar_url=final_avatar_url
        )
        create_profile(db, profile)

        new_identity = OAuthIdentity(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=clean_email
        )
        db.add(new_identity)
        db.commit()
        db.refresh(user)

        # Grant exactly-once welcome bonus (+5 coins)
        try:
            grant_welcome_bonus(db, user.id)
        except Exception as wb_err:
            logger.warning(f"Welcome bonus grant error for OAuth user {user.id}: {wb_err}")

        logger.info(f"Created new user ID {user.id} via {provider} OAuth ({clean_email})")
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating OAuth user for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user via OAuth."
        )


# =========================================================================
# 5. Short-Lived Frontend Handoff Ticket Management
# =========================================================================
def create_oauth_handoff_ticket(token: str, user_data: Dict[str, Any]) -> str:
    """
    Stores an authenticated session in Redis under a short-lived ticket token (60s).
    Allows frontend to securely retrieve JWT without passing it in URL query strings.
    """
    ticket = secrets.token_urlsafe(32)
    key = oauth_ticket_key(ticket)
    payload = {
        "access_token": token,
        "token_type": "bearer",
        "user": user_data,
    }
    ttl = getattr(settings, "OAUTH_TICKET_TTL_SECONDS", 60)
    set_json(key, payload, ttl=ttl)
    return ticket


def consume_oauth_handoff_ticket(ticket: str) -> Optional[Dict[str, Any]]:
    """
    Exchanges the one-time ticket for authenticated JWT payload and deletes it from Redis.
    """
    if not ticket:
        return None

    key = oauth_ticket_key(ticket)
    payload = get_json(key)
    if not payload:
        return None

    # One-time use: delete immediately
    delete_keys(key)
    return payload
