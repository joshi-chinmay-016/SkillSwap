from decimal import Decimal
from enum import Enum
from uuid import UUID as PythonUUID, uuid4

from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Numeric,
    Enum as SqlEnum,
    CheckConstraint,
    func
)

from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class Trade(Base):

    __tablename__ = "trades"

    __table_args__ = (

        CheckConstraint(
            "shares > 0",
            name="ck_trade_shares_positive"
        ),

        CheckConstraint(
            "executed_price > 0",
            name="ck_trade_price_positive"
        ),

        CheckConstraint(
            "total_amount > 0",
            name="ck_trade_total_amount_positive"
        ),

        CheckConstraint(
            "market_price_before >= 0",
            name="ck_market_price_before_non_negative"
        ),

        CheckConstraint(
            "market_price_after >= 0",
            name="ck_market_price_after_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    trade_uuid: Mapped[PythonUUID] = mapped_column(
        PG_UUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    trade_type: Mapped[TradeType] = mapped_column(
        SqlEnum(
            TradeType,
            name="trade_type_enum"
        ),
        nullable=False
    )

    shares: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    executed_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    market_price_before: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    market_price_after: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )