from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CookieSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    secure: bool = Field(default=False, alias="COOKIE_SECURE")
    samesite: str = "lax"
    httponly_access: bool = True
    httponly_refresh: bool = True
    httponly_csrf: bool = False