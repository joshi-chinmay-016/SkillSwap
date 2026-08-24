from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.dependencies.current_user import get_current_user


def require_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not getattr(current_user, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended. Please contact platform support."
        )
    return current_user


def require_admin(
    current_user: User = Depends(require_active_user)
) -> User:
    if getattr(current_user, "role", "USER").upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Administrator privileges required."
        )
    return current_user


def require_role(required_role: str):
    def role_checker(current_user: User = Depends(require_active_user)) -> User:
        user_role = getattr(current_user, "role", "USER").upper()
        if user_role != required_role.upper() and user_role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: {required_role} privileges required."
            )
        return current_user
    return role_checker
