from sqlalchemy import (
    ForeignKey,
    String
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
        String(20)
    )

    reason: Mapped[str] = mapped_column(
        String(255)
    )