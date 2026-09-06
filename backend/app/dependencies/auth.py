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
from app.services.session_cache import SessionCache
from app.core.redis_client import get_redis_client


@dataclass
class CurrentUser:
    user: User
    session_id: UUID


async def get_current_user(
    access_token: str | None = Cookie(default=None, alias="access_token"),
    db: AsyncSession = Depends(get_db_session),
    redis = Depends(get_redis_client),
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

    session_id_uuid = UUID(session_id)
    
    # Check Redis cache first
    session_cache = SessionCache(redis)
    cached_session = await session_cache.get_session(session_id_uuid)
    
    if cached_session:
        # Session found in Redis - verify it's not revoked/expired
        if cached_session.get("revoked_at") is not None:
            raise AppError("AUTH_SESSION_REVOKED", 401, "Session has been revoked.")
        
        expires_at = datetime.fromisoformat(cached_session["expires_at"])
        # cached_session["expires_at"] is offset-naive, make comparison offset-naive
        if expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            raise AppError("AUTH_SESSION_REVOKED", 401, "Session has expired.")
        
        # Load user
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise AppError("AUTH_UNAUTHENTICATED", 401, "User not found.")
        
        # Update last_used_at in cache
        await session_cache.update_session_last_used(session_id_uuid)
        
        return CurrentUser(user=user, session_id=session_id_uuid)
    
    # Fallback to database
    # Load user
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppError("AUTH_UNAUTHENTICATED", 401, "User not found.")

    # Load session and verify it's not revoked/expired
    result = await db.execute(select(Session).where(Session.id == session_id_uuid))
    session = result.scalar_one_or_none()
    if not session or session.revoked_at is not None or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise AppError("AUTH_SESSION_REVOKED", 401, "Session has been revoked.")

    # Cache the session for future requests
    # We need access_token, refresh_token, csrf_token which we don't have here
    # For now, just return - the session will be cached on next login/refresh
    return CurrentUser(user=user, session_id=session_id_uuid)