import uuid
from fastapi import Header, HTTPException
from app.core.errors import AppError


async def get_device_id(x_device_id: str = Header(..., alias="X-Device-Id")) -> uuid.UUID:
    if not x_device_id:
        raise AppError("DEVICE_ID_MISSING", 400, "Device ID header missing.")
    try:
        return uuid.UUID(x_device_id)
    except ValueError:
        raise AppError("DEVICE_ID_INVALID", 400, "Device ID header invalid.")