from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from app.core.phone import normalize_phone_number, validate_phone_number


class AvatarUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avatar_path: str
    avatar_url: str


class PhoneChangeRequestCurrentRequest(BaseModel):
    """No payload needed - sends OTP to current phone"""


class PhoneChangeVerifyCurrentRequest(BaseModel):
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 4:
            raise ValueError("OTP must be a 4-digit code")
        return v


class PhoneChangeVerifyCurrentResponse(BaseModel):
    message: str
    phone_change_token: str
    otp_debug: Optional[str] = None


class PhoneChangeRequestNewRequest(BaseModel):
    phone_change_token: str
    new_phone_number: str

    @field_validator("new_phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return normalize_phone_number(v)


class PhoneChangeRequestNewResponse(BaseModel):
    message: str
    otp_debug: Optional[str] = None


class PhoneChangeVerifyNewRequest(BaseModel):
    phone_change_token: str
    new_phone_number: str
    code: str

    @field_validator("new_phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return normalize_phone_number(v)

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 4:
            raise ValueError("OTP must be a 4-digit code")
        return v


class PhoneChangeVerifyNewResponse(BaseModel):
    message: str