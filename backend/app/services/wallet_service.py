from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.repositories.wallet_repository import (
    get_wallet,
    create_wallet,
    update_wallet,
    create_transaction,
    get_transaction_by_reference_id,
    get_transaction_history
)
from app.services.notification_service import create_user_notification


def create_user_wallet(
    db: Session,
    user_id: int
) -> Wallet:
    wallet = get_wallet(db, user_id)
    if wallet:
        return wallet

    wallet = Wallet(
        user_id=user_id,
        balance=0,
        earned_coins=0,
        spent_coins=0
    )
    return create_wallet(db, wallet)


def grant_welcome_bonus(
    db: Session,
    user_id: int
) -> Wallet:
    """
    Idempotently grants exactly +5 Welcome Bonus coins to genuinely NEW account registrations.
    Uses reference_id="WELCOME_BONUS:{user_id}" to guarantee exactly-once execution.
    """
    ref_id = f"WELCOME_BONUS:{user_id}"

    # 1. Fetch or create wallet
    wallet = get_wallet(db, user_id)
    if not wallet:
        wallet = Wallet(
            user_id=user_id,
            balance=0,
            earned_coins=0,
            spent_coins=0
        )
        db.add(wallet)
        db.flush()

    # 2. Idempotency Check: Verify if WELCOME_BONUS reference_id already exists
    existing_tx = get_transaction_by_reference_id(db, ref_id)
    if existing_tx:
        return wallet

    # 3. Apply +5 Welcome Bonus atomically
    welcome_amount = 5
    wallet.balance += welcome_amount
    wallet.earned_coins += welcome_amount

    tx = WalletTransaction(
        user_id=user_id,
        amount=welcome_amount,
        type="WELCOME_BONUS",
        reason="Welcome Bonus — 5 Skill Coins",
        reference_id=ref_id,
        created_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    try:
        create_user_notification(
            db,
            user_id,
            "+5 Welcome Bonus Skill Coins credited to your wallet!"
        )
    except Exception:
        pass

    return wallet


def credit_wallet(
    db: Session,
    user_id: int,
    amount: int,
    reason: str,
    reference_id: str | None = None,
    transaction_type: str = "credit"
) -> Wallet:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credit amount must be positive"
        )

    # Idempotency check if reference_id provided
    if reference_id:
        existing_tx = get_transaction_by_reference_id(db, reference_id)
        if existing_tx:
            return get_wallet(db, user_id)

    wallet = get_wallet(db, user_id)
    if not wallet:
        wallet = create_user_wallet(db, user_id)

    wallet.balance += amount
    wallet.earned_coins += amount
    update_wallet(db, wallet)

    tx = WalletTransaction(
        user_id=user_id,
        amount=amount,
        type=transaction_type,
        reason=reason,
        reference_id=reference_id,
        created_at=datetime.utcnow()
    )
    create_transaction(db, tx)

    try:
        create_user_notification(
            db,
            user_id,
            f"+{amount} Skill Coins ({reason})"
        )
    except Exception:
        pass

    return wallet


def debit_wallet(
    db: Session,
    user_id: int,
    amount: int,
    reason: str,
    reference_id: str | None = None
) -> Wallet:
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debit amount must be positive"
        )

    if reference_id:
        existing_tx = get_transaction_by_reference_id(db, reference_id)
        if existing_tx:
            return get_wallet(db, user_id)

    wallet = get_wallet(db, user_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    if wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient wallet balance"
        )

    wallet.balance -= amount
    wallet.spent_coins += amount
    update_wallet(db, wallet)

    tx = WalletTransaction(
        user_id=user_id,
        amount=amount,
        type="debit",
        reason=reason,
        reference_id=reference_id,
        created_at=datetime.utcnow()
    )
    create_transaction(db, tx)

    return wallet


def wallet_dashboard(
    db: Session,
    user_id: int
) -> Wallet:
    wallet = get_wallet(db, user_id)
    if not wallet:
        wallet = create_user_wallet(db, user_id)
    return wallet


def transaction_history(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> list[WalletTransaction]:
    return get_transaction_history(db, user_id, page=page, page_size=page_size)