from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Numeric,
    DateTime,
    CheckConstraint,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class UserHolding(Base):

    __tablename__ = "user_holdings"

    __table_args__ = (

        UniqueConstraint(
            "user_id",
            "mentor_id",
            name="uq_user_mentor_holding"
        ),

        CheckConstraint(
            "shares_owned >= 0",
            name="ck_shares_owned_non_negative"
        ),

        CheckConstraint(
            "average_buy_price >= 0",
            name="ck_average_buy_price_non_negative"
        ),

        CheckConstraint(
            "invested_amount >= 0",
            name="ck_invested_amount_non_negative"
        ),

        CheckConstraint(
            "realized_profit >= 0",
            name="ck_realized_profit_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        index=True,
        nullable=False
    )

    shares_owned: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    average_buy_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    invested_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    realized_profit: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )