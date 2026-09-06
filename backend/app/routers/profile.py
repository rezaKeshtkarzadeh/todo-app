from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import os
from pathlib import Path
from PIL import Image
import io
import secrets

from app.core.errors import AppError
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.core.phone import normalize_phone_number
from app.db.session import get_db_session
from app.schemas.profile import (
    AvatarUploadResponse,
    PhoneChangeRequestCurrentRequest,
    PhoneChangeVerifyCurrentRequest,
    PhoneChangeVerifyCurrentResponse,
    PhoneChangeRequestNewRequest,
    PhoneChangeRequestNewResponse,
    PhoneChangeVerifyNewRequest,
    PhoneChangeVerifyNewResponse,
)
from app.models.user import User
from app.models.audit_log import AuditLog
from app.dependencies.auth import get_current_user
from app.dependencies.csrf import validate_csrf
from app.dependencies.rate_limit import create_rate_limit_dependency
from app.services.logging_service import log_audit_event, log_security_event
from app.services.otp_service import (
    generate_otp,
    check_and_set_phone_current_cooldown,
    store_phone_current_otp,
    verify_phone_current_otp,
    delete_phone_current_otp,
    check_and_set_phone_new_cooldown,
    store_phone_new_otp,
    verify_phone_new_otp,
    delete_phone_new_otp,
    store_phone_change_token,
    get_phone_change_token,
    delete_phone_change_token,
)

router = APIRouter(prefix="/profile", tags=["profile"])

rate_limit_avatar = create_rate_limit_dependency("profile:avatar")
rate_limit_phone_current = create_rate_limit_dependency("profile:phone:current")
rate_limit_phone_new = create_rate_limit_dependency("profile:phone:new")


def validate_image_file(file_content: bytes) -> tuple[str, str]:
    """
    Validate image using Pillow.
    Returns (format, extension) if valid, raises AppError if invalid.
    """
    try:
        img = Image.open(io.BytesIO(file_content))
        img.verify()  # Verify it's a valid image
        
        # Re-open for format detection (verify closes the image)
        img = Image.open(io.BytesIO(file_content))
        fmt = img.format
        
        if fmt not in ("JPEG", "PNG", "WEBP"):
            raise AppError("PROFILE_AVATAR_INVALID_TYPE", status.HTTP_400_BAD_REQUEST, "Invalid avatar file type. Allowed: JPEG, PNG, WebP")
        
        ext_map = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
        return fmt, ext_map[fmt]
    except AppError:
        raise
    except Exception as e:
        raise AppError("PROFILE_AVATAR_INVALID_TYPE", status.HTTP_400_BAD_REQUEST, "Invalid avatar file type. Allowed: JPEG, PNG, WebP")


def generate_avatar_filename(user_id: uuid.UUID, extension: str) -> str:
    """Generate avatar filename: {user_id}/{uuid4}.{ext}"""
    return f"{user_id}/{uuid.uuid4()}.{extension}"


@router.post("/avatar", response_model=AvatarUploadResponse, dependencies=[Depends(rate_limit_avatar)])
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    _csrf: None = Depends(validate_csrf),
    db: AsyncSession = Depends(get_db_session),
):
    user = current_user.user
    
    # Check file size BEFORE reading content (uses Content-Length header)
    if file.size is not None and file.size > settings.avatar.max_bytes:
        raise AppError("PROFILE_AVATAR_TOO_LARGE", status.HTTP_413_CONTENT_TOO_LARGE, "Avatar file too large. Maximum 5 MB.")
    
    # Read file content
    file_content = await file.read()
    
    # Fallback size check (in case size wasn't available in header)
    if len(file_content) > settings.avatar.max_bytes:
        raise AppError("PROFILE_AVATAR_TOO_LARGE", status.HTTP_413_CONTENT_TOO_LARGE, "Avatar file too large. Maximum 5 MB.")
    
    # Validate image type with Pillow
    img_format, extension = validate_image_file(file_content)
    
    # Generate filename
    filename = generate_avatar_filename(user.id, extension)
    relative_path = filename
    full_path = settings.avatar.uploads_path / filename
    
    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Delete previous avatar if exists
    if user.avatar_path:
        old_path = settings.avatar.uploads_path / user.avatar_path
        if old_path.exists():
            try:
                old_path.unlink()
            except Exception:
                pass  # Best effort
    
    # Save new avatar
    with open(full_path, "wb") as f:
        f.write(file_content)
    
    # Update user avatar_path in database
    user.avatar_path = relative_path
    await db.flush()
    
    # Write audit log
    await log_audit_event(
        db=db,
        action="AVATAR_UPDATED",
        resource_type="avatar",
        resource_id=user.id,
        user_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"format": img_format, "size_bytes": len(file_content)},
    )
    
    await db.commit()
    
    # Return response with path and URL
    avatar_url = f"/uploads/{relative_path}"
    return AvatarUploadResponse(avatar_path=relative_path, avatar_url=avatar_url)


# ===== Phone Number Change (2-Step Flow) =====

@router.post("/phone/request-current", response_model=PhoneChangeVerifyCurrentResponse, dependencies=[Depends(rate_limit_phone_current)])
async def request_current_phone_otp(
    request: Request,
    _payload: PhoneChangeRequestCurrentRequest,
    current_user = Depends(get_current_user),
    _csrf: None = Depends(validate_csrf),
    redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Step 1: Send OTP to user's current phone number.
    Requires authentication and CSRF.
    Subject to same cooldown and attempt rules as login OTPs.
    """
    user = current_user.user
    
    # Check and set cooldown
    try:
        await check_and_set_phone_current_cooldown(redis, str(user.id))
    except ValueError as e:
        error_code = str(e).split(":")[0]
        raise AppError(error_code, 429, str(e).split(": ", 1)[1])
    
    # Generate OTP
    otp = await generate_otp()
    
    # Store OTP
    await store_phone_current_otp(redis, str(user.id), otp)
    
    # Log security event
    await log_security_event(
        db=db,
        event_type="PHONE_CHANGE_REQUESTED",
        severity="info",
        user_id=user.id,
        session_id=current_user.session_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"step": "request_current"},
    )
    
    await db.commit()
    
    # For testing only - include OTP in response (development only)
    otp_debug = None
    if not settings.app.is_production:
        otp_debug = otp
        print(f"[DEV] Phone change current OTP for user {user.id}: {otp}")
    
    return PhoneChangeVerifyCurrentResponse(
        message="OTP sent to current phone number.", 
        phone_change_token="",
        otp_debug=otp_debug
    )


@router.post("/phone/verify-current", response_model=PhoneChangeVerifyCurrentResponse, dependencies=[Depends(rate_limit_phone_current)])
async def verify_current_phone_otp(
    request: Request,
    payload: PhoneChangeVerifyCurrentRequest,
    current_user = Depends(get_current_user),
    _csrf: None = Depends(validate_csrf),
    redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Step 2: Verify the OTP sent to current phone.
    On success, issue a short-lived phone_change_token and store in Redis.
    Returns the token in response body (never as cookie).
    """
    user = current_user.user
    
    # Verify OTP
    success, error_code = await verify_phone_current_otp(redis, str(user.id), payload.code)
    
    if not success:
        if error_code == "AUTH_OTP_EXPIRED":
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_current", "reason": "expired"},
            )
            await db.commit()
            raise AppError("AUTH_OTP_EXPIRED", 401, "The OTP has expired.")
        elif error_code == "AUTH_OTP_MAX_ATTEMPTS":
            await log_security_event(
                db=db,
                event_type="OTP_MAX_ATTEMPTS_REACHED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_current"},
            )
            await db.commit()
            raise AppError("AUTH_OTP_MAX_ATTEMPTS", 429, "Maximum OTP attempts reached. Request a new code.")
        else:
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_current", "reason": "invalid"},
            )
            await db.commit()
            raise AppError("AUTH_INVALID_OTP", 401, "The OTP is invalid or has expired.")
    
    # OTP verified successfully - generate phone_change_token
    phone_change_token = secrets.token_urlsafe(32)
    
    # Store token in Redis (without new_phone yet - will be bound in request-new step)
    # We'll store a placeholder for new_phone, it will be updated in request-new
    import json
    await redis.set(
        f"phone_change:{user.id}",
        json.dumps({"token": phone_change_token, "new_phone": None}),
        ex=settings.otp.phone_change_token_ttl_seconds
    )
    
    # Log security event
    await log_security_event(
        db=db,
        event_type="PHONE_CHANGE_CURRENT_VERIFIED",
        severity="info",
        user_id=user.id,
        session_id=current_user.session_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"step": "verify_current"},
    )
    
    await db.commit()
    
    return PhoneChangeVerifyCurrentResponse(
        message="Current phone verified. You can now request OTP for new phone number.",
        phone_change_token=phone_change_token
    )


@router.post("/phone/request-new", response_model=PhoneChangeRequestNewResponse, dependencies=[Depends(rate_limit_phone_new)])
async def request_new_phone_otp(
    request: Request,
    payload: PhoneChangeRequestNewRequest,
    current_user = Depends(get_current_user),
    _csrf: None = Depends(validate_csrf),
    redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Step 3: Request OTP for new phone number.
    Requires valid phone_change_token from step 2.
    Validates new number is not in use and not same as current.
    """
    user = current_user.user
    
    # Validate phone_change_token
    token_data = await get_phone_change_token(redis, str(user.id))
    if not token_data or token_data.get("token") != payload.phone_change_token:
        await log_security_event(
            db=db,
            event_type="PHONE_CHANGE_COMPLETED",  # We'll use this for invalid token too
            severity="warning",
            user_id=user.id,
            session_id=current_user.session_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"phone_change_step": "request_new", "reason": "invalid_token"},
        )
        await db.commit()
        raise AppError("PROFILE_PHONE_CHANGE_TOKEN_INVALID", 403, "Phone change token is invalid or expired.")
    
    # Check if new phone is same as current
    if payload.new_phone_number == user.phone_number:
        raise AppError("PROFILE_PHONE_SAME_AS_CURRENT", 400, "New phone number must be different from current phone number.")
    
    # Check if new phone is already in use by another user
    result = await db.execute(select(User).where(User.phone_number == payload.new_phone_number))
    existing_user = result.scalar_one_or_none()
    if existing_user and existing_user.id != user.id:
        raise AppError("PROFILE_PHONE_ALREADY_IN_USE", 409, "This phone number is already registered.")
    
    # Check and set cooldown for new phone OTP
    try:
        await check_and_set_phone_new_cooldown(redis, str(user.id))
    except ValueError as e:
        error_code = str(e).split(":")[0]
        raise AppError(error_code, 429, str(e).split(": ", 1)[1])
    
    # Generate OTP
    otp = await generate_otp()
    
    # Store OTP for new phone
    await store_phone_new_otp(redis, str(user.id), otp)
    
    # Bind token to new phone number in Redis
    import json
    await redis.set(
        f"phone_change:{user.id}",
        json.dumps({"token": payload.phone_change_token, "new_phone": payload.new_phone_number}),
        ex=settings.otp.phone_change_token_ttl_seconds
    )
    
    # Log security event
    await log_security_event(
        db=db,
        event_type="PHONE_CHANGE_REQUESTED",
        severity="info",
        user_id=user.id,
        session_id=current_user.session_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"step": "request_new", "new_phone": payload.new_phone_number},
    )
    
    await db.commit()
    
    # For testing only
    otp_debug = None
    if not settings.app.is_production:
        otp_debug = otp
        print(f"[DEV] Phone change new OTP for user {user.id}: {otp}")
    
    return PhoneChangeRequestNewResponse(message="OTP sent to new phone number.", otp_debug=otp_debug)


@router.post("/phone/verify-new", response_model=PhoneChangeVerifyNewResponse, dependencies=[Depends(rate_limit_phone_new)])
async def verify_new_phone_otp(
    request: Request,
    payload: PhoneChangeVerifyNewRequest,
    current_user = Depends(get_current_user),
    _csrf: None = Depends(validate_csrf),
    redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Step 4: Verify the OTP sent to new phone number.
    On success, update user's phone number, invalidate token, delete both OTPs.
    Sessions are NOT revoked by phone number change.
    """
    user = current_user.user
    
    # Validate phone_change_token
    token_data = await get_phone_change_token(redis, str(user.id))
    if not token_data or token_data.get("token") != payload.phone_change_token:
        await log_security_event(
            db=db,
            event_type="PHONE_CHANGE_COMPLETED",
            severity="warning",
            user_id=user.id,
            session_id=current_user.session_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"phone_change_step": "verify_new", "reason": "invalid_token"},
        )
        await db.commit()
        raise AppError("PROFILE_PHONE_CHANGE_TOKEN_INVALID", 403, "Phone change token is invalid or expired.")
    
    # Verify token is bound to the same new phone number
    if token_data.get("new_phone") != payload.new_phone_number:
        await log_security_event(
            db=db,
            event_type="PHONE_CHANGE_COMPLETED",
            severity="warning",
            user_id=user.id,
            session_id=current_user.session_id,
            request_id=getattr(request.state, "request_id", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            metadata={"phone_change_step": "verify_new", "reason": "phone_mismatch"},
        )
        await db.commit()
        raise AppError("PROFILE_PHONE_CHANGE_TOKEN_INVALID", 403, "Phone change token is invalid for this phone number.")
    
    # Verify OTP for new phone
    success, error_code = await verify_phone_new_otp(redis, str(user.id), payload.code)
    
    if not success:
        if error_code == "AUTH_OTP_EXPIRED":
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_new", "reason": "expired"},
            )
            await db.commit()
            raise AppError("AUTH_OTP_EXPIRED", 401, "The OTP has expired.")
        elif error_code == "AUTH_OTP_MAX_ATTEMPTS":
            await log_security_event(
                db=db,
                event_type="OTP_MAX_ATTEMPTS_REACHED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_new"},
            )
            await db.commit()
            raise AppError("AUTH_OTP_MAX_ATTEMPTS", 429, "Maximum OTP attempts reached. Request a new code.")
        else:
            await log_security_event(
                db=db,
                event_type="OTP_VERIFICATION_FAILED",
                severity="warning",
                user_id=user.id,
                session_id=current_user.session_id,
                request_id=getattr(request.state, "request_id", None),
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                metadata={"phone_change_step": "verify_new", "reason": "invalid"},
            )
            await db.commit()
            raise AppError("AUTH_INVALID_OTP", 401, "The OTP is invalid or has expired.")
    
    # OTP verified successfully - update user's phone number
    old_phone = user.phone_number
    user.phone_number = payload.new_phone_number
    await db.flush()
    
    # Clean up: delete phone change token and both OTPs
    await delete_phone_change_token(redis, str(user.id))
    await delete_phone_current_otp(redis, str(user.id))
    await delete_phone_new_otp(redis, str(user.id))
    
    # Log security event
    await log_security_event(
        db=db,
        event_type="PHONE_CHANGE_COMPLETED",
        severity="info",
        user_id=user.id,
        session_id=current_user.session_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"step": "verify_new", "old_phone": old_phone, "new_phone": payload.new_phone_number},
    )
    
    # Write audit log
    await log_audit_event(
        db=db,
        action="PHONE_CHANGED",
        resource_type="user",
        resource_id=user.id,
        user_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"old_phone": old_phone, "new_phone": payload.new_phone_number},
    )
    
    await db.commit()
    
    return PhoneChangeVerifyNewResponse(message="Phone number updated successfully.")