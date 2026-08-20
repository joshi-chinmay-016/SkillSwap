from datetime import datetime
from sqlalchemy import (
    ForeignKey,
    String,
    DateTime
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class WalletTransaction(Base):

    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    amount: Mapped[int]

    type: Mapped[str] = mapped_column(
        String(50)
    )

    reason: Mapped[str] = mapped_column(
        String(255)
    )

    reference_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )