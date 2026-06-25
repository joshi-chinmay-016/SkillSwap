from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Numeric,
    Enum as SqlEnum,
    String,
    CheckConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class PriceTriggerType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SESSION = "SESSION"
    FEEDBACK = "FEEDBACK"
    BADGE = "BADGE"
    ADMIN = "ADMIN"


class PriceHistory(Base):

    __tablename__ = "price_history"

    __table_args__ = (

        CheckConstraint(
            "price >= 0",
            name="ck_price_history_price_non_negative"
        ),

        CheckConstraint(
            "market_cap >= 0",
            name="ck_price_history_market_cap_non_negative"
        ),

        CheckConstraint(
            "volume >= 0",
            name="ck_price_history_volume_non_negative"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    mentor_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    market_cap: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    trigger_type: Mapped[PriceTriggerType] = mapped_column(
        SqlEnum(
            PriceTriggerType,
            name="price_trigger_type_enum"
        ),
        nullable=False
    )

    trigger_reference: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    volume: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )