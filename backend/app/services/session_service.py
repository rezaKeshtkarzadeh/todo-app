from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.refresh_token import RefreshToken
from app.models.device import Device
from app.services.logging_service import log_security_event


async def revoke_session_by_id(
    db: AsyncSession,
    request,
    session_id: UUID,
    user_id: UUID,
    scope: str,
    current_session_id: Optional[UUID] = None,
) -> bool:
    """
    Revoke a single session and its refresh token family.
    Returns True if session was found and revoked.
    """
    result = await db.execute(
        select(Session).where(
            and_(Session.id == session_id, Session.user_id == user_id)
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        return False

    # Revoke the session
    session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.revoke_reason = f"revoked_{scope}"

    # Revoke all tokens in the same family
    stmt = (
        update(RefreshToken)
        .where(
            and_(
                RefreshToken.token_family_id == session.token_family_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        .values(revoked_at=datetime.now(timezone.utc).replace(tzinfo=None))
    )
    await db.execute(stmt)

    # Log session revocation
    await log_security_event(
        db=db,
        event_type="SESSION_REVOKED",
        severity="info",
        user_id=user_id,
        session_id=session_id,
        device_id=session.device_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"scope": scope, "token_family_id": str(session.token_family_id)},
    )

    return True


async def revoke_device_sessions(
    db: AsyncSession,
    request,
    device_id: UUID,
    user_id: UUID,
    current_session_id: Optional[UUID] = None,
) -> List[UUID]:
    """
    Revoke all sessions for a device.
    Returns list of revoked session IDs.
    """
    result = await db.execute(
        select(Session).where(
            and_(
                Session.device_id == device_id,
                Session.user_id == user_id,
                Session.revoked_at.is_(None),
            )
        )
    )
    sessions = result.scalars().all()

    revoked_session_ids = []
    for session in sessions:
        session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.revoke_reason = "revoked_device"

        # Revoke all tokens in the same family
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.token_family_id == session.token_family_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            .values(revoked_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await db.execute(stmt)

        revoked_session_ids.append(session.id)

        # Log session revocation
        await log_security_event(
            db=db,
            event_type="SESSION_REVOKED",
            severity="info",
            user_id=user_id,
            session_id=session.id,
            device_id=device_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"scope": "device", "token_family_id": str(session.token_family_id)},
        )

    return revoked_session_ids


async def revoke_all_user_sessions(
    db: AsyncSession,
    request,
    user_id: UUID,
    current_session_id: Optional[UUID] = None,
) -> List[UUID]:
    """
    Revoke all sessions for a user (global logout).
    Returns list of revoked session IDs.
    """
    result = await db.execute(
        select(Session).where(
            and_(Session.user_id == user_id, Session.revoked_at.is_(None))
        )
    )
    sessions = result.scalars().all()

    revoked_session_ids = []
    for session in sessions:
        session.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.revoke_reason = "revoked_global"

        # Revoke all tokens in the same family
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.token_family_id == session.token_family_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
            .values(revoked_at=datetime.now(timezone.utc).replace(tzinfo=None))
        )
        await db.execute(stmt)

        revoked_session_ids.append(session.id)

        # Log session revocation
        await log_security_event(
            db=db,
            event_type="SESSION_REVOKED",
            severity="info",
            user_id=user_id,
            session_id=session.id,
            device_id=session.device_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"scope": "global", "token_family_id": str(session.token_family_id)},
        )

    return revoked_session_ids


async def get_user_devices_with_sessions(
    db: AsyncSession,
    user_id: UUID,
    current_session_id: Optional[UUID] = None,
) -> List[Device]:
    """
    Get all devices for a user with their active sessions nested.
    """
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Device)
        .where(Device.user_id == user_id)
        .options(selectinload(Device.sessions))
    )
    devices = result.scalars().all()

    # Mark current session
    for device in devices:
        for session in device.sessions:
            session.is_current = (current_session_id is not None and session.id == current_session_id)

    return devices