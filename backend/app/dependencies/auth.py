from dataclasses import dataclass
from uuid import UUID
from datetime import datetime, timezone
from fastapi import Cookie, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.models.user import User
from app.models.session import Session


@dataclass
class CurrentUser:
    user: User
    session_id: UUID


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db_session),
) -> CurrentUser:
    if not access_token:
        raise AppError("AUTH_UNAUTHENTICATED", 401, "Authentication required.")

    try:
        payload = decode_access_token(access_token)
    except ValueError as e:
        raise AppError("AUTH_UNAUTHENTICATED", 401, str(e)) from e

    user_id = payload.get("sub")
    session_id = payload.get("sid")

    if not user_id or not session_id:
        raise AppError("AUTH_UNAUTHENTICATED", 401, "Invalid token payload.")

    # Load user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("AUTH_UNAUTHENTICATED", 401, "User not found.")

    # Load session and verify it's not revoked/expired
    result = await db.execute(select(Session).where(Session.id == UUID(session_id)))
    session = result.scalar_one_or_none()
    if not session or session.revoked_at is not None or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise AppError("AUTH_SESSION_REVOKED", 401, "Session has been revoked.")

    return CurrentUser(user=user, session_id=UUID(session_id))