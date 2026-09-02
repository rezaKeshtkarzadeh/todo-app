from pydantic import BaseModel, field_validator
from app.core.phone import normalize_phone_number, validate_phone_number


class SendOtpRequest(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not validate_phone_number(v):
            raise ValueError("Invalid phone number format")
        return normalize_phone_number(v)


class SendOtpResponse(BaseModel):
    message: str
    otp_debug: str | None = None


class VerifyOtpRequest(BaseModel):
    phone_number: str
    code: str

    @field_validator("phone_number")
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


class VerifyOtpResponse(BaseModel):
    message: str