import pytest
import uuid
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.services.auth_service import register_user
from app.services.wallet_service import (
    grant_welcome_bonus,
    credit_wallet,
    debit_wallet,
    wallet_dashboard,
    transaction_history
)
from fastapi import HTTPException


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_new_user_registration_grants_five_welcome_coins(db_session: Session):
    test_id = uuid.uuid4().hex[:8]
    user = register_user(
        db=db_session,
        name=f"New User {test_id}",
        email=f"newuser_{test_id}@example.com",
        password="Password123!"
    )

    # Verify wallet balance
    wallet = wallet_dashboard(db_session, user.id)
    assert wallet is not None
    assert wallet.balance == 5
    assert wallet.earned_coins == 5
    assert wallet.spent_coins == 0

    # Verify transaction history
    txs = transaction_history(db_session, user.id)
    assert len(txs) == 1
    assert txs[0].amount == 5
    assert txs[0].type == "WELCOME_BONUS"
    assert txs[0].reference_id == f"WELCOME_BONUS:{user.id}"


def test_welcome_bonus_is_idempotent(db_session: Session):
    test_id = uuid.uuid4().hex[:8]
    user = User(
        name=f"Idempotency User {test_id}",
        email=f"idem_{test_id}@example.com",
        password_hash="hashed"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Call grant_welcome_bonus 3 times
    w1 = grant_welcome_bonus(db_session, user.id)
    w2 = grant_welcome_bonus(db_session, user.id)
    w3 = grant_welcome_bonus(db_session, user.id)

    # Balance must remain exactly 5
    assert w1.balance == 5
    assert w2.balance == 5
    assert w3.balance == 5

    # Transaction count must remain exactly 1
    txs = transaction_history(db_session, user.id)
    assert len(txs) == 1


def test_wallet_credit_and_debit_integrity(db_session: Session):
    test_id = uuid.uuid4().hex[:8]
    user = User(
        name=f"Integrity User {test_id}",
        email=f"integrity_{test_id}@example.com",
        password_hash="hashed"
    )
    db_session.add(user)
    db_session.commit()

    # Initial Welcome Bonus
    grant_welcome_bonus(db_session, user.id)

    # Credit +10 coins
    w = credit_wallet(db_session, user.id, amount=10, reason="Peer Teaching Reward", reference_id=f"TEACH:{test_id}")
    assert w.balance == 15
    assert w.earned_coins == 15

    # Debit -5 coins
    w = debit_wallet(db_session, user.id, amount=5, reason="Booked Session", reference_id=f"BOOK:{test_id}")
    assert w.balance == 10
    assert w.spent_coins == 5

    # Debit failure on insufficient balance
    with pytest.raises(HTTPException) as exc_info:
        debit_wallet(db_session, user.id, amount=999, reason="Overdraft Test")
    assert exc_info.value.status_code == 400
    assert "Insufficient" in exc_info.value.detail


def test_duplicate_reference_id_prevented(db_session: Session):
    test_id = uuid.uuid4().hex[:8]
    user = User(
        name=f"Ref User {test_id}",
        email=f"ref_{test_id}@example.com",
        password_hash="hashed"
    )
    db_session.add(user)
    db_session.commit()

    ref = f"REF_TEST:{test_id}"

    # First credit
    credit_wallet(db_session, user.id, amount=5, reason="First Credit", reference_id=ref)

    # Replayed credit with same reference_id
    w2 = credit_wallet(db_session, user.id, amount=5, reason="Duplicate Credit", reference_id=ref)

    # Balance should not double
    assert w2.balance == 5
