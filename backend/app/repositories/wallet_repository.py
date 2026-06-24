from sqlalchemy.orm import Session

from app.models.wallet import Wallet

from app.models.wallet_transaction import (
    WalletTransaction
)


def get_wallet(
    db: Session,
    user_id: int
):

    return (
        db.query(Wallet)
        .filter(
            Wallet.user_id == user_id
        )
        .first()
    )


def create_wallet(
    db: Session,
    wallet: Wallet
):

    db.add(wallet)

    db.commit()

    db.refresh(wallet)

    return wallet


def update_wallet(
    db: Session,
    wallet: Wallet
):

    db.commit()

    db.refresh(wallet)

    return wallet


def create_transaction(
    db: Session,
    transaction: WalletTransaction
):

    db.add(transaction)

    db.commit()

    db.refresh(transaction)

    return transaction


def get_transaction_history(
    db: Session,
    user_id: int
):

    return (
        db.query(
            WalletTransaction
        )
        .filter(
            WalletTransaction.user_id
            ==
            user_id
        )
        .all()
    )