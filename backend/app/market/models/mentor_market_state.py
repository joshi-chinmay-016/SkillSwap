from decimal import Decimal

from sqlalchemy import (
    ForeignKey,
    Numeric,
    Float,
    Integer,
    DateTime,
    CheckConstraint,
    func
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class MentorMarketState(Base):

    __tablename__ = "mentor_market_state"

    __table_args__ = (

        CheckConstraint(
            "base_price > 0",
            name="ck_base_price_positive"
        ),

        CheckConstraint(
            "current_price >= 0",
            name="ck_current_price_non_negative"
        ),

        CheckConstraint(
            "total_supply >= 0",
            name="ck_total_supply_non_negative"
        ),

        CheckConstraint(
            "fundamentals_score >= 0 AND fundamentals_score <= 100",
            name="ck_market_fundamentals_score"
        ),

        CheckConstraint(
            "market_cap >= 0",
            name="ck_market_cap_non_negative"
        ),

        CheckConstraint(
            "version > 0",
            name="ck_version_positive"
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
        unique=True,
        nullable=False,
        index=True
    )

    base_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    current_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False
    )

    total_supply: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    fundamentals_score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    market_cap: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0.0000"),
        nullable=False
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )