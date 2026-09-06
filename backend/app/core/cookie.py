from pydantic import Field
from .base_settings import BaseAppSettings


class CookieSettings(BaseAppSettings):
    secure: bool = Field(alias="COOKIE_SECURE")
    samesite: str = "lax"
    httponly_access: bool = True
    httponly_refresh: bool = True
    httponly_csrf: bool = False