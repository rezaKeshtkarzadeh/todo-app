import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from .session import Session


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    token_family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.id"), nullable=True
    )

    session: Mapped["Session"] = relationship("Session", backref="refresh_tokens")
    replaced_by: Mapped["RefreshToken | None"] = relationship(
        "RefreshToken", remote_side=[id], backref="replaced_token"
    )

    __table_args__ = (
        Index("ix_refresh_tokens_session_id", "session_id"),
        Index("ix_refresh_tokens_token_family_id", "token_family_id"),
        Index("ix_refresh_tokens_replaced_by_id", "replaced_by_id"),
    )