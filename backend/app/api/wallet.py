from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.core.database import get_db

from app.dependencies.current_user import (
    get_current_user
)

from app.schemas.wallet import (
    WalletResponse
)

from app.schemas.wallet_transaction import (
    WalletTransactionResponse
)

from app.services.wallet_service import (
    wallet_dashboard,
    transaction_history
)

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)


@router.get(
    "/me",
    response_model=WalletResponse
)
def my_wallet(
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return wallet_dashboard(
        db,
        current_user.id
    )


@router.get(
    "/transactions",
    response_model=list[
        WalletTransactionResponse
    ]
)
def my_transactions(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(
        get_current_user
    ),
    db: Session = Depends(
        get_db
    )
):

    return transaction_history(
        db,
        current_user.id,
        page=page,
        page_size=page_size
    )