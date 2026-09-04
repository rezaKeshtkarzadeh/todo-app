from fastapi import APIRouter, Depends, Request, Response, Cookie
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone, timedelta

from app.core.errors import AppError
from app.core.redis_client import get_redis_client
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    encode_refresh_token,
    generate_csrf_token,
    decode_refresh_token,
)
from app.core.cookies import set_access_token_cookie, set_refresh_token_cookie, set_csrf_token_cookie, clear_all_auth_cookies
from app.db.session import get_db_session
from app.schemas.auth import SendOtpRequest, SendOtpResponse, VerifyOtpRequest, VerifyOtpResponse
from app.services.logging_service import log_security_event
from app.services.otp_service import (
    check_and_set_cooldown,
    generate_otp,
    store_otp,
    verify_otp,
    delete_otp,
)
from app.services.auth_service import rotate_refresh_token, handle_refresh_token_reuse
from app.core.config import settings
from app.models.user import User
from app.models.device import Device
from app.models.session import Session
from app.models.refresh_token import RefreshToken
from app.dependencies.device import get_device_id
from app.dependencies.csrf import validate_csrf

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=SendOtpResponse)
async def send_otp(
    request: Request,
    payload: SendOtpRequest,
    redis: Redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    phone = payload.phone_number
    
    # Check and set cooldown
    try:
        await check_and_set_cooldown(redis, phone)
    except ValueError as e:
        error_code = str(e).split(":")[0]
        raise AppError(error_code, 429, str(e).split(": ", 1)[1])
    
    # Generate OTP
    otp = await generate_otp()
    
    # Store OTP
    await store_otp(redis, phone, otp)
    
    # Log security event
    await log_security_event(
        db=db,
        event_type="OTP_REQUESTED",
        severity="info",
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"phone": phone},
    )
    
    await db.commit()
    
    # For testing only - include OTP in response
    response = SendOtpResponse(message="OTP generated.")
    if not settings.app.is_production:
        response.otp_debug = otp
        print(f"[DEV] OTP for {phone}: {otp}")
    
    return response


@router.post("/verify-otp", response_model=VerifyOtpResponse)
async def verify_otp_endpoint(
    request: Request,
    response: Response,
    payload: VerifyOtpRequest,
    client_device_id: uuid.UUID = Depends(get_device_id),
    redis: Redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    phone = payload.phone_number
    code = payload.code
    
    success, error_code = await verify_otp(redis, phone, code)
    
    if not success:
        if error_code == "AUTH_OTP_EXPIRED":
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone": phone, "reason": "expired"},
            )
            await db.commit()
            raise AppError("AUTH_OTP_EXPIRED", 401, "The OTP has expired.")
        elif error_code == "AUTH_OTP_MAX_ATTEMPTS":
            await log_security_event(
                db=db,
                event_type="OTP_MAX_ATTEMPTS_REACHED",
                severity="warning",
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone": phone},
            )
            await db.commit()
            raise AppError("AUTH_OTP_MAX_ATTEMPTS", 429, "Maximum OTP attempts reached. Request a new code.")
        else:
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone": phone, "reason": "invalid"},
            )
            await db.commit()
            raise AppError("AUTH_INVALID_OTP", 401, "The OTP is invalid or has expired.")
    
    # OTP verified successfully - delete OTP and attempts
    await delete_otp(redis, phone)
    
    # Find or create User
    result = await db.execute(select(User).where(User.phone_number == phone))
    user = result.scalar_one_or_none()
    if not user:
        user = User(phone_number=phone)
        db.add(user)
        await db.flush()  # Get user.id
    
    # Find or create Device scoped by (client_device_id, user_id)
    result = await db.execute(
        select(Device).where(Device.device_id == client_device_id, Device.user_id == user.id)
    )
    device = result.scalar_one_or_none()
    if not device:
        device = Device(
            device_id=client_device_id,
            user_id=user.id,
            name=None,
            user_agent=request.headers.get("user-agent"),
            last_seen_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.add(device)
    else:
        device.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None)
        device.user_agent = request.headers.get("user-agent")
    await db.flush()
    
    # Create Session (use device.id which is auto-generated)
    token_family_id = uuid.uuid4()
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.jwt.refresh_token_expire_days)
    session = Session(
        id=uuid.uuid4(),
        user_id=user.id,
        device_id=device.id,
        token_family_id=token_family_id,
        expires_at=expires_at,
        last_used_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    db.add(session)
    await db.flush()
    
    # Create first RefreshToken
    token_id, secret = generate_refresh_token()
    token_hash = hash_refresh_token(secret)
    refresh_token = RefreshToken(
        id=token_id,
        session_id=session.id,
        token_family_id=token_family_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    
    # Create Access Token
    access_token = create_access_token(str(user.id), str(session.id))
    
    # Create CSRF token
    csrf_token = generate_csrf_token()
    
    # Set cookies
    set_access_token_cookie(response, access_token)
    refresh_token_str = encode_refresh_token(token_id, secret)
    set_refresh_token_cookie(response, refresh_token_str)
    set_csrf_token_cookie(response, csrf_token)
    
    # Log LOGIN_SUCCESS
    await log_security_event(
        db=db,
        event_type="LOGIN_SUCCESS",
        severity="info",
        user_id=user.id,
        session_id=session.id,
        device_id=device.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"phone": phone},
    )
    
    # Commit all in one transaction
    await db.commit()
    
    return VerifyOtpResponse(message="OTP verified successfully.")


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
    _csrf: None = Depends(validate_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    if not refresh_token:
        raise AppError("AUTH_REFRESH_FAILED", 401, "Refresh token not found.")
    
    await rotate_refresh_token(db, request, response, refresh_token)
    await db.commit()
    
    return {"message": "Token refreshed successfully."}