from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
import os
from pathlib import Path
from PIL import Image
import io

from app.core.errors import AppError
from app.core.config import settings
from app.db.session import get_db_session
from app.schemas.profile import AvatarUploadResponse
from app.models.user import User
from app.models.audit_log import AuditLog
from app.dependencies.auth import get_current_user
from app.dependencies.csrf import validate_csrf
from app.services.logging_service import log_audit_event

router = APIRouter(prefix="/profile", tags=["profile"])


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


@router.post("/avatar", response_model=AvatarUploadResponse)
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