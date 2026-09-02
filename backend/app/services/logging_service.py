from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_log import SecurityLog
from app.models.audit_log import AuditLog


async def log_security_event(
    db: Optional[AsyncSession],
    event_type: str,
    severity: str = "info",
    user_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    device_id: Optional[UUID] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[SecurityLog]:
    """
    Record a security event.
    Participates in the caller's transaction - does not commit.
    Never accepts raw tokens, OTPs, or secrets.
    """
    if db is None:
        return None
    
    log = SecurityLog(
        user_id=user_id,
        session_id=session_id,
        device_id=device_id,
        event_type=event_type,
        severity=severity,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
        log_metadata=metadata,
    )
    db.add(log)
    return log


async def log_audit_event(
    db: Optional[AsyncSession],
    action: str,
    resource_type: str,
    user_id: Optional[UUID] = None,
    resource_id: Optional[UUID] = None,
    request_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[AuditLog]:
    """
    Record an audit event.
    Participates in the caller's transaction - does not commit.
    Never accepts raw tokens, OTPs, or secrets.
    """
    if db is None:
        return None
    
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        request_id=request_id,
        change_data=metadata,
    )
    db.add(log)
    return log