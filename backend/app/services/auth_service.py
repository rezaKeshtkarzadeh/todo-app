from datetime import datetime, timezone
from typing import Optional, cast
import uuid
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    encode_refresh_token,
    decode_refresh_token,
    verify_refresh_token,
    generate_csrf_token,
)
from app.core.cookies import set_access_token_cookie, set_refresh_token_cookie, set_csrf_token_cookie
from app.models.session import Session
from app.models.refresh_token import RefreshToken
from app.models.device import Device
from app.services.logging_service import log_security_event


async def rotate_refresh_token(
    db: AsyncSession,
    request,
    response,
    refresh_token_cookie: str,
) -> None:
    """
    Rotate refresh token - implements the full rotation flow:
    1. Parse token_id.secret from cookie
    2. Look up RefreshToken by token_id
    3. Validate Session (exists, not revoked, not expired)
    4. Validate token expiration/revocation/usage
    5. Argon2 verify secret against token_hash
    6. Atomically consume current token (UPDATE ... WHERE used_at IS NULL AND revoked_at IS NULL)
    7. If rowcount == 0 → treat as reuse (call handle_reuse)
    8. Create replacement RefreshToken (same session_id, same token_family_id)
    9. Set old token's replaced_by_id
    10. Issue new Access Token
    11. Update sessions.last_used_at and devices.last_seen_at
    12. Set replacement cookies
    13. Write REFRESH_SUCCESS Security Log
    """
    # Parse token_id.secret from cookie
    parsed = decode_refresh_token(refresh_token_cookie)
    if not parsed:
        raise AppError("AUTH_REFRESH_FAILED", 401, "Invalid refresh token format.")
    
    token_id, secret = parsed
    
    # Look up RefreshToken by token_id
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.id == uuid.UUID(token_id))
    )
    refresh_token = result.scalar_one_or_none()
    
    if not refresh_token:
        raise AppError("AUTH_REFRESH_FAILED", 401, "Refresh token not found.")
    
    # Load associated Session
    result = await db.execute(
        select(Session).where(Session.id == refresh_token.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise AppError("AUTH_SESSION_REVOKED", 401, "Session not found.")
    
    if session.revoked_at is not None:
        raise AppError("AUTH_SESSION_REVOKED", 401, "Session has been revoked.")
    
    if session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise AppError("AUTH_SESSION_REVOKED", 401, "Session has expired.")
    
    # Validate token state
    if refresh_token.revoked_at is not None:
        raise AppError("AUTH_REFRESH_FAILED", 401, "Refresh token has been revoked.")
    
    if refresh_token.used_at is not None:
        # Token already used - this is reuse detection
        await handle_refresh_token_reuse(db, request, response, refresh_token)
        return
    
    if refresh_token.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise AppError("AUTH_REFRESH_FAILED", 401, "Refresh token has expired.")
    
    # Argon2 verify secret
    if not verify_refresh_token(refresh_token.token_hash, secret):
        raise AppError("AUTH_REFRESH_FAILED", 401, "Invalid refresh token.")
    
    # Atomically consume current token
    # UPDATE refresh_tokens SET used_at = now() WHERE id = :id AND used_at IS NULL AND revoked_at IS NULL
    stmt = (
        update(RefreshToken)
        .where(
            RefreshToken.id == refresh_token.id,
            RefreshToken.used_at.is_(None),
            RefreshToken.revoked_at.is_(None),
        )
        .values(used_at=datetime.now(timezone.utc).replace(tzinfo=None))
        .execution_options(synchronize_session="fetch")
    )
    result = cast(CursorResult, await db.execute(stmt))
    
    if result.rowcount == 0:
        # Another request already consumed this token - reuse detected
        await handle_refresh_token_reuse(db, request, response, refresh_token)
        return
    
    # Create replacement RefreshToken
    new_token_id, new_secret = generate_refresh_token()
    new_token_hash = hash_refresh_token(new_secret)
    
    replacement_token = RefreshToken(
        id=uuid.UUID(new_token_id),
        session_id=session.id,
        token_family_id=refresh_token.token_family_id,
        token_hash=new_token_hash,
        expires_at=refresh_token.expires_at,
    )
    db.add(replacement_token)
    
    # Flush the new token first so it exists in the database
    await db.flush()
    
    # Set old token's replaced_by_id (now the new token exists in DB)
    refresh_token.replaced_by_id = uuid.UUID(new_token_id)
    
    # Issue new Access Token
    access_token = create_access_token(str(session.user_id), str(session.id))
    
    # Update timestamps
    session.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Update device last_seen_at
    result = await db.execute(
        select(Device).where(Device.id == session.device_id)
    )
    device = result.scalar_one_or_none()
    if device:
        device.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
    
    # Set replacement cookies
    set_access_token_cookie(response, access_token)
    new_refresh_token_str = encode_refresh_token(new_token_id, new_secret)
    set_refresh_token_cookie(response, new_refresh_token_str)
    
    # Generate and set new CSRF token
    new_csrf_token = generate_csrf_token()
    set_csrf_token_cookie(response, new_csrf_token)
    
    # Write REFRESH_SUCCESS Security Log
    await log_security_event(
        db=db,
        event_type="REFRESH_SUCCESS",
        severity="info",
        user_id=session.user_id,
        session_id=session.id,
        device_id=session.device_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"token_family_id": str(refresh_token.token_family_id)},
    )


async def handle_refresh_token_reuse(
    db: AsyncSession,
    request,
    response,
    refresh_token: RefreshToken,
) -> None:
    """
    Handle refresh token reuse detection:
    1. Record REFRESH_TOKEN_REUSED Security Log
    2. Revoke entire token family (mark all non-revoked tokens in family as revoked)
    3. Revoke associated Session
    4. Clear auth cookies
    5. Raise AUTH_REFRESH_TOKEN_REUSED
    """
    # Log reuse event
    await log_security_event(
        db=db,
        event_type="REFRESH_TOKEN_REUSED",
        severity="critical",
        user_id=None,
        session_id=refresh_token.session_id,
        device_id=None,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"token_family_id": str(refresh_token.token_family_id)},
    )
    
    # Load session to get user_id and device_id
    result = await db.execute(
        select(Session).where(Session.id == refresh_token.session_id)
    )
    session = result.scalar_one_or_none()
    
    if session:
        # Revoke entire token family
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_family_id == refresh_token.token_family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await db.execute(stmt)
        
        # Revoke associated session
        session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.revoke_reason = "refresh_token_reuse"
        
        # Log session revocation
        await log_security_event(
            db=db,
            event_type="SESSION_REVOKED",
            severity="critical",
            user_id=session.user_id,
            session_id=session.id,
            device_id=session.device_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"scope": "reuse_detection", "token_family_id": str(refresh_token.token_family_id)},
        )
    
    # Clear auth cookies
    from app.core.cookies import clear_all_auth_cookies
    clear_all_auth_cookies(response)
    
    # Commit the revocation
    await db.commit()
    
    raise AppError("AUTH_REFRESH_TOKEN_REUSED", 401, "Refresh token reuse detected. Session revoked.")