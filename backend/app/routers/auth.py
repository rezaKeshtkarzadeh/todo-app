from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.redis_client import get_redis_client
from app.db.session import get_db_session
from app.schemas.auth import SendOtpRequest, SendOtpResponse, VerifyOtpRequest, VerifyOtpResponse
from app.services.logging_service import log_security_event
from app.services.otp_service import (
    check_and_set_cooldown,
    generate_otp,
    store_otp,
    verify_otp,
)
from app.core.config import settings

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
    payload: VerifyOtpRequest,
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
    
    await db.commit()
    return VerifyOtpResponse(message="OTP verified successfully.")