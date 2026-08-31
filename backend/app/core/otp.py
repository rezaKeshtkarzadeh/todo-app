from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OTPSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    ttl_seconds: int = Field(default=120, alias="OTP_TTL_SECONDS")
    resend_cooldown_seconds: int = Field(default=30, alias="OTP_RESEND_COOLDOWN_SECONDS")
    max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")
    phone_change_token_ttl_seconds: int = Field(default=600, alias="PHONE_CHANGE_TOKEN_TTL_SECONDS")