from pydantic import Field
from .base_settings import BaseAppSettings


class OTPSettings(BaseAppSettings):
    ttl_seconds: int = Field(alias="OTP_TTL_SECONDS")
    resend_cooldown_seconds: int = Field(alias="OTP_RESEND_COOLDOWN_SECONDS")
    max_attempts: int = Field(alias="OTP_MAX_ATTEMPTS")
    phone_change_token_ttl_seconds: int = Field(alias="PHONE_CHANGE_TOKEN_TTL_SECONDS")