from fastapi import APIRouter, Depends, Request, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from datetime import datetime, timezone
from typing import List

from app.core.errors import AppError
from app.db.session import get_db_session
from app.schemas.security import (
    DeviceWithSessions,
    RevokeSessionResponse,
    RevokeDeviceSessionsResponse,
    RevokeAllSessionsResponse,
)
from app.models.session import Session
from app.models.refresh_token import RefreshToken
from app.models.device import Device
from app.dependencies.auth import get_current_user
from app.dependencies.csrf import validate_csrf
from app.services.session_service import (
    revoke_session_by_id,
    revoke_device_sessions,
    revoke_all_user_sessions,
    get_user_devices_with_sessions,
)
from app.core.cookies import clear_all_auth_cookies
from app.services.logging_service import log_security_event


router = APIRouter(prefix="/security", tags=["security"])


@router.get("/devices", response_model=List[DeviceWithSessions])
async def list_devices(
    request: Request,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get devices with their active sessions nested underneath.
    Scoped to the authenticated user.
    """
    user = current_user.user
    current_session_id = current_user.session_id

    devices = await get_user_devices_with_sessions(db, user.id, current_session_id)

    # Build response manually to control nesting
    response = []
    for device in devices:
        sessions_data = []
        for session in device.sessions:
            if session.revoked_at is None:  # Only active sessions
                sessions_data.append({
                    "id": session.id,
                    "created_at": session.created_at,
                    "last_used_at": session.last_used_at,
                    "expires_at": session.expires_at,
                    "is_current": session.is_current,
                })
        response.append({
            "id": device.id,
            "name": device.name,
            "user_agent": device.user_agent,
            "created_at": device.created_at,
            "last_seen_at": device.last_seen_at,
            "sessions": sessions_data,
        })

    return response


@router.delete("/sessions/{session_id}", response_model=RevokeSessionResponse, dependencies=[Depends(validate_csrf)])
async def revoke_session(
    request: Request,
    response: Response,
    session_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Revoke a single session.
    Scoped by (session_id, user_id). Not found/other-user → 404 SESSION_NOT_FOUND.
    Also revokes the associated refresh-token family.
    If the current session is revoked, clear auth cookies.
    """
    user = current_user.user
    current_session_id = current_user.session_id

    revoked = await revoke_session_by_id(
        db=db,
        request=request,
        session_id=session_id,
        user_id=user.id,
        scope="single",
        current_session_id=current_session_id,
    )

    if not revoked:
        raise AppError("SESSION_NOT_FOUND", 404, "Session not found.")

    await db.commit()

    # If the revoked session is the current one, clear cookies
    if session_id == current_session_id:
        clear_all_auth_cookies(response)

    return RevokeSessionResponse(message="Session revoked successfully.")


@router.delete("/devices/{device_id}/sessions", response_model=RevokeDeviceSessionsResponse, dependencies=[Depends(validate_csrf)])
async def revoke_device_sessions_endpoint(
    request: Request,
    response: Response,
    device_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Revoke all sessions for a device.
    Scoped by (device_id, user_id). Not found → 404 DEVICE_NOT_FOUND.
    Revokes every session (and token family) under that device.
    If the current session is among the revoked set, clear auth cookies.
    """
    user = current_user.user
    current_session_id = current_user.session_id

    # Verify device exists and belongs to user
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.user_id == user.id,
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise AppError("DEVICE_NOT_FOUND", 404, "Device not found.")

    revoked_session_ids = await revoke_device_sessions(
        db=db,
        request=request,
        device_id=device_id,
        user_id=user.id,
        current_session_id=current_session_id,
    )

    await db.commit()

    # If the current session was among the revoked ones, clear cookies
    if current_session_id in revoked_session_ids:
        clear_all_auth_cookies(response)

    return RevokeDeviceSessionsResponse(message="All sessions for device revoked successfully.")


@router.delete("/sessions", response_model=RevokeAllSessionsResponse, dependencies=[Depends(validate_csrf)])
async def revoke_all_sessions(
    request: Request,
    response: Response,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Global logout: revoke all sessions across all devices, including the current session.
    Clears auth cookies on the response so the calling client is logged out immediately.
    """
    user = current_user.user
    current_session_id = current_user.session_id

    revoked_session_ids = await revoke_all_user_sessions(
        db=db,
        request=request,
        user_id=user.id,
        current_session_id=current_session_id,
    )

    await db.commit()

    # Always clear cookies on global logout (includes current session)
    clear_all_auth_cookies(response)

    return RevokeAllSessionsResponse(message="All sessions revoked successfully. You have been logged out.")