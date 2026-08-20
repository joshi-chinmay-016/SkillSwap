from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction


def get_wallet(
    db: Session,
    user_id: int
):
    return (
        db.query(Wallet)
        .filter(Wallet.user_id == user_id)
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


def get_transaction_by_reference_id(
    db: Session,
    reference_id: str
):
    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.reference_id == reference_id)
        .first()
    )


def get_transaction_history(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20
):
    offset = (page - 1) * page_size
    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == user_id)
        .order_by(desc(WalletTransaction.id))
        .offset(offset)
        .limit(page_size)
        .all()
    )