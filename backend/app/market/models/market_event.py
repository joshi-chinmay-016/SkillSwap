from uuid import UUID as PythonUUID, uuid4
from enum import Enum

from sqlalchemy import (
    ForeignKey,
    DateTime,
    Enum as SqlEnum,
    func
)

from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
    JSONB
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.models.base import Base


class MarketEventType(str, Enum):

    SESSION_COMPLETED = "SESSION_COMPLETED"
    FEEDBACK_SUBMITTED = "FEEDBACK_SUBMITTED"
    BADGE_AWARDED = "BADGE_AWARDED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    ADMIN_UPDATE = "ADMIN_UPDATE"


class MarketEvent(Base):

    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    event_uuid: Mapped[PythonUUID] = mapped_column(
        PG_UUID(as_uuid=True),
        default=uuid4,
        unique=True,
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

    event_type: Mapped[MarketEventType] = mapped_column(
        SqlEnum(
            MarketEventType,
            name="market_event_type_enum"
        ),
        nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    processed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )