from typing import Any, Optional
from fastapi import HTTPException


class AppError(Exception):
    def __init__(
        self,
        code: str,
        http_status: int,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ):
        self.code = code
        self.http_status = http_status
        self.message = message
        self.details = details
        super().__init__(message)


ERROR_CODES = {
    "AUTH_INVALID_OTP": (401, "The OTP is invalid or has expired."),
    "AUTH_OTP_EXPIRED": (401, "The OTP has expired."),
    "AUTH_OTP_RATE_LIMITED": (429, "Too many OTP requests. Please wait before trying again."),
    "AUTH_OTP_MAX_ATTEMPTS": (429, "Maximum OTP attempts reached. Request a new code."),
    "AUTH_UNAUTHENTICATED": (401, "Authentication required."),
    "AUTH_SESSION_REVOKED": (401, "Session has been revoked."),
    "AUTH_REFRESH_FAILED": (401, "Token refresh failed."),
    "AUTH_REFRESH_TOKEN_REUSED": (401, "Refresh token reuse detected."),
    "CSRF_TOKEN_MISSING": (403, "CSRF token missing."),
    "CSRF_TOKEN_INVALID": (403, "CSRF token invalid."),
    "DEVICE_ID_MISSING": (400, "Device ID header missing."),
    "DEVICE_ID_INVALID": (400, "Device ID header invalid."),
    "DEVICE_NOT_FOUND": (404, "Device not found."),
    "SESSION_NOT_FOUND": (404, "Session not found."),
    "PROFILE_PHONE_CHANGE_TOKEN_INVALID": (403, "Phone change token invalid or expired."),
    "PROFILE_PHONE_ALREADY_IN_USE": (409, "Phone number already in use."),
    "PROFILE_PHONE_SAME_AS_CURRENT": (400, "New phone number cannot be the same as current."),
    "PROFILE_AVATAR_INVALID_TYPE": (400, "Invalid avatar file type."),
    "PROFILE_AVATAR_TOO_LARGE": (413, "Avatar file too large."),
    "TASK_NOT_FOUND": (404, "Task not found."),
    "TASK_TITLE_INVALID": (400, "Task title invalid."),
    "VALIDATION_ERROR": (422, "The request contains invalid fields."),
    "RATE_LIMITED": (429, "Rate limit exceeded."),
    "NOT_FOUND": (404, "Resource not found."),
    "INTERNAL_ERROR": (500, "Internal server error."),
}


def get_error_details(code: str) -> tuple[int, str]:
    if code in ERROR_CODES:
        return ERROR_CODES[code]
    return 500, "Internal server error."