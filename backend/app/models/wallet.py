from sqlalchemy import (
    ForeignKey
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class Wallet(Base):

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True
    )

    balance: Mapped[int] = mapped_column(
        default=0
    )

    earned_coins: Mapped[int] = mapped_column(
        default=0
    )

    spent_coins: Mapped[int] = mapped_column(
        default=0
    )