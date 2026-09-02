from fastapi import Cookie, Header, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AppError
from app.core.security import constant_time_compare
from app.db.session import get_db_session
from app.models.security_log import SecurityLog
from app.core.config import settings as settings_obj


async def validate_csrf(
    request: Request,
    csrf_token: str | None = Cookie(default=None, alias="csrf_token"),
    x_csrf_token: str | None = Header(default=None, alias="X-CSRF-Token"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    if not csrf_token or not x_csrf_token:
        # Log CSRF failure
        await _log_csrf_failure(request, db, "missing")
        raise AppError("CSRF_TOKEN_MISSING", 403, "CSRF token missing.")

    if not constant_time_compare(csrf_token, x_csrf_token):
        # Log CSRF failure
        await _log_csrf_failure(request, db, "mismatch")
        raise AppError("CSRF_TOKEN_INVALID", 403, "CSRF token invalid.")


async def _log_csrf_failure(request: Request, db: AsyncSession, reason: str) -> None:
    try:
        log = SecurityLog(
            user_id=None,
            session_id=None,
            device_id=None,
            event_type="CSRF_FAILURE",
            severity="warning",
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"reason": reason},
        )
        db.add(log)
        await db.commit()
    except Exception:
        await db.rollback()