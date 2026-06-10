from fastapi import (
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordBearer
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.core.security import (
    decode_access_token
)

from app.repositories.user_repository import (
    get_user_by_id
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    payload = decode_access_token(
        token
    )

    if not payload:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")

    user = get_user_by_id(
        db,
        int(user_id)
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user