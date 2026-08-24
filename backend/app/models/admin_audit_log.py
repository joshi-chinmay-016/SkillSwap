from datetime import datetime
from sqlalchemy import ForeignKey, String, Text, DateTime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    admin_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False
    )

    target_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    target_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=sa.func.now(),
        index=True,
        nullable=False
    )

    admin_user = relationship(
        "User",
        foreign_keys=[admin_user_id]
    )
