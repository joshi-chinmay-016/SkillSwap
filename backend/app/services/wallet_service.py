from sqlalchemy.orm import Session

from app.models.wallet import Wallet
from app.models.wallet_transaction import (
    WalletTransaction
)

from app.repositories.wallet_repository import (
    get_wallet,
    create_wallet,
    update_wallet,
    create_transaction,
    get_transaction_history
)

from app.services.notification_service import (
    create_user_notification
)


def create_user_wallet(
    db: Session,
    user_id: int
):

    wallet = get_wallet(
        db,
        user_id
    )

    if wallet:
        return wallet

    wallet = Wallet(
        user_id=user_id,
        balance=0,
        earned_coins=0,
        spent_coins=0
    )

    return create_wallet(
        db,
        wallet
    )


def credit_wallet(
    db: Session,
    user_id: int,
    amount: int,
    reason: str
):

    wallet = get_wallet(
        db,
        user_id
    )

    if not wallet:

        wallet = create_user_wallet(
            db,
            user_id
        )

    wallet.balance += amount

    wallet.earned_coins += amount

    update_wallet(
        db,
        wallet
    )

    create_transaction(
        db,
        WalletTransaction(
            user_id=user_id,
            amount=amount,
            type="credit",
            reason=reason
        )
    )

    create_user_notification(
        db,
        user_id,
        f"+{amount} Skill Coins earned ({reason})"
    )

    return wallet


def debit_wallet(
    db: Session,
    user_id: int,
    amount: int,
    reason: str
):

    wallet = get_wallet(
        db,
        user_id
    )

    if not wallet:

        raise Exception(
            "Wallet not found"
        )

    if wallet.balance < amount:

        raise Exception(
            "Insufficient balance"
        )

    wallet.balance -= amount

    wallet.spent_coins += amount

    update_wallet(
        db,
        wallet
    )

    create_transaction(
        db,
        WalletTransaction(
            user_id=user_id,
            amount=amount,
            type="debit",
            reason=reason
        )
    )

    return wallet


def wallet_dashboard(
    db: Session,
    user_id: int
):

    wallet = get_wallet(
        db,
        user_id
    )

    if not wallet:

        wallet = create_user_wallet(
            db,
            user_id
        )

    return wallet


def transaction_history(
    db: Session,
    user_id: int
):

    return get_transaction_history(
        db,
        user_id
    )