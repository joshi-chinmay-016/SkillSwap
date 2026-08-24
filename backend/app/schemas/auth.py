from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    avatar_url: Optional[str] = None


class RegisterResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class OAuthExchangeRequest(BaseModel):
    ticket: str


class OAuthExchangeResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]