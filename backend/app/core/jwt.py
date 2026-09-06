from pydantic import Field
from .base_settings import BaseAppSettings

class JWTSettings(BaseAppSettings):
    secret: str = Field(alias="JWT_SECRET")
    algorithm: str = Field(alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(alias="REFRESH_TOKEN_EXPIRE_DAYS")